"""CLI for checking and rendering local drafts; no account/network effects."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .catalog import load_registry, load_preset, validate_catalog, render_preset
from .family import propose_handoff
from .lifecycle import inspect_render
from .neutrality import audit_public_tree
from .catalog import ROOT


def main(argv=None) -> int:
    ap=argparse.ArgumentParser(description='Unofficial Muse AI agent presets — offline source tooling')
    sub=ap.add_subparsers(dest='command',required=True)
    sub.add_parser('list',help='List neutral specialist roles')
    sub.add_parser('doctor',help='Validate local catalog, role methods and default-deny policy')
    hostdoc=sub.add_parser('host-doctor',help='Read-only unauthenticated host inventory; no native grant')
    hostdoc.add_argument('--host',choices=['personal-hatch','muse-code'],required=True)
    hostdoc.add_argument('--bin-path',type=Path,default=None)
    hostdoc.add_argument('--proc-root',type=Path,default=None)
    hostdoc.add_argument('--skills-root',type=Path,default=None)
    binding=sub.add_parser('skill-binding-doctor',help='Read-only custom skill and local catalog admission')
    binding.add_argument('--host',choices=['personal-hatch'],required=True)
    binding.add_argument('--custom-root',type=Path,required=True)
    binding.add_argument('--registry',type=Path,required=True)
    binding.add_argument('--skill',action='append',required=True)
    native=sub.add_parser('generic-native-canary',help='Create a generic disposable offline host acceptance package')
    native.add_argument('--preset',required=True)
    native.add_argument('--host',choices=['personal-hatch','muse-code'],required=True)
    native.add_argument('--to',type=Path,required=True)
    native_inspect=sub.add_parser('generic-native-inspect',help='Inspect a disposable generic host handoff, not native auth')
    native_inspect.add_argument('--path',type=Path,required=True)
    fleet=sub.add_parser('generic-native-fleet',help='Stage all 11 generic profiles and both separate host handoffs')
    fleet.add_argument('--to',type=Path,required=True)
    fleet_check=sub.add_parser('generic-native-fleet-inspect',help='Verify a closed-tree generic source fleet')
    fleet_check.add_argument('--path',type=Path,required=True)
    engineer=sub.add_parser('engineer-dropin',help='Create one neutral source-pinned Software Engineer native-format pack')
    engineer.add_argument('--to',type=Path,required=True)
    engineer_inspect=sub.add_parser('engineer-dropin-inspect',help='Inspect local Software Engineer source bundle, not native host use')
    engineer_inspect.add_argument('--path',type=Path,required=True)
    coordinator=sub.add_parser('coordinator-dropin',help='Stage a neutral Coordinator offline review bundle')
    coordinator.add_argument('--to',type=Path,required=True)
    coordinator_check=sub.add_parser('coordinator-dropin-inspect',help='Verify Coordinator source-only packet')
    coordinator_check.add_argument('--path',type=Path,required=True)
    model=sub.add_parser('model-builder-dropin',help='Stage neutral source-only Model Builder evaluation pack')
    model.add_argument('--to',type=Path,required=True)
    model_inspect=sub.add_parser('model-builder-dropin-inspect',help='Verify Model Builder closed-tree source pack')
    model_inspect.add_argument('--path',type=Path,required=True)
    rooms_plan=sub.add_parser('subchat-scopes-plan',help='Read-only plan for three scoped subchats per neutral role')
    rooms_plan.add_argument('--preset',required=True)
    rooms_plan.add_argument('--name',default=None)
    rooms=sub.add_parser('subchat-scopes',help='Create-only scoped subchat drafts, never register a native chat')
    rooms.add_argument('--preset',required=True)
    rooms.add_argument('--name',default=None)
    rooms.add_argument('--to',type=Path,required=True)
    rooms.add_argument('--profile-source-sha256',default=None)
    rooms_inspect=sub.add_parser('subchat-scopes-inspect',help='Compare scoped drafts against trusted source pins')
    rooms_inspect.add_argument('--path',type=Path,required=True)
    rooms_preview=sub.add_parser('subchat-scopes-preview',help='Preview owner changes without applying or overwriting')
    rooms_preview.add_argument('--path',type=Path,required=True)
    rooms_preview.add_argument('--target',type=Path,required=True)
    skill_plan=sub.add_parser('role-skills-plan',help='Read-only three scoped role-skill descriptors')
    skill_plan.add_argument('--preset',required=True)
    skill_plan.add_argument('--name',default=None)
    skills=sub.add_parser('role-skills',help='Create-only disabled skill descriptors, never a host registration')
    skills.add_argument('--preset',required=True)
    skills.add_argument('--name',default=None)
    skills.add_argument('--to',type=Path,required=True)
    skills.add_argument('--profile-source-sha256',default=None)
    skills_inspect=sub.add_parser('role-skills-inspect',help='Inspect skill files against trusted source bytes')
    skills_inspect.add_argument('--path',type=Path,required=True)
    skills_preview=sub.add_parser('role-skills-preview',help='Read-only owner host registry change preview')
    skills_preview.add_argument('--path',type=Path,required=True)
    skills_preview.add_argument('--target',type=Path,required=True)
    dropin_plan=sub.add_parser('dropin-install-plan',help='Read-only plan for an independent source-only agent pack')
    dropin_plan.add_argument('--preset',required=True)
    dropin_plan.add_argument('--name',default=None)
    dropin=sub.add_parser('dropin-stage',help='Create a new standalone role pack, never a native install')
    dropin.add_argument('--preset',required=True)
    dropin.add_argument('--name',default=None)
    dropin.add_argument('--to',type=Path,required=True)
    dropin.add_argument('--profile-source-sha256',default=None)
    dropin_inspect=sub.add_parser('dropin-inspect',help='Strict source-backed inspection for a packaged role')
    dropin_inspect.add_argument('--path',type=Path,required=True)
    dropin_upgrade=sub.add_parser('dropin-upgrade-preview',help='Read-only upgrade differences, no owner writes')
    dropin_upgrade.add_argument('--candidate',type=Path,required=True)
    dropin_upgrade.add_argument('--target',type=Path,required=True)
    dropin_export=sub.add_parser('dropin-export',help='Create a clean source-only ZIP, excluding owner changes')
    dropin_export.add_argument('--path',type=Path,required=True)
    dropin_export.add_argument('--to',type=Path,required=True)
    dropin_uninstall=sub.add_parser('dropin-uninstall-plan',help='Read-only uninstall/export plan, never delete')
    dropin_uninstall.add_argument('--path',type=Path,required=True)
    portable=sub.add_parser('connector-plan',help='Role-scoped connector proposal, providers unconnected')
    portable.add_argument('--preset',required=True)
    portable.add_argument('--capability',required=True)
    portable.add_argument('--request-id',required=True)
    portable.add_argument('--provider',default='offline-fixture')
    fixture=sub.add_parser('connector-fixture',help='Normalize supplied offline JSON fixture, never call host tools')
    fixture.add_argument('--preset',required=True)
    fixture.add_argument('--capability',required=True)
    fixture.add_argument('--request-id',required=True)
    fixture.add_argument('--file',type=Path,required=True)
    research=sub.add_parser('research-trace',help='Validate caller-provided research excerpts and heldout source-family trace offline')
    research.add_argument('--file',type=Path,required=True)
    numeric=sub.add_parser('research-numeric',help='Score caller-supplied heldout binary predictions offline, without scientific proof')
    numeric.add_argument('--file',type=Path,required=True)
    omnium_plan=sub.add_parser('omnium-plan-preview',help='Review caller-supplied Omnium plan for absent worker routes; no dispatch')
    omnium_plan.add_argument('--file',type=Path,required=True)
    omnium_plan.add_argument('--sha256',required=True)
    builder_plan=sub.add_parser('builder-plan',help='Read-only Appwright/Swiftwright source-recipe preview')
    builder_plan.add_argument('--role',choices=['appwright','swiftwright'],required=True)
    builder_plan.add_argument('--repo',type=Path,required=True)
    builder_plan.add_argument('--commit',required=True)
    builder_stage=sub.add_parser('builder-stage',help='Opt-in detached disposable Git worktree; no tests')
    builder_stage.add_argument('--role',choices=['appwright','swiftwright'],required=True)
    builder_stage.add_argument('--repo',type=Path,required=True)
    builder_stage.add_argument('--commit',required=True)
    builder_stage.add_argument('--to',type=Path,required=True)
    builder_stage.add_argument('--evidence',type=Path,required=True)
    builder_stage.add_argument('--allow-disposable-stage',action='store_true')
    builder_inspect=sub.add_parser('builder-inspect',help='Read-only pinned worktree stage inspection')
    builder_inspect.add_argument('--evidence',type=Path,required=True)
    builder_inspect.add_argument('--stage-sha256',required=True)
    builder_run=sub.add_parser('builder-run',help='Explicit opt-in local reviewed source test/typecheck')
    builder_run.add_argument('--evidence',type=Path,required=True)
    builder_run.add_argument('--stage-sha256',required=True)
    builder_run.add_argument('--to',type=Path,required=True)
    builder_run.add_argument('--allow-reviewed-execution',action='store_true')
    sub.add_parser('audit-neutrality',help='Read-only scan of the complete public source distribution')
    profile_plan=sub.add_parser('system-profile-plan',help='Read-only source plan for a complete neutral profile')
    profile_plan.add_argument('--preset',required=True)
    profile_plan.add_argument('--name',default=None)
    profile=sub.add_parser('system-profile',help='Create a new full system-profile draft, never install it')
    profile.add_argument('--preset',required=True)
    profile.add_argument('--name',default=None)
    profile.add_argument('--to',type=Path,required=True)
    profile.add_argument('--source-sha256',default=None)
    profile_check=sub.add_parser('system-profile-inspect',help='Compare draft files with pinned repository source')
    profile_check.add_argument('--path',type=Path,required=True)
    profile_preview=sub.add_parser('system-profile-preview',help='Preview per-file changes without applying them')
    profile_preview.add_argument('--path',type=Path,required=True)
    profile_preview.add_argument('--target',type=Path,required=True)
    renderer=sub.add_parser('render',help='Create one draft profile, never install into Muse')
    renderer.add_argument('--preset',required=True)
    renderer.add_argument('--to',type=Path,required=True)
    renderer.add_argument('--name',default=None)
    inspect=sub.add_parser('inspect',help='Read-only source/owner-change check for a rendered draft')
    inspect.add_argument('--path',type=Path,required=True)
    preview=sub.add_parser('family-preview',help='Validate a proposal without sending it')
    preview.add_argument('--from-role',dest='from_role',required=True)
    preview.add_argument('--to-role',dest='to_role',required=True)
    preview.add_argument('--request-id',required=True)
    preview.add_argument('--capability',default='review')
    args=ap.parse_args(argv)
    if args.command=='list':
        print('\n'.join(f"{s}: {load_preset(s)['title']}" for s in load_registry()['presets']))
        return 0
    if args.command=='audit-neutrality':
        findings = audit_public_tree(ROOT)
        print(json.dumps({'status':'PASS' if not findings else 'FAIL',
                          'scope':'PUBLIC_DISTRIBUTION_HEURISTIC', 'findings':findings,
                          'native_muse_status':'NOT_CHECKED'}, indent=2))
        return 0 if not findings else 2
    if args.command=='doctor':
        errors=validate_catalog()
        print(json.dumps({'status':'PASS' if not errors else 'FAIL','errors':errors,'native_muse_status':'NOT_CHECKED'},indent=2))
        return 0 if not errors else 2
    if args.command in ('builder-plan','builder-stage','builder-inspect','builder-run'):
        from .builder_delivery import (
            preview_builder_delivery,stage_builder_worktree,
            inspect_builder_worktree,run_builder_worktree)
        try:
            if args.command=='builder-plan':
                result=preview_builder_delivery(args.repo,args.commit,args.role)
            elif args.command=='builder-stage':
                result=stage_builder_worktree(args.repo,args.commit,args.role,
                      args.to,args.evidence,
                      allow_disposable_stage=args.allow_disposable_stage)
            elif args.command=='builder-inspect':
                result=inspect_builder_worktree(args.evidence,args.stage_sha256)
            else:
                result=run_builder_worktree(args.evidence,args.stage_sha256,
                      args.to,
                      allow_reviewed_execution=args.allow_reviewed_execution)
            print(json.dumps(result,sort_keys=True,indent=2))
            if result['status'] in ('LOCAL_REVIEWED_TEST_FAIL',
                'LOCAL_REVIEWED_TEST_NOT_STARTED',
                'LOCAL_REVIEWED_TEST_TIMEOUT_HOLD',
                'NOT_RUN_SWIFT_TOOLCHAIN_REQUIRED'):
                return 2
            return 0
        except (OSError,ValueError,TypeError,KeyError) as exc:
            print(json.dumps({'status':'REFUSED','reason':str(exc),
                'native_app_installed':False,'external_effect_authorized':False},
                sort_keys=True))
            return 2
    if args.command=='omnium-plan-preview':
        from .omnium_plan_review import (
            load_omnium_plan_file,review_omnium_plan_only,
            OMNIUM_SCHEMA_SHA256,OMNIUM_REGISTRY_SHA256)
        try:
            report=review_omnium_plan_only(
                load_omnium_plan_file(args.file),args.sha256,
                expected_schema_sha256=OMNIUM_SCHEMA_SHA256,
                expected_registry_sha256=OMNIUM_REGISTRY_SHA256)
            print(json.dumps(report,sort_keys=True,indent=2))
            return 0
        except (OSError,ValueError,TypeError,KeyError) as exc:
            print(json.dumps({'status':'REFUSED','reason':str(exc),
                 'external_effect_authorized':False},sort_keys=True))
            return 2
    if args.command=='research-numeric':
        from .numeric_evaluation import load_numeric_file,evaluate_numeric_case
        try:
            result=evaluate_numeric_case(load_numeric_file(args.file))
            print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))
            return 0
        except (OSError,ValueError,TypeError,KeyError) as exc:
            print(json.dumps({'status':'REFUSED','reason':str(exc)},sort_keys=True))
            return 2
    if args.command=='research-trace':
        from .research_evaluator import load_case_file,evaluate_research_case
        try:
            result=evaluate_research_case(load_case_file(args.file))
            print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))
            return 0
        except (OSError,ValueError,TypeError,KeyError) as exc:
            print(json.dumps({'status':'REFUSED','reason':str(exc)},sort_keys=True))
            return 2
    if args.command=='host-doctor':
        from .native_host_doctor import probe_host
        report=probe_host(args.host,binary_path=args.bin_path,process_root=args.proc_root,skills_root=args.skills_root)
        print(json.dumps(report,indent=2,sort_keys=True))
        return 2  # The local observation cannot authorize a native effect.
    if args.command=='skill-binding-doctor':
        from .native_skill_binding import inspect_skill_bindings, propose_registry_entries
        try:
            report=inspect_skill_bindings(custom_root=args.custom_root,
                                         registry_path=args.registry,skill_names=args.skill)
            report['proposal']=propose_registry_entries(report)
        except (OSError,ValueError) as exc:
            report={'status':'REFUSED','reason':str(exc),'native_installed':False,
                    'external_effect_authorized':False}
        print(json.dumps(report,indent=2,sort_keys=True))
        return 2  # Neither local registration nor an on-disk entrypoint is native authorization.
    try:
        if args.command in ('connector-plan','connector-fixture'):
            from .portable_connectors import plan_connector,run_offline_fixture,load_fixture_file
            plan=plan_connector(args.preset,args.capability,request_id=args.request_id,
                                provider=args.provider if args.command=='connector-plan'
                                else 'offline-fixture')
            result=(plan if args.command=='connector-plan' else
                    run_offline_fixture(plan,load_fixture_file(args.file)))
            print(json.dumps(result,indent=2,sort_keys=True))
            return 0
        if args.command in ('dropin-install-plan','dropin-stage','dropin-inspect',
                            'dropin-upgrade-preview','dropin-export','dropin-uninstall-plan'):
            from .standalone_pack import (
                plan_standalone_pack,stage_standalone_pack,inspect_standalone_pack,
                preview_standalone_upgrade,export_clean_standalone_pack,
                plan_uninstall_standalone)
            if args.command=='dropin-install-plan':
                report=plan_standalone_pack(args.preset,display_name=args.name)
            elif args.command=='dropin-stage':
                report=stage_standalone_pack(args.to,args.preset,display_name=args.name,
                                             expected_profile_source_sha256=args.profile_source_sha256)
            elif args.command=='dropin-inspect':
                report=inspect_standalone_pack(args.path)
            elif args.command=='dropin-upgrade-preview':
                report=preview_standalone_upgrade(args.candidate,args.target)
            elif args.command=='dropin-export':
                report=export_clean_standalone_pack(args.path,args.to)
            else:
                report=plan_uninstall_standalone(args.path)
            print(json.dumps(report,indent=2,sort_keys=True))
            return 2 if report['status'] in ('REVIEW_REQUIRED','SOURCE_DRIFT',
                       'INCOMPLETE_STAGE') else 0
        if args.command in ('role-skills-plan','role-skills','role-skills-inspect','role-skills-preview'):
            from .role_skills import (plan_role_skills,stage_role_skills,
                                      inspect_role_skills,preview_role_skills)
            if args.command=='role-skills-plan':
                report=plan_role_skills(args.preset,display_name=args.name)
            elif args.command=='role-skills':
                report=stage_role_skills(args.to,args.preset,display_name=args.name,
                                        expected_profile_source_sha256=args.profile_source_sha256)
            elif args.command=='role-skills-inspect':
                report=inspect_role_skills(args.path)
            else:
                report=preview_role_skills(args.path,args.target)
            print(json.dumps(report,indent=2,sort_keys=True))
            return 2 if report['status'] in ('REVIEW_REQUIRED','SOURCE_DRIFT','INCOMPLETE_STAGE') else 0
        if args.command in ('subchat-scopes-plan','subchat-scopes','subchat-scopes-inspect','subchat-scopes-preview'):
            from .subchat_scopes import (plan_subchat_scopes,stage_subchat_scopes,
                                         inspect_subchat_scopes,preview_subchat_scopes)
            if args.command=='subchat-scopes-plan':
                report=plan_subchat_scopes(args.preset,display_name=args.name)
            elif args.command=='subchat-scopes':
                report=stage_subchat_scopes(args.to,args.preset,display_name=args.name,
                                            expected_profile_source_sha256=args.profile_source_sha256)
            elif args.command=='subchat-scopes-inspect':
                report=inspect_subchat_scopes(args.path)
            else:
                report=preview_subchat_scopes(args.path,args.target)
            print(json.dumps(report,indent=2,sort_keys=True))
            return 2 if report['status'] in ('REVIEW_REQUIRED','SOURCE_DRIFT','INCOMPLETE_STAGE') else 0
        if args.command in ('system-profile-plan','system-profile','system-profile-inspect','system-profile-preview'):
            from .system_profile import (plan_system_profile,stage_system_profile,
                                         inspect_system_profile,preview_system_profile)
            if args.command=='system-profile-plan':
                report=plan_system_profile(args.preset,display_name=args.name)
            elif args.command=='system-profile':
                report=stage_system_profile(args.to,args.preset,display_name=args.name,
                                            expected_source_sha256=args.source_sha256)
            elif args.command=='system-profile-inspect':
                report=inspect_system_profile(args.path)
            else:
                report=preview_system_profile(args.path,args.target)
            print(json.dumps(report,indent=2,sort_keys=True))
            return 2 if report['status'] in ('REVIEW_REQUIRED','SOURCE_DRIFT','INCOMPLETE_STAGE') else 0
        if args.command=='model-builder-dropin':
            from .model_builder_dropin import stage_model_builder_dropin
            report=stage_model_builder_dropin(args.to)
            print(json.dumps(report,indent=2,sort_keys=True))
            return 0
        if args.command=='model-builder-dropin-inspect':
            from .model_builder_dropin import inspect_model_builder_dropin
            report=inspect_model_builder_dropin(args.path)
            print(json.dumps(report,indent=2,sort_keys=True))
            return 0 if report['status']=='LOCAL_MODEL_BUILDER_MATCH' else 2
        if args.command=='coordinator-dropin':
            from .coordinator_dropin import stage_coordinator_dropin
            report=stage_coordinator_dropin(args.to)
            print(json.dumps(report,indent=2,sort_keys=True))
            return 0
        if args.command=='coordinator-dropin-inspect':
            from .coordinator_dropin import inspect_coordinator_dropin
            report=inspect_coordinator_dropin(args.path)
            print(json.dumps(report,indent=2,sort_keys=True))
            return 0 if report['status']=='LOCAL_COORDINATOR_MATCH' else 2
        if args.command=='engineer-dropin':
            from .engineer_dropin import stage_engineer_dropin
            report=stage_engineer_dropin(args.to)
            print(json.dumps(report,indent=2,sort_keys=True))
            return 0
        if args.command=='engineer-dropin-inspect':
            from .engineer_dropin import inspect_engineer_dropin
            report=inspect_engineer_dropin(args.path)
            print(json.dumps(report,indent=2,sort_keys=True))
            return 0 if report['status']=='LOCAL_DROPIN_MATCH' else 2
        if args.command=='generic-native-fleet-inspect':
            from .native_fleet import inspect_generic_fleet
            report=inspect_generic_fleet(args.path)
            print(json.dumps(report,indent=2,sort_keys=True))
            return 0 if report['status']=='LOCAL_FLEET_MATCH' else 2
        if args.command=='generic-native-fleet':
            from .native_fleet import stage_generic_fleet
            report=stage_generic_fleet(args.to)
            print(json.dumps(report,indent=2,sort_keys=True))
            return 0
        if args.command=='generic-native-inspect':
            from .native_canary import inspect_canary
            report=inspect_canary(args.path)
            print(json.dumps(report,indent=2,sort_keys=True))
            return 0 if report['status']=='SOURCE_ONLY_MATCH' else 2
        if args.command=='generic-native-canary':
            from .native_canary import stage_canary
            report=stage_canary(args.to,args.preset,args.host)
            print(json.dumps(report,indent=2,sort_keys=True))
            return 0
        if args.command=='inspect':
            report=inspect_render(args.path)
            print(json.dumps(report,indent=2,sort_keys=True))
            return 0 if report['status'] in ('LOCAL_MATCH','OWNER_CUSTOMIZED') else 2
        if args.command=='render':
            dest=render_preset(args.preset,args.to,display_name=args.name)
            print(json.dumps({'status':'LOCAL_DRAFT_CREATED','destination':str(dest),'native_installed':False},indent=2))
        else:
            print(json.dumps(propose_handoff(args.from_role,args.to_role,request_id=args.request_id,capability=args.capability),indent=2))
    except (OSError,ValueError,KeyError) as exc:
        print(json.dumps({'status':'REFUSED','reason':str(exc)}))
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
