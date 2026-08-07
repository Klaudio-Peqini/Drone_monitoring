from __future__ import annotations
from pathlib import Path
import json, hashlib

ROOT = Path(__file__).resolve().parents[1]

def sha256(path: Path, chunk=1024*1024):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(chunk),b''): h.update(b)
    return h.hexdigest()

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write_json(path,obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2)+"\n",encoding='utf-8')
