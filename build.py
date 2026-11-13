"""Build a static, read-only PWA using the existing fail-closed Agri-OS pipeline."""
import json, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DOCS=ROOT/'docs'
DOCS.mkdir(exist_ok=True)
cmd=[sys.executable,str(ROOT/'agri_os.py'),*sys.argv[1:]]
subprocess.run(cmd,check=True,cwd=ROOT,timeout=180)
report=json.loads((ROOT/'report.json').read_text(encoding='utf-8'))
(DOCS/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('Published static report; missing sources remain marked unavailable')
