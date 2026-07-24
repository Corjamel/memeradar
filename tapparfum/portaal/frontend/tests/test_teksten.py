from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(800)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:null,data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:5000}}];
      window.__MOCK.signin={data:{user:{id:'u-staff',email:'k@tp.nl',app_metadata:{role:'staff'}}},error:null};""")
    login(pg,"k@tp.nl")

    # standaard-nav-label + topbar
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(400)
    ck("standaard topbar-titel Winkels", (pg.text_content('.tb-title') or '').strip()=='Winkels')

    pg.click('nav >> text=Beheer'); pg.wait_for_timeout(400)
    pg.click('[data-test=tab-teksten]'); pg.wait_for_timeout(300)
    ck("teksten-veld voor 'winkels' aanwezig", pg.locator('[data-test=tekst-winkels]').count()==1)

    pg.fill('[data-test=tekst-winkels]','Mijn tapbars')
    pg.click('[data-test=teksten-opslaan]'); pg.wait_for_timeout(500)
    up=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='central' && u[1]['ns']==='teksten').slice(-1)[0][1]['data']")
    ck("override opgeslagen title.winkels", up.get('title.winkels')=='Mijn tapbars')

    # live toegepast: nav-label bijgewerkt
    ck("nav-label live 'Mijn tapbars'", pg.locator("nav >> text=Mijn tapbars").count()==1)
    pg.click('nav >> text=Mijn tapbars'); pg.wait_for_timeout(400)
    ck("topbar-titel live 'Mijn tapbars'", (pg.text_content('.tb-title') or '').strip()=='Mijn tapbars')

    # reset leegt de velden
    pg.click('nav >> text=Beheer'); pg.wait_for_timeout(300)
    pg.click('[data-test=tab-teksten]'); pg.wait_for_timeout(300)
    ck("override herladen in veld", pg.input_value('[data-test=tekst-winkels]')=='Mijn tapbars')
    pg.click('[data-test=teksten-reset]'); pg.wait_for_timeout(200)
    ck("reset leegt veld", pg.input_value('[data-test=tekst-winkels]')=='')

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
