"""One-shot external ingestion. No scheduler and no network call unless invoked explicitly.

Examples:
  python scripts/ingest_external.py openaq --location-id 2178
  python scripts/ingest_external.py firms --west 76.7 --south 28.2 --east 77.8 --north 29.1
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from airsource.connectors import fetch_openaq_location_latest, fetch_firms_area
from airsource.ingestion import canonicalize_openaq, canonicalize_firms
from airsource.store import ObservationStore


def main():
    parser=argparse.ArgumentParser(description="Fetch and persist external environmental context")
    sub=parser.add_subparsers(dest="provider",required=True)
    oq=sub.add_parser("openaq"); oq.add_argument("--location-id",type=int,required=True)
    fi=sub.add_parser("firms")
    for name in ("west","south","east","north"): fi.add_argument("--"+name,type=float,required=True)
    fi.add_argument("--source",default="VIIRS_SNPP_NRT"); fi.add_argument("--days",type=int,default=1)
    args=parser.parse_args()
    if args.provider=="openaq":
        frame,meta=fetch_openaq_location_latest(args.location_id)
        canonical=canonicalize_openaq(frame,meta)
    else:
        frame,meta=fetch_firms_area(args.west,args.south,args.east,args.north,source=args.source,day_range=args.days)
        canonical=canonicalize_firms(frame,meta)
    result=ObservationStore(ROOT/"data"/"airsource_observations.sqlite").ingest(canonical,meta)
    print({"provider":args.provider,**result})

if __name__=="__main__": main()
