"""Deterministic offline creative-production planning, never media rendering.

Input is declarative JSON. References and rights are caller declarations; this
module neither opens assets nor grants permission, invokes models or accesses
networks. A textual storyboard is a production document, not an accepted render.
"""
from __future__ import annotations

import copy
import csv
import hashlib
import heapq
import html
import io
import json
import os
from pathlib import Path
import re
import stat
import sys
import unicodedata

BRIEF_SCHEMA = "muse-presets/creative-brief-v1"
PLAN_SCHEMA = "muse-presets/creative-production-v1"
MANIFEST_SCHEMA = "muse-presets/creative-export-v1"
MAX_INPUT = 262144
MAX_OUTPUT = 2097152
OUTPUT_NAMES = ("BRIEF.json", "PRODUCTION.json", "SHOT_LIST.csv", "STORYBOARD.html", "MANIFEST.json")
_ID = re.compile(r"[a-z][a-z0-9-]{0,47}\Z")
_KEY = re.compile(r"[a-z][a-z0-9_-]{0,31}\Z")
_SHA = re.compile(r"[a-f0-9]{64}\Z")
_ALIASES = {"/var": "/private/var", "/tmp": "/private/tmp", "/etc": "/private/etc"}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def canonical_bytes(value: object) -> bytes:
    """Stable, strict UTF-8 JSON; no floating nonfinite values or custom encoders."""
    try:
        return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError("INVALID_JSON_VALUE") from exc


