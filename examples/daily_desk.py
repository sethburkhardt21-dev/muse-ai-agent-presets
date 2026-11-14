"""Daily Desk: optional local UI; no server or permanent database by default."""
from pathlib import Path
import argparse,json,os,secrets,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from muse_presets.personal_companion import CompanionScope
from muse_presets.daily_desk import DailyDesk,restore_desk,read_archive,MAX_ARCHIVE_BYTES
from muse_presets.space_server import make_server
from muse_presets.database_paths import validated_database_path

LOCAL_SCOPE=CompanionScope('local-owner','local-space','local-owner',True)

def demo():
    authority=lambda:LOCAL_SCOPE
    with tempfile.TemporaryDirectory(prefix='daily-desk-demo-') as td:
        root=Path(td).resolve();database=root/'desk.sqlite';restored=root/'restored.sqlite'
        clock=[1000]
        with DailyDesk(database,authority=authority,clock_ms=lambda:clock[0]) as desk:
            for n,title in enumerate(['Choose the next priority','Review the outline','Plan tomorrow']):
                desk.put_task(task_id='task-'+str(n),title=title,status='pending',due_ms=None,expected_revision=0,operation_id='create-task-'+str(n))
            for n,text in enumerate(['A small useful step beats an oversized plan.','Questions to revisit after the first draft.']):
                desk.put_note('note-'+str(n),text,expected_revision=0,operation_id='create-note-'+str(n))
            clock[0]=2000
            task=desk.put_task(task_id='task-1',title='Outline reviewed',status='done',due_ms=None,expected_revision=1,operation_id='edit-task')
            desk.put_note('note-0','Keep the next step small and verifiable.',expected_revision=1,operation_id='edit-note')
            replay=desk.put_task(task_id='task-1',title='Outline reviewed',status='done',due_ms=None,expected_revision=1,operation_id='edit-task')
            assert replay==task and replay['revision']==2
            stale={}
            for label,call in [('task',lambda:desk.put_task(task_id='task-1',title='Old tab',status='pending',due_ms=None,expected_revision=1,operation_id='stale-task')),
                               ('note',lambda:desk.put_note('note-0','Old text',expected_revision=1,operation_id='stale-note'))]:
                try:call()
                except ValueError as exc:assert str(exc)=='STALE_REVISION';stale[label]=True
                else:raise AssertionError('STALE_WRITE_ACCEPTED')
            before=desk.snapshot();archive=desk.export_archive()
        with DailyDesk(database,authority=authority) as reopened:assert reopened.snapshot()==before
        receipt=restore_desk(restored,archive,authority=authority)
        with DailyDesk(restored,authority=authority) as copy:
            after=copy.snapshot();assert after['scope_key']!=before['scope_key']
            assert {k:v for k,v in after.items() if k!='scope_key'}=={k:v for k,v in before.items() if k!='scope_key'}
            assert copy.export_archive()==archive
        with DailyDesk(database,authority=authority) as original:assert original.export_archive()==archive
        assert len(read_archive(archive)['operations'])==7
        return {'status':'DAILY_DESK_VERTICAL_SLICE_PASS','tasks':3,'notes':2,
                'reopened':True,'stale_task_refused':stale['task'],'stale_note_refused':stale['note'],
                'restored':receipt['status']=='RESTORED_LOCAL_DESK','exact_operation_replayed_once':True,
                'source_store_unchanged_by_restore':True,'server_started':False,'native_installed':False,
                'provider_connected':False,'notifications_sent':0,'scope':'DISPOSABLE_LOCAL_SQLITE_ONLY'}

def _restore_directory(path:Path)->Path:
    # Explicit launcher-selected output only. Never create arbitrary ancestors.
    if not path.exists():
        validated_database_path(path,error='RESTORE_PATH_UNSAFE',absolute=True)
        path.mkdir()
    if not path.is_dir():raise ValueError('RESTORE_DIRECTORY_REQUIRED')
    validated_database_path(path/'.validation-only',error='RESTORE_PATH_UNSAFE',absolute=True)
    return path

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group();mode.add_argument('--serve',action='store_true');mode.add_argument('--restore',type=Path,metavar='ARCHIVE')
    parser.add_argument('--database',type=Path);parser.add_argument('--restore-directory',type=Path);parser.add_argument('--port',type=int,default=0)
    args=parser.parse_args(argv)
    if not args.serve and args.restore is None:
        if args.database is not None or args.restore_directory is not None:parser.error('Default demo uses only disposable storage; choose --serve or --restore.')
        print(json.dumps(demo(),indent=2,sort_keys=True));return 0
    if args.database is None:parser.error('--serve and --restore require an absolute --database path')
    path=validated_database_path(args.database,error='DATABASE_PATH_UNSAFE',absolute=True)
    authority=lambda:LOCAL_SCOPE
    if args.restore is not None:
        archive_path=validated_database_path(args.restore,error='ARCHIVE_PATH_UNSAFE',absolute=True)
        if not archive_path.is_file() or archive_path.stat().st_nlink!=1 or archive_path.stat().st_size>MAX_ARCHIVE_BYTES:raise ValueError('ARCHIVE_PATH_UNSAFE')
        print(json.dumps(restore_desk(path,archive_path.read_bytes(),authority=authority),indent=2));return 0
    directory=_restore_directory(args.restore_directory or path.parent/(path.stem+'-restores'))
    token=secrets.token_urlsafe(36)
    server=make_server(path,token=token,authority=authority,port=args.port,daily_desk=True,restore_directory=directory)
    # This token is intentionally printed only to the local launching terminal.
    print(json.dumps({'status':'DAILY_DESK_LOCAL_SERVER','url':'http://127.0.0.1:'+str(server.server_address[1]),
                      'session_token':token,'database':str(path),'restore_directory':str(directory),
                      'native_installed':False,'provider_connected':False,'public_service':False}),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,TypeError) as exc:
        print(json.dumps({'status':'REFUSED','reason':str(exc),'native_installed':False}),flush=True)
        raise SystemExit(2)
