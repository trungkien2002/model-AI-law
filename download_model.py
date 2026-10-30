"""Download release parts and reconstruct the model, validating SHA256 before use."""
import argparse, hashlib, json, os, re, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--local-parts',type=Path,help='Use already downloaded release files instead of the network')
    args=parser.parse_args()
    m=json.loads((ROOT/'model_manifest.json').read_text('utf-8'))
    folder=ROOT/'model';folder.mkdir(exist_ok=True)
    target=folder/'model-ai-law-Q8_0.gguf'
    if target.exists() and sha(target)==m['sha256']:
        print('Model already verified:',target);return
    paths=[]
    for p in m['parts']:
        # Fixed release origin and strict file allowlist; no arbitrary paths or shell execution.
        if not re.fullmatch(r'model-ai-law-Q8_0\.gguf\.part[0-9]{2}',p['name']):raise ValueError('Invalid part filename')
        path=(args.local_parts/p['name']) if args.local_parts else folder/p['name']
        if not path.exists() or path.stat().st_size!=p['size'] or sha(path)!=p['sha256']:
            if args.local_parts:raise ValueError('Local part missing or corrupt: '+p['name'])
            url='https://github.com/trungkien2002/model-AI-law/releases/download/v1.0.0/'+p['name']
            temp=path.with_name(path.name+'.partial')
            print('Downloading',p['name'],flush=True)
            with urllib.request.urlopen(url,timeout=120) as r,temp.open('wb') as out:
                total=0
                while True:
                    b=r.read(8*1024*1024)
                    if not b:break
                    total+=len(b)
                    if total>p['size']:raise ValueError('Unexpected download size')
                    out.write(b)
            if temp.stat().st_size!=p['size'] or sha(temp)!=p['sha256']:raise ValueError('Download checksum mismatch')
            os.replace(temp,path)
        paths.append(path)
    temp=target.with_suffix('.gguf.partial')
    with temp.open('wb') as out:
        for path in paths:
            with path.open('rb') as f:
                for b in iter(lambda:f.read(8*1024*1024),b''):out.write(b)
    if temp.stat().st_size!=m['size'] or sha(temp)!=m['sha256']:raise ValueError('Reconstructed model checksum mismatch')
    os.replace(temp,target)
    print('Verified model:',target)
    print('Next: ollama create model-ai-law -f Modelfile')
if __name__=='__main__':main()
