"""Deterministic client regression for an acknowledgement lost after DB commit.

This runs the shipped client in Node with a minimal DOM/network fixture. It is
supplemented by separate real-browser qualification; it is not browser proof.
"""
import json,shutil,subprocess,tempfile,unittest
from pathlib import Path

class ClientTests(unittest.TestCase):
 @unittest.skipUnless(shutil.which('node'),'Node is optional for the client VM regression')
 def test_lost_reply_reuses_exact_request_and_prompt(self):
  asset=Path(__file__).resolve().parents[1]/'src/muse_presets/space_assets/app.js'
  script=r'''
const vm=require('node:vm'), fs=require('node:fs');
const nodes=new Map();
function node(){return {value:'',textContent:'',hidden:false,disabled:false,handlers:{},addEventListener(k,v){this.handlers[k]=v;},append(){},replaceChildren(){},focus(){}};}
const document={getElementById(id){if(!nodes.has(id))nodes.set(id,node());return nodes.get(id);},createElement:node,body:{setAttribute(){},removeAttribute(){}}};
let n=0,failed=false;const requests=[],stored=new Map();
const context={document,crypto:{randomUUID(){return 'id'+(++n);}},console,Error,JSON,
 fetch:async(url,options)=>{
  if(url==='/api/request'){
   const body=JSON.parse(options.body);requests.push(body);stored.set(body.request_id,body);
   if(!failed){failed=true;throw Error('LOST_REPLY_AFTER_COMMIT');}
   return {ok:true,json:async()=>body};
  }
  return {ok:true,json:async()=>({adapter:{enabled:true,revision:1,requests:[]},notes:[]})};
 }};
vm.createContext(context);vm.runInContext(fs.readFileSync(process.argv[2],'utf8'),context);
const prompt=document.getElementById('prompt'),form=document.getElementById('request-form');
const tick=()=>new Promise(r=>setImmediate(r));
(async()=>{
 prompt.value='stable payload';form.handlers.submit({preventDefault(){}});await tick();
 if(!document.getElementById('status').textContent.includes('LOST_REPLY'))throw Error('FAILED_TO_SIMULATE_UNKNOWN');
 prompt.value='changed payload';form.handlers.submit({preventDefault(){}});await tick();
 if(requests.length!==1)throw Error('CONFLICTING_PAYLOAD_SENT');
 prompt.value='stable payload';form.handlers.submit({preventDefault(){}});await tick();
 if(requests.length!==2 || stored.size!==1 || requests[0].request_id!==requests[1].request_id)throw Error('DUPLICATE_INTENT');
 if(requests[0].prompt!==requests[1].prompt)throw Error('PAYLOAD_CHANGED');
 console.log(JSON.stringify({status:'PASS',sent:2,stored:1,conflict_refused:true}));
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
  with tempfile.TemporaryDirectory() as directory:
   runner=Path(directory)/'client-test.cjs';runner.write_text(script,encoding='utf-8')
   p=subprocess.run([shutil.which('node'),str(runner),str(asset)],stdin=subprocess.DEVNULL,capture_output=True,timeout=20)
  self.assertEqual(p.returncode,0,p.stderr.decode(errors='replace'))
  result=json.loads(p.stdout);self.assertEqual(result['stored'],1);self.assertTrue(result['conflict_refused'])
if __name__=='__main__':unittest.main()
