'use strict';
// This file is a local, network-free directory filter and copy action only.
// It never fetches upstream executables, sends credentials or connects accounts.
const byId=id=>document.getElementById(id);
const cards=[...document.querySelectorAll('.connector-card')];
const search=byId('connector-search');
const category=byId('category-filter');
const specialist=byId('specialist-filter');
const count=byId('results');
const empty=byId('no-results');

function update(){
  const term=search.value.trim().toLocaleLowerCase();
  let visible=0;
  for(const card of cards){
    const matches=(!term||card.dataset.keywords.includes(term))&&
      (!category.value||card.dataset.category===category.value)&&
      (!specialist.value||card.dataset.specialists.split(' ').includes(specialist.value));
    card.hidden=!matches;
    if(matches)visible++;
  }
  empty.hidden=visible!==0;
  count.textContent='Showing '+visible+' of '+cards.length+' custom connectors.';
}
for(const control of [search,category,specialist]){
  control.addEventListener(control===search?'input':'change',update);
}
byId('reset').addEventListener('click',()=>{
  search.value='';category.value='';specialist.value='';
  update();search.focus();
});
for(const button of document.querySelectorAll('.copy-prompt')){
  button.addEventListener('click',async()=>{
    const id=button.dataset.id;
    const field=byId('prompt-'+id);
    if(!field)return;
    const value=field.value;
    try{
      if(navigator.clipboard&&navigator.clipboard.writeText){
        await navigator.clipboard.writeText(value);
      }else{
        field.focus();field.select();
        if(!document.execCommand('copy'))throw new Error('COPY_NOT_AVAILABLE');
      }
      count.textContent='Copied the '+id+' setup message for Muse.';
    }catch{
      field.focus();field.select();
      count.textContent='Copy is restricted here. Select the message shown in the service card.';
    }
  });
}
function applyAnchor(){
  const id=decodeURIComponent(window.location.hash.slice(1));
  if(!id)return;
  const target=byId(id);
  if(target&&target.classList.contains('connector-card')){
    search.value='';category.value='';specialist.value='';update();target.open=true;
  }
}
window.addEventListener('hashchange',applyAnchor);
update();applyAnchor();