def _pairs(items):
    result = {}
    for key, value in items:
        _require(key not in result, "DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _constant(value):
    raise ValueError("NONFINITE_JSON_VALUE")


def _parse(raw: bytes, limit: int = MAX_INPUT):
    _require(type(raw) is bytes and len(raw) <= limit, "INPUT_BUDGET")
    try:
        return json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError("INVALID_JSON:" + type(exc).__name__) from exc


def _shape(value, keys, label):
    _require(type(value) is dict and set(value) == set(keys), "INVALID_SHAPE:" + label)


def _text(value, limit=800):
    _require(type(value) is str, "INVALID_TEXT")
    result = unicodedata.normalize("NFC", value.strip())
    _require(0 < len(result) <= limit and all(ord(c) >= 32 or c in "\n\t" for c in result), "INVALID_TEXT")
    _require(not any(0xD800 <= ord(c) <= 0xDFFF for c in result), "INVALID_UNICODE")
    return result


def _identifier(value):
    _require(type(value) is str and _ID.fullmatch(value) is not None, "INVALID_IDENTIFIER")
    return value


def _list(value, low, high, label):
    _require(type(value) is list and low <= len(value) <= high, "LIST_BUDGET:" + label)
    return value


def _references(value, limit=128):
    result = [_identifier(x) for x in _list(value, 0, limit, "references")]
    _require(len(result) == len(set(result)), "DUPLICATE_REFERENCE")
    return sorted(result)


def _state(value):
    _require(type(value) is dict and len(value) <= 16, "CONTINUITY_STATE_SHAPE")
    result = {}
    for key, val in value.items():
        _require(type(key) is str and _KEY.fullmatch(key) is not None, "CONTINUITY_STATE_KEY")
        result[key] = _text(val, 100)
    return result


def _state_map(value):
    _require(type(value) is dict and len(value) <= 32, "CONTINUITY_MAP_SHAPE")
    return {_identifier(key): _state(val) for key, val in value.items()}


def normalize_brief(value: object) -> dict:
    """Validate the closed bounded schema; normalize text without inventing content."""
    _shape(value, ("schema", "project", "assets", "scenes"), "brief")
    _require(len(canonical_bytes(value)) <= MAX_INPUT, "INPUT_BUDGET")
    _require(value["schema"] == BRIEF_SCHEMA, "UNSUPPORTED_BRIEF_SCHEMA")
    project = value["project"]
    _shape(project, ("id", "title", "summary", "audience", "fps", "aspect_ratio", "constraints"), "project")
    _require(type(project["fps"]) is int and project["fps"] in (12, 24, 25, 30, 48, 50, 60), "UNSUPPORTED_FRAME_RATE")
    _require(project["aspect_ratio"] in ("16:9", "9:16", "1:1", "4:3"), "UNSUPPORTED_ASPECT_RATIO")
    normalized_project = {"id": _identifier(project["id"]), "title": _text(project["title"], 160),
        "summary": _text(project["summary"], 2000), "audience": _text(project["audience"], 240),
        "fps": project["fps"], "aspect_ratio": project["aspect_ratio"],
        "constraints": [_text(x, 400) for x in _list(project["constraints"], 0, 24, "constraints")]}
    assets = []; asset_ids = set()
    for asset in _list(value["assets"], 1, 128, "assets"):
        _shape(asset, ("id", "kind", "label", "reference", "rights", "depends_on", "initial_state"), "asset")
        aid = _identifier(asset["id"])
        _require(aid not in asset_ids, "DUPLICATE_ASSET_ID"); asset_ids.add(aid)
        _require(asset["kind"] in ("character", "prop", "background", "audio", "graphic"), "UNSUPPORTED_ASSET_KIND")
        _require(asset["reference"] == "asset:" + aid, "ASSET_REFERENCE_UNSUPPORTED")
        rights = asset["rights"]
        _shape(rights, ("license", "credit", "source", "restricted", "person_copy"), "rights")
        _require(rights["license"] in ("original", "CC0-1.0", "CC-BY-4.0") and rights["restricted"] is False
                 and rights["person_copy"] is False, "RIGHTS_DECLARATION_REFUSED")
        assets.append({"id": aid, "kind": asset["kind"], "label": _text(asset["label"], 160),
            "reference": asset["reference"], "depends_on": _references(asset["depends_on"]),
            "initial_state": _state(asset["initial_state"]),
            "rights": {"license": rights["license"], "credit": _text(rights["credit"], 300),
                       "source": _text(rights["source"], 400), "restricted": False, "person_copy": False}})
    scenes = []; scene_ids = set(); shot_ids = set(); frames = 0
    for scene in _list(value["scenes"], 1, 64, "scenes"):
        _shape(scene, ("id", "title", "location", "shots"), "scene")
        sid = _identifier(scene["id"])
        _require(sid not in scene_ids, "DUPLICATE_SCENE_ID"); scene_ids.add(sid)
        shots = []
        for shot in _list(scene["shots"], 1, 256, "shots"):
            _shape(shot, ("id", "description", "framing", "duration_frames", "assets", "depends_on", "requires", "changes"), "shot")
            shid = _identifier(shot["id"])
            _require(shid not in shot_ids, "DUPLICATE_SHOT_ID"); shot_ids.add(shid)
            _require(len(shot_ids) <= 256, "SHOT_COUNT_BUDGET")
            _require(type(shot["duration_frames"]) is int and 1 <= shot["duration_frames"] <= 1000000, "FRAME_BUDGET")
            frames += shot["duration_frames"]; _require(frames <= 1000000, "TOTAL_FRAME_BUDGET")
            _require(shot["framing"] in ("wide", "medium", "close", "detail"), "UNSUPPORTED_FRAMING")
            shots.append({"id": shid, "description": _text(shot["description"]), "framing": shot["framing"],
                "duration_frames": shot["duration_frames"], "assets": _references(shot["assets"], 32),
                "depends_on": _references(shot["depends_on"], 32), "requires": _state_map(shot["requires"]),
                "changes": _state_map(shot["changes"])})
        scenes.append({"id": sid, "title": _text(scene["title"], 160), "location": _identifier(scene["location"]), "shots": shots})
    return {"schema": BRIEF_SCHEMA, "project": normalized_project, "assets": sorted(assets, key=lambda a: a["id"]), "scenes": scenes}


def parse_brief(raw: bytes) -> dict:
    return normalize_brief(_parse(raw))


def _topological(graph):
    """Bounded deterministic Kahn traversal; no recursive descent through user DAGs."""
    dependents = {key: [] for key in graph}
    degree = {}
    for key, deps in graph.items():
        _require(set(deps) <= set(graph), "MISSING_DEPENDENCY:" + key)
        degree[key] = len(deps)
        for dep in deps: dependents[dep].append(key)
    queue = [key for key, count in degree.items() if not count]; heapq.heapify(queue)
    result = []
    while queue:
        key = heapq.heappop(queue); result.append(key)
        for item in sorted(dependents[key]):
            degree[item] -= 1
            if not degree[item]: heapq.heappush(queue, item)
    _require(len(result) == len(graph), "DEPENDENCY_CYCLE")
    return result


def compile_brief(value: object) -> dict:
    """Create source-bound timeline and production tasks; does not execute those tasks."""
    data = normalize_brief(value)
    assets = {a["id"]: copy.deepcopy(a) for a in data["assets"]}
    order = _topological({aid: a["depends_on"] for aid, a in assets.items()})
    raw_shots = [shot for scene in data["scenes"] for shot in scene["shots"]]
    _topological({s["id"]: s["depends_on"] for s in raw_shots})
    state = {aid: copy.deepcopy(a["initial_state"]) for aid, a in assets.items()}
    for a in assets.values(): a["used_by"] = []
    shots = []; tasks = []; scenes = []; completed_order = set(); frame = 0
    for aid in order:
        tasks.append({"id": "asset:" + aid, "kind": "prepare-asset", "subject": aid,
                      "depends_on": ["asset:" + dep for dep in assets[aid]["depends_on"]], "status": "NOT_STARTED"})
    for scene in data["scenes"]:
        location = scene["location"]
        _require(location in assets, "MISSING_ASSET:" + location)
        _require(assets[location]["kind"] == "background", "LOCATION_KIND_NOT_BACKGROUND")
        scene_start = frame
        for shot in scene["shots"]:
            sid = shot["id"]
            _require(set(shot["depends_on"]) <= completed_order, "SHOT_DEPENDENCY_ORDER:" + sid)
            active = set(shot["assets"]) | {location}
            _require(active <= set(assets), "MISSING_ASSET:" + sid)
            for change_type in ("requires", "changes"):
                for aid, values in shot[change_type].items():
                    _require(aid in active and aid in state, "CONTINUITY_ASSET_NOT_VISIBLE:" + sid)
                    _require(set(values) <= set(state[aid]), "CONTINUITY_UNKNOWN_STATE_KEY:" + sid)
                    if change_type == "requires":
                        for key, expected in values.items():
                            _require(state[aid][key] == expected, "CONTINUITY_MISMATCH:" + sid + ":" + aid + ":" + key)
            for aid, values in shot["changes"].items(): state[aid].update(values)
            for aid in sorted(active): assets[aid]["used_by"].append(sid)
            shots.append(dict(copy.deepcopy(shot), scene_id=scene["id"], location=location,
                              start_frame=frame, end_frame=frame + shot["duration_frames"]))
            frame += shot["duration_frames"]
            tasks.extend([
                {"id": "layout:" + sid, "kind": "layout-shot", "subject": sid,
                 "depends_on": sorted(["asset:" + aid for aid in active] + ["review:" + dep for dep in shot["depends_on"]]), "status": "NOT_STARTED"},
                {"id": "produce:" + sid, "kind": "produce-media-externally", "subject": sid, "depends_on": ["layout:" + sid], "status": "NOT_STARTED"},
                {"id": "review:" + sid, "kind": "human-visual-review", "subject": sid, "depends_on": ["produce:" + sid], "status": "NOT_STARTED"}
            ])
            completed_order.add(sid)
        scenes.append({"id": scene["id"], "title": scene["title"], "location": location,
                       "start_frame": scene_start, "end_frame": frame, "shot_ids": [s["id"] for s in scene["shots"]]})
    _topological({t["id"]: t["depends_on"] for t in tasks})
    plan = {"schema": PLAN_SCHEMA, "brief_sha256": hashlib.sha256(canonical_bytes(data)).hexdigest(),
        "project": data["project"], "total_frames": frame, "frame_interval": "HALF_OPEN_START_INCLUSIVE_END_EXCLUSIVE",
        "asset_order": order, "assets": assets, "scenes": scenes, "shots": shots, "tasks": tasks,
        "final_state": state, "rights_verification": "CALLER_DECLARATIONS_NOT_INDEPENDENTLY_VERIFIED",
        "acceptance": [{"id": key, "status": "NOT_RUN"} for key in ("rights-review", "story-review", "asset-production", "visual-review", "accessibility-review", "consumer-acceptance")],
        "capabilities": {"deterministic_planning": True, "continuity_constraints_checked": True,
            "media_rendered": False, "native_installed": False, "external_effects_authorized": False,
            "original_animation_renderer_bundled": False, "network_accessed": False}}
    _require(len(canonical_bytes(plan)) <= MAX_OUTPUT, "PRODUCTION_OUTPUT_BUDGET")
    return plan


def compare_briefs(before: object, after: object) -> dict:
    a = normalize_brief(before); b = normalize_brief(after)
    pa = compile_brief(a); pb = compile_brief(b)
    def delta(left, right):
        return {"added": sorted(set(right) - set(left)), "removed": sorted(set(left) - set(right)),
                "changed": sorted(k for k in set(left) & set(right) if left[k] != right[k])}
    return {"schema": "muse-presets/creative-revision-v1", "before_sha256": pa["brief_sha256"], "after_sha256": pb["brief_sha256"],
        "before_total_frames": pa["total_frames"], "after_total_frames": pb["total_frames"],
        "project_changed": a["project"] != b["project"],
        "scenes": delta({s["id"]: {k: v for k, v in s.items() if k != "shots"} for s in a["scenes"]},
                        {s["id"]: {k: v for k, v in s.items() if k != "shots"} for s in b["scenes"]}),
        "scene_order_changed": [s["id"] for s in a["scenes"]] != [s["id"] for s in b["scenes"]],
        "shot_order_changed": [x["id"] for s in a["scenes"] for x in s["shots"]] !=
                              [x["id"] for s in b["scenes"] for x in s["shots"]],
        "assets": delta({x["id"]: x for x in a["assets"]}, {x["id"]: x for x in b["assets"]}),
        "shots": delta({x["id"]: dict(x, scene_id=s["id"]) for s in a["scenes"] for x in s["shots"]},
                       {x["id"]: dict(x, scene_id=s["id"]) for s in b["scenes"] for x in s["shots"]}),
        "media_compared": False, "external_effects_authorized": False}


def safe_path(path: Path) -> Path:
    """Reject linked ancestry. Not a hostile concurrent-filesystem sandbox."""
    p = Path(path)
    _require(".." not in p.parts, "PATH_TRAVERSAL_REFUSED")
    p = p.absolute()
    for part in (p, *p.parents):
        junction = getattr(part, "is_junction", None)
        if callable(junction) and junction(): raise ValueError("LINKED_PATH_REFUSED")
        if part.is_symlink():
            target = _ALIASES.get(str(part))
            allowed = (sys.platform == "darwin" and target and part.lstat().st_uid == 0
                       and part.resolve(strict=True) == Path(target))
            _require(bool(allowed), "LINKED_PATH_REFUSED")
    return p


def read_regular(path: Path, limit: int = MAX_INPUT) -> bytes:
    p = safe_path(path)
    before = p.lstat()
    _require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= limit, "NONREGULAR_OR_OVERSIZED_FILE")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(p, flags)
    with os.fdopen(fd, "rb") as stream:
        observed = os.fstat(stream.fileno())
        _require(stat.S_ISREG(observed.st_mode) and observed.st_nlink == 1 and
                 (before.st_dev, before.st_ino) == (observed.st_dev, observed.st_ino), "FILE_CHANGED_DURING_OPEN")
        raw = stream.read(limit + 1)
    _require(len(raw) <= limit, "FILE_READ_BUDGET")
    return raw


