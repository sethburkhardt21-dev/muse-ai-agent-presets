'use strict';
// Source-only local client. Session material never enters URLs or persistent storage.
const el=id=>document.getElementById(id);
let token='', current=null, noteRevision=0, busy=false, pendingRequest=null;
const message=text=>{el('status').textContent=text;};
const uid=prefix=>prefix+crypto.randomUUID().replaceAll('-','');
async function api(path,data){
 const headers={'Authorization':'Bearer '+token};
 const init={method:data===undefined?'GET':'POST',headers,cache:'no-store',credentials:'omit',redirect:'error'};
 if(data!==undefined){headers['Content-Type']='application/json';init.body=JSON.stringify(data);}
 const response=await fetch(path,init);const body=await response.json();
 if(!response.ok)throw new Error(body.error||'REQUEST_UNCONFIRMED');return body;
}
function resetNote(){noteRevision=0;el('note-id').value=uid('n');el('note-id').readOnly=false;el('note-text').value='';}
function element(tag,text){const node=document.createElement(tag);node.textContent=text;return node;}
function render(){
 const adapter=current.adapter;el('policy').textContent=adapter.enabled?'Local requests enabled — provider disconnected':'Disabled by default';
 el('toggle').textContent=adapter.enabled?'Disable local requests':'Enable local requests';el('queue').disabled=!adapter.enabled;
 el('notes').replaceChildren();
 for(const note of current.notes){
  const row=element('li','');row.append(element('strong',note.note_id),element('p',note.text));
  const edit=element('button','Edit note');edit.className='secondary';edit.type='button';
  edit.addEventListener('click',()=>{noteRevision=note.revision;el('note-id').value=note.note_id;el('note-id').readOnly=true;el('note-text').value=note.text;el('note-text').focus();});
  row.append(edit);el('notes').append(row);
 }
 el('requests').replaceChildren();
 for(const request of adapter.requests){
  const row=element('li','');row.append(element('strong',request.request_id+' · '+request.state),element('p',request.prompt));
  if(request.result)row.append(element('p',request.result));
  if(['queued','dispatching','unknown'].includes(request.state)){
   const cancel=element('button','Cancel local request');cancel.className='secondary';cancel.type='button';
   cancel.addEventListener('click',()=>perform(async()=>{await api('/api/cancel',{request_id:request.request_id,expected_revision:request.revision});await refresh();message('Local request cancelled. External work, if any, needs separate host reconciliation.');}));row.append(cancel);
  }
  el('requests').append(row);
 }
}
async function refresh(){current=await api('/api/state');render();}
async function perform(fn){
 if(busy)return;busy=true;document.body.setAttribute('aria-busy','true');
 try{await fn();}catch(error){message('Not confirmed: '+error.message+'. Refresh original state before repeating a mutation.');}
 finally{busy=false;document.body.removeAttribute('aria-busy');}
}
el('session-form').addEventListener('submit',event=>{event.preventDefault();perform(async()=>{
 token=el('token').value;await refresh();el('token').value='';el('unlock').hidden=true;el('workspace').hidden=false;resetNote();message('Local workspace opened. Native provider remains disconnected.');el('note-id').focus();
});});
el('lock').addEventListener('click',()=>{if(busy)return;token='';current=null;noteRevision=0;pendingRequest=null;el('notes').replaceChildren();el('requests').replaceChildren();el('note-text').value='';el('prompt').value='';el('workspace').hidden=true;el('unlock').hidden=false;el('token').value='';message('Session cleared from this page. Local database was not erased.');el('token').focus();});
el('refresh').addEventListener('click',()=>perform(async()=>{await refresh();message('Original local state read back.');}));
el('toggle').addEventListener('click',()=>perform(async()=>{await api('/api/config',{enabled:!current.adapter.enabled,expected_revision:current.adapter.revision});await refresh();message('Local policy saved. No jobs dispatched.');}));
el('note-form').addEventListener('submit',event=>{event.preventDefault();perform(async()=>{await api('/api/note',{note_id:el('note-id').value,text:el('note-text').value,expected_revision:noteRevision});await refresh();resetNote();message('Note persisted and read back from SQLite.');});});
el('new-note').addEventListener('click',()=>{if(!busy){resetNote();el('note-text').focus();}});
el('request-form').addEventListener('submit',event=>{event.preventDefault();perform(async()=>{
 const prompt=el('prompt').value;
 if(pendingRequest&&pendingRequest.prompt!==prompt)throw new Error('PENDING_REQUEST_REQUIRES_ORIGINAL_STATE_RECONCILIATION');
 if(!pendingRequest)pendingRequest={request_id:uid('r'),prompt};
 // Keep the exact ID/payload until acknowledgement, including a lost response.
 await api('/api/request',pendingRequest);pendingRequest=null;el('prompt').value='';
 await refresh();message('Local request recorded. Nothing sent to a provider.');
});});
