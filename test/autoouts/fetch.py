#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
import os
import sys
import time
import random
from datetime import datetime
import re

from fetch_in import code_library

BASE_URL_CALC = 'https://anydice.com/calculator_limited.php'
BASE_URL_GET = 'https://anydice.com/program/'

js_auto_path = Path(__file__).parent / 'fetch_auto_in.json'

def get_cookie():
    from dotenv import load_dotenv
    load_dotenv('.evn.secret')
    C = os.getenv('ANYDICE_COOKIE')
    assert isinstance(C, str) and len(C) > 10, 'no cookie! To get coockie: Go to the https://anydice.com, open dev tools, go to network tab, click on the request, copy the cookie'
    return C

def get_anydice_resp(inp, C):
    import requests
    return requests.post(BASE_URL_CALC, {'program': inp}, cookies={'anydice': C})

SCRIPT_PRE = r'<script>\s*var loadedProgram = "'
SCRIPT_POST = r'";\$\(function\(\){}\);\s*</script>'
RE_SCRIPT = re.compile(SCRIPT_PRE + r'(.+?)' + SCRIPT_POST, re.DOTALL)
def get_prog(code):
    import requests
    resp = requests.get(BASE_URL_GET + code)
    m = RE_SCRIPT.search(resp.text)
    if not m:
        raise ValueError('Script not found')
    s = m.group(1)
    # fix the escaped characters
    s = s.encode('ascii', 'ignore').decode('unicode_escape')
    return s

def hex_plus_one(s):
    b16 = int(s, 16) + 1
    return hex(b16)[2:]

def populate_prog(js, prog_key=None):
    if prog_key is None:
        last_code = js['last_done']
        prog_key = hex_plus_one(last_code)
    print('doing:', prog_key)
    new_entry = {'time': datetime.now().isoformat()}
    try:
        new_entry['prog'] = get_prog(prog_key)
    except ValueError as e:
        new_entry['error'] = str(e)
    js['last_done'] = prog_key
    js['data'][prog_key] = new_entry


def populate_loop():
    js = json.loads(js_auto_path.read_text())
    while True:
        populate_prog(js)
        js_auto_path.write_text(json.dumps(js, indent=2))
        time.sleep(0.5 + random.random() * 0.5)
        if random.random() < 0.02:
            print('Sleeping for 1-2 minutes')
            time.sleep(60 + random.random() * 60)
        # if random.random() < 0.001:
        #     print('Sleeping for 10-11 minutes. Very unlukcy')
        #     time.sleep(600 + random.random() * 60)


def main_fetch():
    cur_dir = Path(__file__).parent
    fetch_out = json.loads((cur_dir / 'fetch_out.json').read_text())
    done_inps_set = set([x['inp'] for x in fetch_out['data']])
    # preserve order
    new_inps_set = set([x for x in code_library if x.strip() and x not in done_inps_set])
    new_inps = [('manual', x) for x in code_library if x in new_inps_set]
    # from fetch_auto_in.json
    js_auto = json.loads(js_auto_path.read_text())['data']
    new_inps_set = set([x['prog'] for (k, x) in js_auto.items() if x.get('prog', '').strip() and x['prog'] not in done_inps_set])
    new_inps += [(k, x['prog']) for (k, x) in js_auto.items() if x.get('prog', False) in new_inps_set]

    if not new_inps:
        print('No new inputs to fetch.\nAdd inputs to fetch_in.py')
        sys.exit(0)
    print('Code to request:', len(new_inps))
    C = get_cookie()
    for (key, inp) in new_inps:
        resp = get_anydice_resp(inp, C)
        print('GOT', resp.text)
        fetch_out['data'].append({'inp': inp, 'out': resp.text, 'key': key, 'time': datetime.now().isoformat(), 'i': len(fetch_out['data'])})
        with open(cur_dir / 'fetch_out.json', 'w') as f:
            json.dump(fetch_out, f, indent=2)
        time.sleep(1 + random.random() * 5)  # sleep for 1-6 seconds
        if random.random()*100 < 1:  # 1%
            print('Sleeping for 1-2 minutes')
            time.sleep(60 + random.random() * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch anydice outputs')
    parser.add_argument('--fetch', action='store_true', help='Fetch results for current progs in fetch_in.py')
    parser.add_argument('--populate', action='store_true', help='Populate auto inputs by incrementally fetching')
    args = parser.parse_args()
    if args.fetch:
        main_fetch()
    elif args.populate:
        populate_loop()
    else:
        parser.print_help()
        sys.exit(1)