def load_brief(path: Path) -> dict:
    return parse_brief(read_regular(path))


def _csv_cell(value):
    text = str(value)
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text


def _storyboard(plan):
    escape = lambda value: html.escape(str(value), quote=True)
    project = plan["project"]
    cards = []
    for shot in plan["shots"]:
        cards.append('<article class="shot" id="shot-' + escape(shot["id"]) + '"><div class="eyebrow">' +
            escape(shot["scene_id"]) + ' / ' + escape(shot["framing"]) + '</div><h2>' + escape(shot["id"]) +
            '</h2><p class="timing">Frames ' + str(shot["start_frame"]) + '–' + str(shot["end_frame"]) +
            ' · ' + str(shot["duration_frames"]) + ' frames</p><p class="description">' + escape(shot["description"]) +
            '</p><p><strong>Assets:</strong> ' + escape(", ".join(sorted(set(shot["assets"]) | {shot["location"]}))) +
            '</p><details><summary>Continuity requirements and planned changes</summary><pre>' +
            escape(json.dumps({"requires": shot["requires"], "changes": shot["changes"]}, indent=2, sort_keys=True)) +
            '</pre></details><p class="pending">Media production and visual review: NOT RUN</p></article>')
    inventory = ''.join('<tr><th scope="row">' + escape(aid) + '</th><td>' + escape(a["kind"]) +
                        '</td><td>' + escape(a["rights"]["license"]) + '</td><td>' + escape(a["rights"]["credit"]) +
                        '</td></tr>' for aid, a in sorted(plan["assets"].items()))
    css = 'body{margin:0;background:#f5f2eb;color:#172a2a;font:16px/1.6 system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:36px 24px}h1{font-size:clamp(28px,5vw,56px);line-height:1.1;margin:12px 0}h2{margin:.3em 0}p,td,th,h1,h2{overflow-wrap:anywhere}.eyebrow{font-size:12px;letter-spacing:.13em;text-transform:uppercase;color:#375b59}.meta{display:flex;gap:24px;flex-wrap:wrap}.notice{border-left:4px solid #87602b;padding:12px 18px;background:#fff7e5}.shots{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin:28px 0}.shot{background:white;border:1px solid #ccd5cf;border-radius:10px;padding:24px}.description{font-size:18px}.timing,.pending{font-size:13px;color:#47615d}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f4f2;padding:12px}summary{cursor:pointer}.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%;min-width:560px;background:white}th,td{text-align:left;border-bottom:1px solid #ccd5cf;padding:12px}.hash{font:12px/1.5 ui-monospace,monospace;overflow-wrap:anywhere}@media(max-width:700px){main{padding:22px 16px}.shots{grid-template-columns:1fr}.shot{padding:18px}.meta{gap:12px}}@media print{body{background:white}.shot{break-inside:avoid}.shots{display:block}.shot{margin-bottom:16px}}'
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">'
        '<title>' + escape(project["title"]) + ' — Production board</title><style>' + css + '</style></head><body><main>'
        '<header><div class="eyebrow">Creative Studio · Offline production plan</div><h1>' + escape(project["title"]) + '</h1><p>' + escape(project["summary"]) +
        '</p><div class="meta"><span>' + str(len(plan["shots"])) + ' shots</span><span>' + str(plan["total_frames"]) + ' frames</span><span>' + str(project["fps"]) +
        ' fps</span><span>' + escape(project["aspect_ratio"]) + '</span></div></header><p class="notice"><strong>Textual storyboard.</strong> No images or animation have been rendered. Rights are caller declarations; human review is outstanding.</p>'
        '<section aria-label="Shot specifications" class="shots">' + ''.join(cards) + '</section><section><h2>Asset inventory</h2><div class="table-wrap" tabindex="0" aria-label="Scrollable asset inventory"><table><caption>Declared sources; not independently authenticated rights</caption><thead><tr><th>Asset</th><th>Kind</th><th>License declaration</th><th>Credit</th></tr></thead><tbody>' +
        inventory + '</tbody></table></div></section><footer><p class="hash">Canonical brief SHA-256: ' + plan["brief_sha256"] + '</p><p>No network, native assistant, model, or external renderer is invoked.</p></footer></main></body></html>\n').encode("utf-8")


