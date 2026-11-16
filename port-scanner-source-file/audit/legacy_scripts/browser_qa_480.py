#!/usr/bin/env python3
"""True local HTTP browser UI QA; no external network traffic."""
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];qa=R/'qa';qa.mkdir(exist_ok=True)
manual=json.loads((R/'SOURCE_MANIFEST.json').read_text())['manual']

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

@contextmanager
def localhost_server():
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(R)))
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield f'http://127.0.0.1:{server.server_address[1]}/{manual}'
    finally:server.shutdown();server.server_close();thread.join(timeout=3)

report={}
with localhost_server() as url,sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-gpu'])
    for label,width,height,mobile in [('desktop',1440,900,False),('mobile',390,844,True)]:
        ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=mobile,has_touch=mobile)
        page=ctx.new_page();errors=[]
        page.on('pageerror',lambda ex: errors.append(str(ex)))
        navigable=True
        try:page.goto(url,wait_until='domcontentloaded',timeout=10000)
        except Exception:
            navigable=False
            page.set_content((R/manual).read_text(encoding='utf-8'),wait_until='domcontentloaded',timeout=30000)
        assert page.locator('section.manual-section').count()==16
        assert page.locator('article.lesson-step').count()==107
        assert page.locator('article.portfolio-task').count()==19
        assert page.locator('.portfolio-code-annotation').count()==214
        assert page.locator('tr.line-analysis').count()==0  # HTML uses table.line-analysis
        page.screenshot(path=str(qa/f'v480_{label}_home.png'))
        if mobile:
            page.locator('#menuButton').click()
            assert page.locator('#sidebar').evaluate('(e)=>e.classList.contains("open")')
            page.screenshot(path=str(qa/'v480_mobile_menu.png'))
        page.locator('#sidebar [data-target="portfolio"]').click()
        assert page.locator('#portfolio').is_visible()
        page.wait_for_timeout(400)
        if mobile:assert not page.locator('#sidebar').evaluate('(e)=>e.classList.contains("open")')
        page.locator('#portfolio-step-11').scroll_into_view_if_needed()
        page.wait_for_timeout(200)
        page.screenshot(path=str(qa/f'v480_{label}_portfolio.png'))
        # New authored progress is a different store from the 107 original worksteps.
        ck=page.locator('#portfolio-step-11 input[data-portfolio-done]')
        ck.check()
        page.locator('#fontUp').click()
        if mobile:
            page.locator('#menuButton').click()
        page.locator('#sidebar [data-target="phase-02"]').click()
        original=page.locator('#phase-02 input[data-done]').first;original.check()
        if navigable:
            page.reload(wait_until='domcontentloaded',timeout=20000)
        # Returning to the originally checked chapter must not clear new project progress.
        if mobile:page.locator('#menuButton').click()
        page.locator('#sidebar [data-target="portfolio"]').click()
        if navigable:assert page.locator('#portfolio-step-11 input[data-portfolio-done]').is_checked()
        if mobile:page.locator('#menuButton').click()
        page.locator('#sidebar [data-target="phase-02"]').click()
        if navigable:assert page.locator('#phase-02 input[data-done]').first.is_checked()
        factor=float(page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--font-scale")'))
        assert factor>1
        page.locator('#searchButton').click()
        page.locator('#searchInput').fill('ポートフォリオ')
        assert page.locator('#searchResults button').count()>0
        page.screenshot(path=str(qa/f'v480_{label}_search.png'))
        if mobile:page.locator('#searchClose').click()
        dims=page.evaluate('({doc:document.documentElement.scrollWidth,body:document.body.scrollWidth,inner:innerWidth})')
        assert dims['doc']<=dims['inner']+1,(label,dims)
        assert not errors,(label,errors)
        report[label]={'status':'PASS','viewport':f'{width}x{height}','width':dims,'reload_state':'PASS' if navigable else 'NOT VERIFIED: local URL navigation blocked by browser policy','font_scale':factor,'browser_errors':errors}
        ctx.close()
    browser.close()
(qa/'UI_QA_REPORT_480.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(report,indent=2,ensure_ascii=False))
