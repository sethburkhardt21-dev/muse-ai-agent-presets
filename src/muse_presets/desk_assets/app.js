'use strict';
// Only an uncertain write is tab-persistent. The local bearer token never is.
const PENDING_KEY='daily-desk.pending.v1';
const byId=id=>document.getElementById(id);
let token='',deskState=null,pending=null,busy=false,taskEdit=null,noteEdit=null;

function status(message,error=false){byId('status').textContent=message;byId('status').classList.toggle('error',error);}
function loadPending(){
 const raw=sessionStorage.getItem(PENDING_KEY);if(!raw)return null;
 const value=JSON.parse(raw);
 if(!value||Object.keys(value).sort().join(',')!=='payload,route,scope_key'||
    !['/api/desk/task','/api/desk/note'].includes(value.route)||
    typeof value.scope_key!=='string'||!/^[a-f0-9]{64}$/.test(value.scope_key)||
    !value.payload||typeof value.payload.operation_id!=='string')throw Error('PENDING_RECORD_INVALID');
 return value;
}
function pendingView(){
 byId('pending-panel').hidden=!pending||!token;
 if(pending)byId('pending-description').textContent='Operation '+pending.payload.operation_id+' has no confirmed reply. Check its saved receipt or retry only the exact original write.';
 for(const id of ['task-title','task-status','task-due','note-text','save-task','save-note','new-task','new-note'])byId(id).disabled=busy||!!pending;
}
function clearPending(){sessionStorage.removeItem(PENDING_KEY);pending=null;pendingView();}
async function api(route,payload){
 if(!token)throw Error('SESSION_REQUIRED');
 const options={method:payload===undefined?'GET':'POST',headers:{Authorization:'Bearer '+token},cache:'no-store'};
 if(payload!==undefined){options.headers['Content-Type']='application/json';options.body=JSON.stringify(payload);}
 const response=await fetch(route,options);let result;
 try{result=await response.json();}catch{throw Error('REPLY_UNREADABLE_CHECK_ORIGINAL_OPERATION');}
 if(!response.ok){
  const error=Error(result.error||'REQUEST_REFUSED');error.definitive=[400,401,403,404,409,413,415].includes(response.status)&&!error.message.includes('UNCONFIRMED');throw error;
 }
 return result;
}
async function beginWrite(route,payload){
 if(pending)throw Error('PENDING_WRITE_MUST_BE_RECONCILED');
 if(!deskState)throw Error('SESSION_REQUIRED');
 pending={route,payload:JSON.parse(JSON.stringify(payload)),scope_key:deskState.scope_key};
 // If durable pending storage fails, do not send the write.
 try{sessionStorage.setItem(PENDING_KEY,JSON.stringify(pending));}catch{pending=null;throw Error('PENDING_STORAGE_UNAVAILABLE_WRITE_NOT_SENT');}
 pendingView();return sendPending();
}
async function sendPending(){
 if(!pending||!deskState||pending.scope_key!==deskState.scope_key)throw Error('PENDING_SCOPE_MISMATCH');
 try{const result=await api(pending.route,pending.payload);clearPending();return result;}
 catch(error){if(error.definitive)clearPending();pendingView();throw error;}
}
function lock(){token='';deskState=null;byId('token').value='';byId('unlock').hidden=false;byId('workspace').hidden=true;byId('refresh').disabled=true;byId('lock').disabled=true;byId('pending-panel').hidden=true;status('Session locked. Saved work remains in the local database.');}
async function run(action){
 if(busy)return;busy=true;pendingView();
 for(const id of ['refresh','export','restore','check-restore','check-pending','retry-pending'])byId(id).disabled=true;
 try{await action();}catch(error){status(error.message,true);}
 finally{busy=false;pendingView();for(const id of ['refresh','export','restore','check-restore','check-pending','retry-pending'])byId(id).disabled=!token;}
}
function button(label,action){const b=document.createElement('button');b.type='button';b.classList.add('secondary');b.textContent=label;b.addEventListener('click',action);return b;}
function text(tag,value,cls){const el=document.createElement(tag);el.textContent=value;if(cls)el.classList.add(cls);return el;}
function dueInput(ms){
 if(ms===null)return '';const d=new Date(ms);const local=new Date(d.getTime()-d.getTimezoneOffset()*60000);return local.toISOString().slice(0,16);
}
function selectTask(row){
 if(pending){status('Resolve the pending write before editing another record.',true);return;}
 taskEdit=row?{id:row.task_id,revision:row.revision}:null;
 byId('task-title').value=row?row.title:'';byId('task-status').value=row?row.status:'pending';byId('task-due').value=row?dueInput(row.due_ms):'';
 byId('task-editor-title').textContent=row?'Edit task':'Add a task';byId('task-revision').textContent=row?'Revision '+row.revision:'New record';byId('task-conflict').hidden=true;byId('reload-task').hidden=true;byId('task-title').focus();
}
function selectNote(row){
 if(pending){status('Resolve the pending write before editing another record.',true);return;}
 noteEdit=row?{id:row.note_id,revision:row.revision}:null;
 byId('note-text').value=row?row.text:'';byId('note-editor-title').textContent=row?'Edit note':'Add a note';byId('note-revision').textContent=row?'Revision '+row.revision:'New record';byId('note-conflict').hidden=true;byId('reload-note').hidden=true;byId('note-text').focus();
}
function render(){
 if(!deskState)return;
 byId('pending-count').textContent=String(deskState.tasks.filter(t=>t.status==='pending').length);
 byId('done-count').textContent=String(deskState.tasks.filter(t=>t.status==='done').length);
 byId('note-count').textContent=String(deskState.notes.length);
 const tasks=byId('task-list');tasks.replaceChildren();const filter=byId('task-filter').value||'all';
 const visible=deskState.tasks.filter(t=>filter==='all'||t.status===filter);
 for(const row of visible){
  const li=document.createElement('li');li.dataset.recordId=row.task_id;if(row.status==='done')li.classList.add('done');
  li.append(text('p',row.title,'record-title'));
  const meta=(row.status==='done'?'Done':'To do')+' · revision '+row.revision+(row.due_ms===null?'':' · due '+new Date(row.due_ms).toLocaleString());
  li.append(text('p',meta,'record-meta'));const actions=document.createElement('div');actions.classList.add('record-actions');actions.append(button('Edit task',()=>selectTask(row)));li.append(actions);tasks.append(li);
 }
 byId('tasks-empty').hidden=visible.length!==0;
 const notes=byId('note-list');notes.replaceChildren();
 for(const row of deskState.notes){
  const li=document.createElement('li');li.dataset.recordId=row.note_id;
  const lines=row.text.split('\n');li.append(text('p',lines[0].slice(0,100),'record-title'));
  if(row.text.length>100||lines.length>1)li.append(text('p',row.text.slice(0,240),'record-preview'));
  li.append(text('p','Revision '+row.revision,'record-meta'));const actions=document.createElement('div');actions.classList.add('record-actions');actions.append(button('Edit note',()=>selectNote(row)));li.append(actions);notes.append(li);
 }
 byId('notes-empty').hidden=deskState.notes.length!==0;
 byId('saved-state').textContent='Read back from your local store.';pendingView();
}
async function refresh(){
 const result=await api('/api/desk/state');
 if(result.protocol!=='daily-desk/1'||result.native_installed!==false||result.provider_connected!==false)throw Error('UNEXPECTED_DESK_CONTRACT');
 deskState=result;render();
}
async function finishWrite(route,result){
 await refresh();
 if(route==='/api/desk/task')selectTask(deskState.tasks.find(x=>x.task_id===result.task_id)||null);
 else selectNote(deskState.notes.find(x=>x.note_id===result.note_id)||null);
 status('Saved and read back. Revision '+result.revision+'.');
}
async function saveTask(){
 const due=byId('task-due').value;const ms=due?new Date(due).getTime():null;
 if(ms!==null&&!Number.isSafeInteger(ms))throw Error('INVALID_DUE_TIME');
 const data={task_id:taskEdit?taskEdit.id:'task-'+crypto.randomUUID(),title:byId('task-title').value,status:byId('task-status').value,due_ms:ms,expected_revision:taskEdit?taskEdit.revision:0,operation_id:'op-'+crypto.randomUUID()};
 try{const result=await beginWrite('/api/desk/task',data);await finishWrite('/api/desk/task',result);}
 catch(error){
  if(error.message==='STALE_REVISION'){await refresh();byId('task-conflict').textContent='This task changed elsewhere. Your draft is preserved. Load the saved version before applying a new edit.';byId('task-conflict').hidden=false;byId('reload-task').hidden=false;}
  throw error;
 }
}
async function saveNote(){
 const data={note_id:noteEdit?noteEdit.id:'note-'+crypto.randomUUID(),text:byId('note-text').value,expected_revision:noteEdit?noteEdit.revision:0,operation_id:'op-'+crypto.randomUUID()};
 try{const result=await beginWrite('/api/desk/note',data);await finishWrite('/api/desk/note',result);}
 catch(error){
  if(error.message==='STALE_REVISION'){await refresh();byId('note-conflict').textContent='This note changed elsewhere. Your draft is preserved. Load the saved version before applying a new edit.';byId('note-conflict').hidden=false;byId('reload-note').hidden=false;}
  throw error;
 }
}
byId('session-form').addEventListener('submit',event=>{event.preventDefault();run(async()=>{
 token=byId('token').value.trim();await refresh();pending=loadPending();
 if(pending&&pending.scope_key!==deskState.scope_key)throw Error('PENDING_SCOPE_MISMATCH_OPEN_ORIGINAL_DESK');
 byId('token').value='';byId('unlock').hidden=true;byId('workspace').hidden=false;byId('refresh').disabled=false;byId('lock').disabled=false;pendingView();status(pending?'A previous write needs readback before continuing.':'Desk opened. Changes are saved only when you press Save.');
 });});