def project_documents(value: object) -> tuple[dict[str, bytes], dict]:
    normalized = normalize_brief(value); plan = compile_brief(normalized)
    csv_stream = io.StringIO(newline="")
    writer = csv.writer(csv_stream, lineterminator="\n")
    writer.writerow(("scene", "shot", "start_frame", "end_frame", "duration_frames", "framing", "description", "assets"))
    for shot in plan["shots"]:
        writer.writerow([_csv_cell(x) for x in (shot["scene_id"], shot["id"], shot["start_frame"], shot["end_frame"], shot["duration_frames"], shot["framing"], shot["description"], ", ".join(shot["assets"]))])
    files = {"BRIEF.json": canonical_bytes(normalized), "PRODUCTION.json": canonical_bytes(plan),
             "SHOT_LIST.csv": csv_stream.getvalue().encode("utf-8"), "STORYBOARD.html": _storyboard(plan)}
    _require(all(len(raw) <= MAX_OUTPUT for raw in files.values()), "ARTIFACT_OUTPUT_BUDGET")
    manifest = {"schema": MANIFEST_SCHEMA, "brief_sha256": plan["brief_sha256"],
                "files_sha256": {name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(files.items())},
                "media_rendered": False, "external_effects_authorized": False, "native_installed": False,
                "rights_independently_verified": False}
    files["MANIFEST.json"] = canonical_bytes(manifest)
    return files, plan


