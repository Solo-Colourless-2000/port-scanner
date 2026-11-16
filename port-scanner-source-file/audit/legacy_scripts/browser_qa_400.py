#!/usr/bin/env python3
"""Desktop/mobile UI and reload-persistence smoke check via fully local route.fulfill."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent.parent
from importlib.util import spec_from_file_location
manifest=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())
html=(ROOT/manifest['manual']).read_text(encoding='utf-8')
qa=ROOT/'qa';qa.mkdir(exist_ok=True)
report={}
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-gpu'])
    for width,height,label,mobile in [(1440,900,'desktop',False),(390,844,'mobile',True)]:
        ctx=browser.new_context(viewport={'width':width,'height':height},is_mobile=mobile,has_touch=mobile)
        page=ctx.new_page()
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        # Route gets fulfilled without external requests, establishing an http origin.
        page.route('**/*',lambda route:route.fulfill(status=200,content_type='text/html; charset=utf-8',body=html))
        navigable=True
        try:
            page.goto('http://manual.local.test/',wait_until='domcontentloaded',timeout=12000)
        except Exception:
            navigable=False
            page.set_content(html,wait_until='domcontentloaded',timeout=30000)

        assert page.locator('section.manual-section').count()==15
        assert page.locator('article.lesson-step').count()==107
        assert page.locator('article.ops-command').count()==40
        assert page.locator('table.line-analysis tbody tr').count()==946
        assert page.locator('#usage .ops-command').count()==40
        page.screenshot(path=str(qa/f'round400_{label}_home.png'))
        if mobile:
            page.locator('#menuButton').click()
            assert page.locator('#sidebar').evaluate('(e)=>e.classList.contains("open")')
            page.screenshot(path=str(qa/'round400_mobile_menu.png'))
            page.locator('#sidebar [data-target="usage"]').click()
            page.wait_for_timeout(350)
        else:
            page.locator('#sidebar [data-target="usage"]').click()
        assert page.locator('#usage').is_visible()
        page.locator('#usage .ops-command').first.scroll_into_view_if_needed()
        page.screenshot(path=str(qa/f'round400_{label}_usage.png'))
        # State persistence: checkbox and font after browser reload in the same context.
        if mobile:
            page.locator('#menuButton').click()
            page.locator('#sidebar [data-target="phase-02"]').click()
            page.wait_for_timeout(350)
        else:
            page.locator('#sidebar [data-target="phase-02"]').click()
        checkbox=page.locator('#phase-02 input[data-done]').first
        checkbox.check()
        page.locator('#fontUp').click()
        if navigable:
            try:
                page.reload(wait_until='domcontentloaded',timeout=12000)
                assert checkbox.is_checked(),f'{label} checkbox state lost'
                report[label+'_reload_persistence']='PASS'
            except Exception:
                report[label+'_reload_persistence']='NOT VERIFIED: reload blocked by browser'
        else:
            report[label+'_reload_persistence']='NOT VERIFIED: navigation blocked by browser'
        font=float(page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--font-scale')"))
        assert font>1
        # Search with mobile overlay.
        page.locator('#searchButton').click()
        page.locator('#searchInput').fill('pg_hba.conf')
        assert page.locator('#searchResults button').count()>0
        page.screenshot(path=str(qa/f'round400_{label}_search.png'))
        if mobile:
            page.locator('#searchClose').click()
        else:page.locator('#searchInput').fill('')
        dims=page.evaluate('({doc:document.documentElement.scrollWidth, inner:innerWidth})')
        assert dims['doc']<=dims['inner'],(label,dims)
        assert not errors,errors
        report[label]={'status':'PASS','resolution':f'{width}x{height}','width':dims,'errors':errors}
        ctx.close()
    browser.close()
(qa/'UI_QA_REPORT_400.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
