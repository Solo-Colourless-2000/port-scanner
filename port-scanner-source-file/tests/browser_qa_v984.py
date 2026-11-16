#!/usr/bin/env python3
"""Localhost-only Chromium smoke test, including real reload persistence."""
import json, threading
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright, Error
R=Path(__file__).resolve().parents[1]
HTML='portscanner_pentest_development_manual_v984_20261117.html'
QA=R/'qa';QA.mkdir(exist_ok=True)
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(R),**kwargs)
    def log_message(self, format,*args):pass
srv=ThreadingHTTPServer(('127.0.0.1',0),Handler)
threading.Thread(target=srv.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{srv.server_port}/{HTML}'
checks={}
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    for mode,width,height in [('desktop',1440,900),('mobile',390,844)]:
        context=browser.new_context(viewport={'width':width,'height':height})
        page=context.new_page(); errors=[]
        page.on('pageerror',lambda exc: errors.append(str(exc)))
        loaded_with='localhost'
        try:
            page.goto(url,wait_until='domcontentloaded',timeout=5000)
        except Error:
            loaded_with='set_content (localhost navigation blocked)'
            page.set_content((R/HTML).read_text(encoding='utf-8'),wait_until='domcontentloaded')
        page.wait_for_selector('#home.active')
        if mode=='mobile':
            page.locator('#menuButton').click()
            page.wait_for_selector('#sidebar.open')
        page.locator('#sidebar [data-target="report-compare"]').click()
        page.wait_for_selector('#report-compare.active')
        assert page.locator('#utf8-validation-v984').count()==1
        page.wait_for_timeout(350)  # allow mobile drawer closing animation to complete
        assert not page.locator('#sidebar').evaluate('(el)=>el.classList.contains("open")')
        page.screenshot(path=str(QA/f'v984_{mode}_reportdiff.png'),full_page=False)
        page.locator('#diff-step-03').scroll_into_view_if_needed()
        page.screenshot(path=str(QA/f'v984_{mode}_code_step.png'),full_page=False)
        page.locator('#utf8-validation-v984').scroll_into_view_if_needed()
        assert page.locator('#utf8-validation-v984').is_visible()
        page.screenshot(path=str(QA/f'v984_{mode}_utf8_guide.png'),full_page=False)
        page.locator('#diff-step-01 input[data-diff-done]').check()
        assert page.locator('#diff-step-01 input[data-diff-done]').is_checked()
        persistence_verified=False
        if loaded_with=='localhost':
            page.reload(wait_until='domcontentloaded')
            page.wait_for_selector('body')
            assert page.locator('#diff-step-01 input[data-diff-done]').is_checked(),'diff progress lost on reload'
            persistence_verified=True
        if mode=='desktop':
            page.locator('#sidebar [data-target="report-compare"]').click()
            page.locator('#searchInput').fill('集合差')
        else:
            page.locator('#searchButton').click()
            page.locator('#searchInput').fill('集合差')
        page.wait_for_timeout(300)
        panel=page.locator('#searchPanel')
        assert panel.is_visible(),'search panel not visible'
        assert page.locator('#searchResults').inner_text().strip(),'search results empty'
        # Clear search without needing to click a result (the panel is floating).
        page.keyboard.press('Escape')
        sizing=page.evaluate('({w:document.documentElement.scrollWidth,v:innerWidth})')
        checks[mode]={'horizontal_overflow': sizing['w']-sizing['v'], 'js_errors':errors,
                      'diff_progress_survived_reload':persistence_verified, 'loading_method':loaded_with, 'search_ok':True,
                      'screenshots':f'qa/v984_{mode}_reportdiff.png'}
        assert sizing['w']<=sizing['v']+2,sizing
        assert not errors,errors
        context.close()
    browser.close()
srv.shutdown();srv.server_close()
(QA/'UI_QA_REPORT_v984.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS browser QA',checks)
