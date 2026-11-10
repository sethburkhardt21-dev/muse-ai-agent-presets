"""Check product pages, advertised functionality, privacy and exact source hashes."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from muse_presets.distribution import check_distribution,refresh_manifest

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--refresh-manifest',action='store_true',help='Refresh hashes after local review; does not publish')
 args=p.parse_args()
 try:
  if args.refresh_manifest:refresh_manifest(ROOT)
  result=check_distribution(ROOT)
  print(json.dumps(result,indent=2,sort_keys=True))
  return 0 if result['status']=='PASS' else 2
 except (ValueError,OSError) as e:
  print(json.dumps({'status':'FAIL','reason':str(e)}));return 2
if __name__=='__main__':raise SystemExit(main())
