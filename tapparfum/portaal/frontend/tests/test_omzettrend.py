from playwright.sync_api import sync_playwright
from datetime import date
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(800)
VANDAAG=date.today().isoformat()
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    # één winkel met één oud meetpunt in joLog + jaaromzet 5000
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:null,
        data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:5000,setup:{skipped:true},joLog:[{at:'2026-01-15',v:5000}]}}];
      window.__MOCK.signin={data:{user:{id:'u-staff',email:'k@tp.nl',app_metadata:{role:'staff'}}},error:null};""")
    login(pg,"k@tp.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(500)
    pg.click('[data-test=tappunt-rij]'); pg.wait_for_timeout(600)

    # 1 meetpunt -> nog geen trend
    ck("geen trend bij 1 meetpunt", pg.locator('[data-test=omzet-trend]').count()==0)

    # jaaromzet wijzigen -> snapshot geschreven
    pg.fill('[data-test=omzet-jaaromzet]','8000')
    pg.click('[data-test=omzet-opslaan]'); pg.wait_for_timeout(600)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    jo=d.get('joLog',[])
    ck("joLog kreeg 2e meetpunt", len(jo)==2)
    ck("nieuw meetpunt = vandaag, v=8000", jo[-1]['at'][:10]==VANDAAG and jo[-1]['v']==8000)

    # trend verschijnt nu (2 punten: 5000 -> 8000 = +60%, omhoog)
    ck("omzet-trend zichtbaar bij 2 meetpunten", pg.locator('[data-test=omzet-trend]').count()==1)
    dl=pg.text_content('[data-test=trend-delta]') or ''
    ck("richting omhoog +60%", '▲' in dl and '+60%' in dl)

    # zelfde dag opnieuw wijzigen -> geen dubbel meetpunt, laatste bijgewerkt
    pg.fill('[data-test=omzet-jaaromzet]','9000')
    pg.click('[data-test=omzet-opslaan]'); pg.wait_for_timeout(600)
    d2=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    jo2=d2.get('joLog',[])
    ck("zelfde dag: nog steeds 2 meetpunten (bijgewerkt)", len(jo2)==2 and jo2[-1]['v']==9000)

    # ongewijzigd opslaan -> geen extra meetpunt
    pg.click('[data-test=omzet-opslaan]'); pg.wait_for_timeout(500)
    d3=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("ongewijzigd: geen extra meetpunt", len(d3.get('joLog',[]))==2)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
