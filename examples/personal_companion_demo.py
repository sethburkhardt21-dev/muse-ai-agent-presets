"""A fictional household day plan using a real temporary SQLite database."""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from muse_presets.personal_companion import CompanionScope,PersonalCompanion

def need(condition: bool,reason: str) -> None:
    if not condition:raise ValueError(reason)

def main() -> int:
    now=12*60*60*1000
    scope=CompanionScope('fictional-owner','fictional-home','fictional-owner',True)
    current=[scope]
    with TemporaryDirectory(prefix='personal-companion-demo-') as temp:
        path=Path(temp).resolve()/'companion.sqlite3'
        with PersonalCompanion(path,authority=lambda:current[0],clock_ms=lambda:now) as store:
            need(store.notes()==[],'EXPECTED_EMPTY_NOTEBOOK')
            store.put_note('daily-priority','Read one chapter and take a quiet break.')
            store.add_reminder(reminder_id='reading',title='Read a chapter',due_ms=now)
            need(store.due_reminders()['status']=='REMINDERS_DISABLED','OPT_IN_NOT_REQUIRED')
            store.configure(expected_revision=0,changes={'tone':'gentle','large_text':True,'reminders_enabled':True})
            plan=store.day_plan()
            need(len(plan['due']['items'])==1,'DUE_RECORD_MISSING')
            store.configure(expected_revision=1,changes={'paused':True})
            need(store.due_reminders()['status']=='PAUSED','PAUSE_DID_NOT_STOP_PRESENTATION')
            store.configure(expected_revision=2,changes={'paused':False})
            receipt=store.acknowledge('reading',expected_revision=1,operation_id='read-ack')
            need(receipt['notification_sent'] is False,'FALSE_NOTIFICATION_CLAIM')
        with PersonalCompanion(path,authority=lambda:current[0],clock_ms=lambda:now) as recovered:
            need(recovered.receipt('read-ack')==receipt,'RESTART_RECEIPT_MISMATCH')
            need(recovered.acknowledge('reading',expected_revision=1,operation_id='read-ack')==receipt,
                 'DUPLICATE_ACK_NOT_RECONCILED')
            need(recovered.preferences()['large_text'] is True,'PREFERENCES_DID_NOT_SURVIVE')
            need(len(recovered.notes())==1,'NOTEBOOK_DID_NOT_SURVIVE')
            current[0]=CompanionScope('other-owner','fictional-home','other-owner',True)
            need(recovered.notes()==[] and recovered.receipt('read-ack') is None,'OTHER_OWNER_DATA_LEAK')
            need(recovered.preferences()['reminders_enabled'] is False,'OTHER_OWNER_PREFERENCES_LEAK')
    print(json.dumps({'status':'LOCAL_COMPANION_DEMO_PASSED','uses_real_sqlite':True,
          'owner_isolation_verified':True,'restart_recovery':True,'lost_ack_recovered':True,
          'opt_in_required':True,'pause_verified':True,'example_plan':plan,
          'local_acknowledgement':receipt,'host_authenticated':False,
          'provider_authenticated':False,'notification_sent':False,
          'native_installed':False,'scheduler_started':False},sort_keys=True))
    return 0

if __name__=='__main__':raise SystemExit(main())
