from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(600)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle',
        logboek:[{id:'g1',at:'2026-07-01',type:'bezoek',txt:'Langs geweest',duurMin:75,gps:{lat:52.5,lng:6.09,loc:'Zwolle centrum'},nextDate:'',nextDone:false}]}}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"m@t.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(400)
    pg.locator('[data-test=tappunt-rij]').first.click(); pg.wait_for_timeout(700)
    ck("geïmporteerde bezoekduur getoond (v71 fmtDuur)", '1 u 15' in (pg.text_content('[data-test=log-duur-badge]') or ''))
    ck("gps-pin uit importdata getoond", pg.locator('.gps').count()==1)
    # mail met richting registreren
    pg.select_option('[data-test=log-type]','mail'); pg.wait_for_timeout(150)
    ck("mailrichting-keuze verschijnt bij type mail", pg.locator('[data-test=log-dir]').count()==1)
    pg.select_option('[data-test=log-dir]','in')
    pg.fill('[data-test=log-tekst]','Klant reageerde')
    pg.click('[data-test=log-toevoegen]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("mail met dir=in opgeslagen (v71-veld)", d['logboek'][0].get('type')=='mail' and d['logboek'][0].get('dir')=='in')
    ck("richting-badge '↓ ontvangen' getoond", '↓ ontvangen' in (pg.text_content('[data-test=log-mdir]') or ''))
    # bezoek met duur
    pg.select_option('[data-test=log-type]','bezoek'); pg.wait_for_timeout(150)
    ck("duur-veld verschijnt bij type bezoek", pg.locator('[data-test=log-duur]').count()==1)
    pg.fill('[data-test=log-duur]','40'); pg.fill('[data-test=log-tekst]','Kort langs')
    pg.click('[data-test=log-toevoegen]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("bezoek met duurMin=40 opgeslagen", d['logboek'][0].get('type')=='bezoek' and d['logboek'][0].get('duurMin')==40)
    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
