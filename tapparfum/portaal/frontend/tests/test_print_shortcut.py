from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(700)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle'}}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"m@t.nl")
    pg.keyboard.press('/'); pg.wait_for_timeout(300)
    ck("'/'-sneltoets opent zoeken", pg.locator('[data-test=zoek-veld]').count()==1)
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    ck("Esc sluit zoeken", pg.locator('[data-test=zoek-veld]').count()==0)
    pg.click('nav >> text=Formulieren'); pg.wait_for_timeout(500)
    ck("Formulieren heeft Print/PDF-knop", pg.locator('[data-test=form-print]').count()==1)
    pg.click('nav >> text=Proces'); pg.wait_for_timeout(400)
    ck("Proces heeft Print/PDF-knop", pg.locator('[data-test=proces-print]').count()==1)
    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
