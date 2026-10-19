"""Browser integration check on an isolated database; never touches personal data."""
import os
import secrets
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests

ROOT=Path(__file__).resolve().parents[1]


def main():
    from playwright.sync_api import sync_playwright
    output=ROOT/'data'/'verification'
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='athena-browser-') as temporary:
        env=dict(os.environ,ATHENA_DATA_DIR=temporary,ATHENA_JWT_SECRET=secrets.token_urlsafe(48),
                 ATHENA_ALLOWED_HOSTS='127.0.0.1,localhost',ATHENA_ALLOW_REGISTRATION='1',ATHENA_RATE_LIMIT='0')
        log=(output/'browser-server.log').open('w',encoding='utf-8')
        server=subprocess.Popen([sys.executable,'-m','uvicorn','app.api:app','--host','127.0.0.1','--port','8765'],
                                cwd=ROOT,env=env,stdout=log,stderr=log)
        try:
            for _ in range(40):
                if server.poll() is not None:
                    raise RuntimeError('Test server failed; see browser-server.log')
                try:
                    if requests.get('http://127.0.0.1:8765/health',timeout=1).status_code==200:break
                except requests.RequestException:pass
                time.sleep(.25)
            else:raise RuntimeError('Test server did not start')
            with sync_playwright() as playwright:
                edge=Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')
                browser=playwright.chromium.launch(headless=True, **({'executable_path':str(edge)} if edge.exists() else {}))
                page=browser.new_page(viewport={'width':1440,'height':1000})
                errors=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.goto('http://127.0.0.1:8765')
                page.locator('#username').fill('browser_test')
                page.locator('#password').fill('test-password-not-real-123')
                page.locator('#register').click()
                page.locator('#workspace').wait_for(state='visible')
                page.screenshot(path=str(output/'chat-desktop.png'),full_page=True)
                page.locator('[data-tab="code"]').click()
                page.locator('#code-name').fill('hello.py')
                page.locator('#code-content').fill('def hello(name):\n    return f"Hello, {name}"\n')
                page.locator('#code-form button').click()
                page.get_by_role('heading',name='hello.py').wait_for()
                page.screenshot(path=str(output/'code-desktop.png'),full_page=True)
                page.locator('[data-tab="learning"]').click()
                page.locator('#lesson-prompt').fill('How do I add numbers?')
                page.locator('#lesson-answer').fill('def add(a, b):\n    return a + b')
                page.locator('#lesson-approved').check()
                page.locator('#lesson-form button').click()
                page.get_by_role('heading',name='Approved · beginner').wait_for()
                with page.expect_download() as download:
                    page.locator('#export-lessons').click()
                assert download.value.suggested_filename.endswith('.jsonl')
                # Plain text rendering must not run uploaded markup.
                page.locator('[data-tab="photos"]').click()
                import io
                from PIL import Image
                picture=io.BytesIO();Image.new('RGB',(80,60),'green').save(picture,'PNG')
                page.locator('#image-file').set_input_files({'name':'test.png','mimeType':'image/png','buffer':picture.getvalue()})
                page.locator('#image-caption').fill('<script>window.pwned=true</script> Green test image')
                page.locator('#describe-image').uncheck()
                page.locator('#image-form button').click()
                page.locator('#image-list img').wait_for()
                assert page.evaluate('window.pwned') is None
                assert page.evaluate('localStorage.length')==0
                page.screenshot(path=str(output/'photos-desktop.png'),full_page=True)
                page.set_viewport_size({'width':390,'height':844})
                page.screenshot(path=str(output/'photos-mobile.png'),full_page=True)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                assert not errors, errors
                browser.close()
            print('Browser checks passed: register, code editing, lessons, export, image upload, XSS rendering, mobile layout.')
        finally:
            if server.poll() is None and os.name == 'nt':
                # Windows venv python.exe is a launcher with a child process.
                # Stop only the process tree started above, not unrelated servers.
                subprocess.run(['taskkill','/PID',str(server.pid),'/T','/F'],check=False,
                               stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            elif server.poll() is None:
                server.terminate()
            server.wait(timeout=20)
            log.close()


if __name__=='__main__':main()
