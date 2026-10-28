"""Smoke test for local app, Chrome desktop + mobile using Playwright."""
import functools
import http.server
import socketserver
import threading
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
class Reusable(socketserver.TCPServer):allow_reuse_address=True
handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT))
server=Reusable(('127.0.0.1',0),handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
url=(ROOT/'index.html').as_uri()
print('TEST URL',url)
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for name,w,h in [('desktop',1440,900),('mobile',390,844)]:
  ctx=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=1)
  page=ctx.new_page()
  errors=[]
  page.on('pageerror',lambda x:errors.append(str(x)))
  page.route('**/raw.githubusercontent.com/**',lambda route: route.abort('failed'))
  html=(ROOT/'index.html').read_text(encoding='utf-8')
  html=html.replace('<link rel="stylesheet" href="./styles.css"/>','<style>'+ (ROOT/'styles.css').read_text(encoding='utf-8') +'</style>')
  html=html.replace('<script defer src="./app.js"></script>','<script>'+ (ROOT/'app.js').read_text(encoding='utf-8') +'</script>')
  page.set_content(html,wait_until='domcontentloaded')
  page.wait_for_timeout(600)
  print(name,'title',page.title(),'latest',page.locator('#lastRound').inner_text(),'metrics',page.locator('#metricDraws').inner_text())
  assert page.locator('#metricDraws').inner_text()=='5'
  assert page.locator('#bandChart .chart-row').count()==5
  assert page.locator('#pairList .pair-line').count()>0
  page.locator('#generate').click()
  assert page.locator('#generatedList .result-line').count()==5
  page.locator('#saveGenerated').click()
  assert page.locator('#savedList .saved-line').count()==5
  page.locator('#oddPref').select_option('6')
  page.locator('#sumMin').fill('250')
  page.locator('#sumMax').fill('255')
  page.locator('#generate').click()
  assert page.locator('#generatedList .result-line').count()==0
  page.locator('#resetGen').click()
  page.locator('#fixed').fill('1,2,3')
  page.locator('#excluded').fill('1, 5')
  page.locator('#generate').click()
  assert '겹칩니다' in page.locator('#genMessage').inner_text()
  page.locator('#fixed').fill('')
  page.locator('#excluded').fill('')
  csv=(ROOT.parent/'lotto_sample_5rounds.csv').read_bytes()
  page.locator('#csvFile').set_input_files({'name':'sample.csv','mimeType':'text/csv','buffer':csv})
  assert '5회 불러옴' in page.locator('#importMessage').inner_text()
  page.screenshot(path=str(ROOT.parent/f'lotto_v2_{name}.png'),full_page=True)
  print(name,'page errors',errors,'horizontal overflow',page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth'))
  assert not errors,errors
  assert not page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth'),'horizontal scroll'
  ctx.close()
 browser.close()
server.shutdown()
print('BROWSER SMOKE PASS')