def _write_new(path: Path, data: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())


def export_project(value: object, destination: Path) -> dict:
    files, plan = project_documents(value)
    root = safe_path(destination)
    _require(root.parent.is_dir() and not root.exists() and not root.is_symlink(), "DESTINATION_OCCUPIED_OR_UNSAFE")
    root.mkdir()  # Atomic create-only reservation. Partial output is preserved on any failure.
    for name in OUTPUT_NAMES:
        _write_new(root/name, files[name])  # The completion manifest is always last.
    result = verify_project(root, plan["brief_sha256"])
    return dict(result, status="CREATIVE_PROJECT_EXPORTED")


def verify_project(directory: Path, expected_brief_sha256: str) -> dict:
    root = safe_path(directory)
    _require(root.is_dir(), "INCOMPLETE_EXPORT")
    actual = set()
    with os.scandir(root) as entries:
        for i, entry in enumerate(entries, 1):
            _require(i <= len(OUTPUT_NAMES), "UNKNOWN_EXPORT_ENTRY")
            actual.add(entry.name)
    _require(set(OUTPUT_NAMES) <= actual, "INCOMPLETE_EXPORT")
    _require(actual == set(OUTPUT_NAMES), "UNKNOWN_EXPORT_ENTRY")
    _require(type(expected_brief_sha256) is str and _SHA.fullmatch(expected_brief_sha256) is not None, "EXTERNAL_BRIEF_DIGEST_REQUIRED")
    observed = {name: read_regular(root/name, MAX_OUTPUT) for name in OUTPUT_NAMES}
    normalized = parse_brief(observed["BRIEF.json"])
    digest = hashlib.sha256(canonical_bytes(normalized)).hexdigest()
    _require(digest == expected_brief_sha256, "EXTERNAL_BRIEF_DIGEST_MISMATCH")
    _parse(observed["MANIFEST.json"], MAX_OUTPUT)
    expected, plan = project_documents(normalized)
    for name, raw in expected.items():
        _require(observed[name] == raw, "ARTIFACT_CHANGED:" + name)
    return {"status": "CREATIVE_PROJECT_VERIFIED", "brief_sha256": digest,
            "total_frames": plan["total_frames"], "shots": len(plan["shots"]), "files": len(expected),
            "files_sha256": {name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(expected.items())},
            "media_rendered": False, "native_installed": False, "external_effects_authorized": False}
