from pathlib import Path
from playwright.sync_api import sync_playwright
p=Path(__file__).resolve().parents[1];s=Path(p/'portscanner_pentest_SNAKE_style_560round_refined_manual_20261116.html').read_text()
with sync_playwright() as w:
 b=w.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-gpu']);page=b.new_page(viewport={'width':390,'height':844});page.set_content(s)
 page.locator('#menuButton').click();page.locator('#sidebar [data-target="portfolio"]').click();page.locator('#fontUp').click()
 for label in ('after_font','after_search'):
  if label=='after_search':
   page.locator('#searchButton').click();page.locator('#searchInput').fill('タイムアウト');page.locator('#searchClose').click()
  print(label,page.evaluate('({d:document.documentElement.scrollWidth,b:document.body.scrollWidth,w:innerWidth})'))
  x=page.evaluate('''() => Array.from(document.querySelectorAll('*')).map(e=>({tag:e.tagName,cls:e.className?.toString().slice(0,60),id:e.id,right:e.getBoundingClientRect().right,scroll:e.scrollWidth,width:e.getBoundingClientRect().width,txt:(e.textContent||'').trim().slice(0,45)})).filter(x=>x.right>window.innerWidth+10 && x.width>20).sort((a,b)=>b.right-a.right).slice(0,22)''')
  for r in x:print(r)
 b.close()
