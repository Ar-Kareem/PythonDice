import requests
import re
import dice_calc

version = dice_calc.__version__
print('Version:', version)
r = requests.get(f'https://pypi.org/project/dice-calc/{version}/#files')
resp = r.text
whl_link = re.findall(r'href="(.*\.whl)"', resp)
assert len(whl_link) != 0, 'No .whl link found'
assert len(whl_link) < 2, 'Got more than one .whl link : ' + str(whl_link)
print('Wheel link:\n' + whl_link[0])