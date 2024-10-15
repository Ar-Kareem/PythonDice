
import json
from pathlib import Path
import requests
import os
import sys
import time
import random
from dotenv import load_dotenv
from datetime import datetime

from fetch_in import code_library

load_dotenv('.evn.secret')
C = os.getenv('ANYDICE_COOKIE')
assert isinstance(C, str) and len(C) > 10, 'no cookie'

cur_dir = Path(__file__).parent
fetch_out = json.loads((cur_dir / 'fetch_out.json').read_text())
done_inps_set = set([x['inp'] for x in fetch_out['data']])
new_inps = set([x for x in code_library if x.strip() and x not in done_inps_set])
print('TODO:', len(new_inps))

if input('y to continue: ') != 'y':
    sys.exit(0)

for inp in new_inps:
    resp = requests.post('https://anydice.com/calculator_limited.php', {'program': inp}, cookies={'anydice': C})
    print('GOT', resp.text)
    fetch_out['data'].append({'inp': inp, 'out': resp.text, 'time': datetime.now().isoformat()})
    time.sleep(0.5 + random.random() * 0.5)

with open(cur_dir / 'fetch_out.json', 'w') as f:
    json.dump(fetch_out, f, indent=2)