byId('lock').addEventListener('click',lock);
byId('refresh').addEventListener('click',()=>run(async()=>{await refresh();status('Saved records refreshed. Any open draft is unchanged.');}));
byId('task-filter').addEventListener('change',render);
byId('task-form').addEventListener('submit',e=>{e.preventDefault();run(saveTask);});
byId('note-form').addEventListener('submit',e=>{e.preventDefault();run(saveNote);});
byId('new-task').addEventListener('click',()=>selectTask(null));byId('new-note').addEventListener('click',()=>selectNote(null));
byId('reload-task').addEventListener('click',()=>{if(taskEdit)selectTask(deskState.tasks.find(x=>x.task_id===taskEdit.id)||null);});
byId('reload-note').addEventListener('click',()=>{if(noteEdit)selectNote(deskState.notes.find(x=>x.note_id===noteEdit.id)||null);});
byId('retry-pending').addEventListener('click',()=>run(async()=>{if(!pending)throw Error('NO_PENDING_WRITE');const route=pending.route;const result=await sendPending();await finishWrite(route,result);}));
byId('check-pending').addEventListener('click',()=>run(async()=>{
 if(!pending||pending.scope_key!==deskState.scope_key)throw Error('PENDING_SCOPE_MISMATCH');
 const route=pending.route;const r=await api('/api/desk/receipt',{operation_id:pending.payload.operation_id});
 if(r.receipt){const result=r.receipt.result;clearPending();await finishWrite(route,result);}
 else status('No committed receipt found yet. Only the exact pending write may be retried; do not create a replacement operation.',true);
}));
byId('export').addEventListener('click',()=>run(async()=>{
 if(pending)throw Error('RECONCILE_PENDING_WRITE_BEFORE_EXPORT');
 const archive=await api('/api/desk/export');const blob=new Blob([JSON.stringify(archive,null,2)+'\n'],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='daily-desk-backup.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);status('Backup downloaded. Its digest checks consistency, not authorship.');
}));
byId('backup-form').addEventListener('submit',event=>{event.preventDefault();run(async()=>{
 if(pending)throw Error('RECONCILE_PENDING_WRITE_BEFORE_RESTORE');
 const file=byId('backup-file').files[0];if(!file||file.size>16*1024*1024)throw Error('BACKUP_FILE_REQUIRED_WITHIN_16_MIB');
 const name=byId('restore-name').value;const raw=await file.text();
 const result=await api('/api/desk/restore',{name,archive:raw});
 byId('restore-result').textContent='Restored '+result.tasks+' tasks and '+result.notes+' notes to:\n'+result.database+'\nYour current store is unchanged. Open this new database with the local launcher to verify it.';status('Restoration created a new store and read it back.');
 });});
byId('check-restore').addEventListener('click',()=>run(async()=>{
 const result=await api('/api/desk/restore-status',{name:byId('restore-name').value});
 byId('restore-result').textContent=result.status==='RESTORE_NOT_FOUND'?'No published store at that name. Preserve the original restore request before retrying.':'Verified new store: '+result.tasks+' tasks, '+result.notes+' notes.\n'+result.database+'\nPayload digest: '+result.payload_sha256;status('Restore destination inspected; no restore was replayed.');
}));
