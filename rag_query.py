"""Optional RAG example without a desktop UI or saved user chat logs."""
import argparse,json,sys,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tool'))
def create_service():
    from model_first_runtime import ChatService
    service=ChatService()
    # Load once before the bounded planning/answer deadlines; cold GPU/CPU startup can take longer.
    payload=json.dumps({'model':service.config['generation_model'],'prompt':'','stream':False,'keep_alive':'10m'}).encode()
    request=urllib.request.Request('http://127.0.0.1:11434/api/generate',data=payload,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=300) as response:
        result=json.load(response)
    if result.get('error'):raise RuntimeError(result['error'])
    return service
def main():
    p=argparse.ArgumentParser(description='model AI law + versioned local RAG')
    p.add_argument('question')
    p.add_argument('--json',action='store_true')
    args=p.parse_args()
    result=create_service().answer(args.question,history=[],log=False)
    if args.json:
        print(json.dumps({k:result.get(k) for k in ('answer','source_links','quality_status','missing_information','model_used')},ensure_ascii=False,indent=2))
    else:
        print(result['answer'])
        for s in result.get('source_links',[]):print(s['label']+': '+s['url'])
if __name__=='__main__':main()
