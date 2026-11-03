"""Download documented OpenCity Delhi monitor CSVs on a network-enabled computer.

No scraping around access restrictions. Fail clearly if the publisher is unreachable.
"""
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime,timezone
import requests

SOURCES={
 'anand-vihar':('Anand Vihar', 'https://data.opencity.in/dataset/0dc7b9fe-9fd4-46ee-a37e-88f0bd6f6362/resource/5ef3f66f-2bb0-4593-91db-ba6e693a77f3/download/del-anand-vihar-dpcc-2024-25.csv'),
 'r-k-puram':('R K Puram','https://data.opencity.in/dataset/delhi-hourly-air-quality-reports/resource/d9dfd28d-038d-448f-8e33-5e6f6b32d15c'),
 'ito':('ITO', 'https://data.opencity.in/dataset/0dc7b9fe-9fd4-46ee-a37e-88f0bd6f6362/resource/890f786d-fb9f-475e-8516-191bfa1b01ea/download/del-ito-cpcb-2024-25.csv'),
}

def fetch(station='anand-vihar',outdir='data/raw'):
    label,url=SOURCES[station]
    target=Path(outdir);target.mkdir(parents=True,exist_ok=True)
    if station=='r-k-puram':
        raise RuntimeError('R K Puram source page is known, but the direct CSV URL is not verified. Use manual CSV download from the published page.')
    try:
        r=requests.get(url,timeout=70,headers={'User-Agent':'AirSourceX-research-project/0.1'},stream=True)
        r.raise_for_status()
        content_type=r.headers.get('Content-Type','')
        if 'html' in content_type.lower():raise RuntimeError('Publisher returned HTML, not a CSV. Use manual download.')
        path=target/f'{station}-2024-25.csv'
        sha=hashlib.sha256();first=b'';size=0
        with open(path,'wb') as f:
            for chunk in r.iter_content(1024*256):
                if chunk:
                    if not first:first=chunk[:1024]
                    f.write(chunk);sha.update(chunk);size+=len(chunk)
        if b'PM2.5' not in first and b'Timestamp' not in first:
            path.unlink(missing_ok=True);raise RuntimeError('Downloaded content is not clearly a station CSV.')
        manifest={'station':label,'url':url,'downloaded_at_utc':datetime.now(timezone.utc).isoformat(),
                  'sha256':sha.hexdigest(),'bytes':size,'file':str(path)}
        (target/f'{station}-manifest.json').write_text(json.dumps(manifest,indent=2))
        return path
    except (requests.RequestException,RuntimeError) as e:
        raise RuntimeError(f'Cannot fetch {station}: {e}. Download manually from the OpenCity page and supply --csv.') from e

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--station',choices=SOURCES,default='anand-vihar');parser.add_argument('--outdir',default='data/raw')
    args=parser.parse_args();print(fetch(args.station,args.outdir))
