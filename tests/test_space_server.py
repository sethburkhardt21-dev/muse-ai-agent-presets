"""Real loopback HTTP acceptance, no external provider or internet calls."""
import http.client,json,tempfile,threading,unittest
from pathlib import Path
from muse_presets.personal_companion import CompanionScope
from muse_presets.space_server import make_server

class ServerTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.db=Path(self.tmp.name)/'space.db'
  self.scope=CompanionScope('owner','space','owner',True);self.token='t'*48
  self.server=make_server(self.db,token=self.token,authority=lambda:self.scope)
  self.thread=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':0.02});self.thread.start()
  self.port=self.server.server_address[1];self.origin='http://127.0.0.1:'+str(self.port)
  self.addCleanup(self.cleanup)
 def cleanup(self):
  self.server.shutdown();self.server.server_close();self.thread.join(5);self.tmp.cleanup()
 def call(self,method,path,body=None,headers=None,auth=True):
  h={'Authorization':'Bearer '+self.token} if auth else {}
  if body is not None:h['Content-Type']='application/json'
  h.update(headers or {});payload=json.dumps(body) if isinstance(body,dict) else body
  c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
  try:
   c.request(method,path,payload,h);r=c.getresponse();return r.status,dict(r.getheaders()),r.read()
  finally:c.close()
 def post(self,path,body):return self.call('POST',path,body)
 def test_static_page_no_token_exposed(self):
  status,h,b=self.call('GET','/',auth=False);self.assertEqual(status,200);self.assertNotIn(self.token.encode(),b);self.assertIn(b'Local companion',b)
 def test_assets(self):
  for p,mime in [('/app.js','javascript'),('/app.css','css')]:
   status,h,b=self.call('GET',p,auth=False);self.assertEqual(status,200);self.assertIn(mime,h['Content-Type'])
 def test_auth_required(self):self.assertEqual(self.call('GET','/api/state',auth=False)[0],401)
 def test_wrong_auth(self):self.assertEqual(self.call('GET','/api/state',headers={'Authorization':'Bearer wrong'})[0],401)
 def test_default_disabled(self):
  status,h,b=self.call('GET','/api/state');self.assertEqual(status,200);self.assertFalse(json.loads(b)['adapter']['enabled'])
 def test_foreign_origin_rejected(self):self.assertEqual(self.call('GET','/api/state',headers={'Origin':'https://other.invalid'})[0],403)
 def test_null_origin_rejected(self):self.assertEqual(self.call('GET','/api/state',headers={'Origin':'null'})[0],403)
 def test_same_origin_passes(self):self.assertEqual(self.call('GET','/api/state',headers={'Origin':self.origin})[0],200)
 def test_wrong_host(self):self.assertEqual(self.call('GET','/',headers={'Host':'other.invalid'})[0],403)
 def test_fetch_cross_site(self):self.assertEqual(self.call('GET','/api/state',headers={'Sec-Fetch-Site':'cross-site'})[0],403)
 def test_query_token_not_supported(self):self.assertEqual(self.call('GET','/api/state?token='+self.token,auth=False)[0],404)
 def test_no_callback_endpoint(self):self.assertEqual(self.post('/api/callback',{})[0],404)
 def test_no_claim_endpoint(self):self.assertEqual(self.post('/api/claim',{})[0],404)
 def test_no_path_traversal(self):self.assertEqual(self.call('GET','/../space.db')[0],404)
 def test_json_duplicate_keys(self):self.assertEqual(self.call('POST','/api/config','{"enabled":true,"enabled":false,"expected_revision":0}')[0],400)
 def test_json_nan(self):self.assertEqual(self.call('POST','/api/config','{"enabled":true,"expected_revision":NaN}')[0],400)
 def test_extra_owner_not_trusted(self):self.assertEqual(self.post('/api/config',{'enabled':True,'expected_revision':0,'owner_id':'other'})[0],400)
 def test_browser_cannot_self_grant_owner(self):
  self.scope=CompanionScope('owner','space','visitor',False)
  self.assertEqual(self.post('/api/config',{'enabled':True,'expected_revision':0})[0],403)
 def test_note_roundtrip(self):
  self.assertEqual(self.post('/api/note',{'note_id':'n1','text':'A real local note','expected_revision':0})[0],200)
  doc=json.loads(self.call('GET','/api/state')[2]);self.assertEqual(doc['notes'][0]['text'],'A real local note')
 def test_note_revision_conflict(self):
  data={'note_id':'n1','text':'one','expected_revision':0};self.post('/api/note',data);self.assertEqual(self.post('/api/note',data)[0],409)
 def test_request_cancel(self):
  self.assertEqual(self.post('/api/config',{'enabled':True,'expected_revision':0})[0],200)
  self.assertEqual(self.post('/api/request',{'request_id':'r1','prompt':'local intent'})[0],200)
  self.assertEqual(self.post('/api/cancel',{'request_id':'r1','expected_revision':1})[0],200)
  self.assertEqual(json.loads(self.call('GET','/api/state')[2])['adapter']['requests'][0]['state'],'cancelled')
 def test_disabled_request(self):self.assertEqual(self.post('/api/request',{'request_id':'r1','prompt':'local'})[0],409)
 def test_body_limit(self):self.assertEqual(self.call('POST','/api/note','x'*32769)[0],413)
 def test_content_type(self):self.assertEqual(self.call('POST','/api/config','{}',{'Content-Type':'text/plain'})[0],415)
 def test_no_cors_and_no_cache(self):
  _,h,_=self.call('GET','/api/state');self.assertNotIn('Access-Control-Allow-Origin',h);self.assertEqual(h['Cache-Control'],'no-store');self.assertEqual(h['X-Content-Type-Options'],'nosniff')
 def test_csp_no_external_source(self):
  _,h,_=self.call('GET','/');self.assertIn("default-src 'none'",h['Content-Security-Policy']);self.assertIn("frame-ancestors 'none'",h['Content-Security-Policy'])
 def test_token_bounds(self):
  with self.assertRaises(ValueError):make_server(self.db,token='short',authority=lambda:self.scope)
 def test_client_not_using_html_injection(self):
  _,_,js=self.call('GET','/app.js');self.assertNotIn(b'innerHTML',js);self.assertNotIn(b'localStorage',js)
 def test_ui_page_small_width_rules(self):
  _,_,css=self.call('GET','/app.css');self.assertIn(b'@media',css);self.assertIn(b'focus-visible',css)
if __name__=='__main__':unittest.main()
