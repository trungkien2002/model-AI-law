"""Optional RAG example without a desktop UI or saved user chat logs."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tool'))
def main():
    p=argparse.ArgumentParser(description='model AI law + versioned local RAG')
    p.add_argument('question')
    p.add_argument('--json',action='store_true')
    args=p.parse_args()
    from model_first_runtime import ChatService
    result=ChatService().answer(args.question,history=[],log=False)
    if args.json:
        print(json.dumps({k:result.get(k) for k in ('answer','source_links','quality_status','missing_information','model_used')},ensure_ascii=False,indent=2))
    else:
        print(result['answer'])
        for s in result.get('source_links',[]):print(s['label']+': '+s['url'])
if __name__=='__main__':main()
