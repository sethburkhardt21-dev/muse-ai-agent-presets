"""Real source-only review/checkpoint/reopen across separate Python processes.

This uses synthetic inputs and a temporary file, never a native planner,
scheduler, local model, connected account, original task DB or actual worker.
Run: PYTHONPATH=src python -B examples/continuum_checkpoint_demo.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from muse_presets.coordinator_review import review_workgraph
from muse_presets.continuum_checkpoint import (
    capture_offline_checkpoint, checkpoint_sha256,
)


def fixture():
    graph={
      "schema":"r33/coordinator-workgraph-v1",
      "workspace":"fixture-offline",
      "budget_units":4,
      "tasks":[
        {"id":"diagnose-1","role":"software-engineer",
         "reviewer":"adversarial-verifier","requires":[],
         "estimated_units":2,"effect_class":"none",
         "source_sha256":"a"*64,
         "acceptance":["Synthetic defect verified by reviewer"]},
        {"id":"analyze-2","role":"claims-adjudicator",
         "reviewer":"research-evaluator","requires":["diagnose-1"],
         "estimated_units":2,"effect_class":"external",
         "source_sha256":"b"*64,
         "acceptance":["Hold external recipient until independently verified"]}
      ]}
    report={
      "schema":"r33/coordinator-assertions-v1",
      "workgraph_sha256":review_workgraph(graph)["workgraph_sha256"],
      "items":[
        {"task_id":"diagnose-1","actor_role":"software-engineer",
         "reviewer_role":"adversarial-verifier","source_sha256":"a"*64,
         "actor_claim":"completed","reviewer_claim":"pass"},
        {"task_id":"analyze-2","actor_role":"claims-adjudicator",
         "reviewer_role":"research-evaluator","source_sha256":"b"*64,
         "actor_claim":"unknown_effect","reviewer_claim":"hold"}
      ]}
    return graph,report


REOPEN_SOURCE = """
import json,sys
from pathlib import Path
from muse_presets.continuum_checkpoint import resume_offline_checkpoint
directory=Path(sys.argv[1])
expected=sys.argv[2]
with (directory/'graph.json').open(encoding='utf-8') as f: graph=json.load(f)
with (directory/'assertions.json').open(encoding='utf-8') as f: assertions=json.load(f)
with (directory/'checkpoint.json').open(encoding='utf-8') as f: checkpoint=json.load(f)
result=resume_offline_checkpoint(checkpoint,graph,assertions,expected)
print(json.dumps({**result,'separate_process_verified':True},sort_keys=True))
"""


def main() -> int:
    graph,reported=fixture()
    checkpoint=capture_offline_checkpoint(graph,reported)
    expected=checkpoint_sha256(checkpoint)
    with tempfile.TemporaryDirectory(prefix="continuum-offline-restart-") as temp:
        root=Path(temp)
        for name,value in (
            ("graph.json",graph),
            ("assertions.json",reported),
            ("checkpoint.json",checkpoint)
        ):
            payload=(json.dumps(value,sort_keys=True,separators=(",",":"),
                                ensure_ascii=True,allow_nan=False)+"\n").encode()
            with (root/name).open("xb") as file:
                file.write(payload)
        environment=dict(os.environ,PYTHONDONTWRITEBYTECODE="1")
        # The child is an actual new interpreter and independently reloads
        # all three persisted JSON files, but uses caller-supplied expected SHA.
        finished=subprocess.run([sys.executable,"-B","-c",REOPEN_SOURCE,
                                 str(root),expected],
            capture_output=True,env=environment,timeout=25)
        if finished.returncode:
            sys.stderr.write(finished.stderr.decode("utf-8",errors="replace"))
            return 2
        data=json.loads(finished.stdout.decode("utf-8"))
        if (data.get("status")!="LOCAL_REVIEW_ONLY_RESUME" or
            data.get("held_task_ids")!=["analyze-2"] or
            data.get("effect_authorized") is not False):
            return 2
        sys.stdout.write(json.dumps(data,sort_keys=True)+"\n")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
