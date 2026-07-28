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

    # standaard: content niet gecentreerd
    ck("content standaard niet gecentreerd", not pg.locator('.content').evaluate("el=>el.classList.contains('mid')"))

    pg.click('nav >> text=Beheer'); pg.wait_for_timeout(400)
    pg.click('[data-test=tab-regie]'); pg.wait_for_timeout(300)
    ck("layout-keuze voor kantoor aanwezig", pg.locator('[data-test=align-kantoor]').count()==1)

    pg.select_option('[data-test=align-kantoor]','midden')
    pg.click('[data-test=inst-opslaan]'); pg.wait_for_timeout(500)
    up=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='central' && u[1]['ns']==='layout').slice(-1)[0][1]['data']")
    ck("layout opgeslagen: align.kantoor=midden", (up.get('align') or {}).get('kantoor')=='midden')

    # live toegepast: content krijgt .mid (kantoor = huidige rol)
    ck("content live gecentreerd", pg.locator('.content').evaluate("el=>el.classList.contains('mid')"))

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
