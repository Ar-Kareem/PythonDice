import json
from pathlib import Path
import argparse
import sys


def fix_outs():
    cur_dir = Path(__file__).parent
    fetch_out_path = cur_dir / 'fetch_out.json'
    js = json.loads(fetch_out_path.read_text())
    for i in range(len(js['data'])):
        js['data'][i]['i'] = i
    fetch_out_path.write_text(json.dumps(js, indent=2))


def fix_ins():
    cur_dir = Path(__file__).parent
    js_auto_path = cur_dir / 'fetch_auto_in.json'
    js = json.loads(js_auto_path.read_text())
    js_keys = list(js['data'].keys())
    for i in range(len(js['data'])):
        js['data'][js_keys[i]]['i'] = i
    js_auto_path.write_text(json.dumps(js, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fix_outs', action='store_true', help='fix_outs')
    parser.add_argument('--fix_ins', action='store_true', help='fix_ins')
    args = parser.parse_args()
    if args.fix_ins:
        fix_ins()
    elif args.fix_outs:
        fix_outs()
    else:
        parser.print_help()
        sys.exit(1)
