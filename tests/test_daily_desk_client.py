"""Deterministic client lost-ack checks; real browser proof is separate."""
import json,pathlib,shutil,subprocess,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]

class DeskClient(unittest.TestCase):
 def test_user_text_is_not_an_html_sink_and_token_is_not_persisted(self):
  script=(ROOT/'src/muse_presets/desk_assets/app.js').read_text(encoding='utf8')
  self.assertNotIn('innerHTML',script);self.assertNotIn('localStorage',script)
  self.assertIn('sessionStorage.setItem',script)
  self.assertIn('scope_key',script)
 @unittest.skipUnless(shutil.which('node'),'Node unavailable for optional client fixture')
 def test_lost_reply_preserves_exact_operation_and_blocks_unrelated_writes(self):
  js=r'''
const fs=require('node:fs'),vm=require('node:vm');const nodes=new Map(),storage=new Map();
function node(){return {value:'',textContent:'',hidden:false,disabled:false,files:[],children:[],handlers:{},dataset:{},classList:{add(){},remove(){},toggle(){}},addEventListener(k,v){this.handlers[k]=v;},append(...v){this.children.push(...v);},replaceChildren(){this.children=[];},focus(){},setAttribute(){},removeAttribute(){},remove(){},click(){}};}
const document={getElementById(id){if(!nodes.has(id))nodes.set(id,node());return nodes.get(id);},createElement:node,querySelectorAll(){return []},body:node()};
let fail=true;const seen=[],written=new Map();
const ctx={document,console,Error,JSON,Date,Number,Set,Blob:globalThis.Blob,URL:{},setTimeout,crypto:{randomUUID(){return 'unused-id';}},sessionStorage:{getItem(k){return storage.get(k)||null;},setItem(k,v){storage.set(k,v);},removeItem(k){storage.delete(k);}},
 fetch:async(url,options)=>{const data=options.body?JSON.parse(options.body):null;
  if(url==='/api/desk/task'){seen.push(data);written.set(data.operation_id,data);if(fail){fail=false;throw Error('LOST_AFTER_COMMIT');}return {ok:true,status:200,json:async()=>({task_id:data.task_id,title:data.title,status:'pending',due_ms:null,revision:1,created_ms:1000,updated_ms:1000})};}
  throw Error('Unexpected request '+url);
 }};
vm.createContext(ctx);vm.runInContext(fs.readFileSync(process.argv[2],'utf8'),ctx);
(async()=>{
 vm.runInContext("token='fixture-token';deskState={scope_key:'a'.repeat(64),tasks:[],notes:[]};",ctx);
 const data={task_id:'task',title:'stable original',status:'pending',due_ms:null,expected_revision:0,operation_id:'operation'};
 ctx.payload=data;
 try{await vm.runInContext("beginWrite('/api/desk/task',payload)",ctx);throw Error('Expected lost response');}catch(e){if(!e.message.includes('LOST_AFTER_COMMIT'))throw e;}
 if(storage.size!==1)throw Error('No saved uncertain write');
 const preserved=JSON.parse([...storage.values()][0]);if(preserved.payload.operation_id!=='operation'||preserved.payload.title!=='stable original')throw Error('Lost exact payload');
 if([...storage.values()].join('').includes('fixture-token'))throw Error('Token persisted');
 try{await vm.runInContext("beginWrite('/api/desk/task',{...payload,title:'changed'})",ctx);throw Error('Changed pending write accepted');}catch(e){if(!e.message.includes('PENDING_WRITE'))throw e;}
 if(seen.length!==1)throw Error('New intent sent while unknown');
 const result=await vm.runInContext('sendPending()',ctx);
 if(result.revision!==1||seen.length!==2||written.size!==1||JSON.stringify(seen[0])!==JSON.stringify(seen[1]))throw Error('Replay was not identical');
 if(storage.size!==0)throw Error('Confirmed receipt still pending');
 console.log(JSON.stringify({status:'PASS',requests:2,unique_writes:1,changed_payload_refused:true,token_stored:false}));
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
  with tempfile.TemporaryDirectory() as td:
   p=pathlib.Path(td)/'test.cjs';p.write_text(js,encoding='utf8')
   r=subprocess.run([shutil.which('node'),str(p),str(ROOT/'src/muse_presets/desk_assets/app.js')],capture_output=True,timeout=20)
  self.assertEqual(r.returncode,0,r.stderr.decode('utf8','replace'));self.assertEqual(json.loads(r.stdout)['unique_writes'],1)

if __name__=='__main__':unittest.main()
