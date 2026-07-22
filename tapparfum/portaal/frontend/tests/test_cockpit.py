from playwright.sync_api import sync_playwright
from datetime import date
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1

INIT=open("/tmp/claude-0/-home-user-memeradar/b0dc4ae2-3376-5404-9da1-5b0364a4f411/scratchpad/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
VANDAAG=date.today().isoformat()

def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x')
    pg.click('button[type=submit]'); pg.wait_for_timeout(700)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT)
    pg.goto(URL); pg.wait_for_timeout(500)

    # 3 winkels: groeit / stagneert / nieuw
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[
        {snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
         data:{snelstart:'kl-1',name:'Zwolle',plaats:'Zwolle',jaaromzet:22000,setup:{skipped:true}}},
        {snelstart:'kl-2',name:'Deventer',email:null,geblokkeerd:false,am_id:'am-1',
         data:{snelstart:'kl-2',name:'Deventer',plaats:'Deventer',jaaromzet:0,vorigJaar:5000,setup:{skipped:true}}},
        {snelstart:'kl-3',name:'Kampen',email:null,geblokkeerd:false,am_id:'am-1',
         data:{snelstart:'kl-3',name:'Kampen',plaats:'Kampen',jaaromzet:500,be:{inv:3950,rev:16.53,perWk:20,days:84,bottles:239}}}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"marian@tp.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(600)

    ck("KPI-rij: 3 winkels + 1 A-klant", '3' in (pg.text_content('.kpis') or '') and '1' in (pg.text_content('.kpis') or ''))
    ck("filterchips met tellingen", pg.locator('[data-test=filter-alle]').count()==1 and pg.locator('[data-test=filter-stagneert]').count()==1)
    ck("status-groepen: stagneert + nieuw + groeit", pg.locator('[data-test=groep-stagneert]').count()==1 and pg.locator('[data-test=groep-nieuw]').count()==1 and pg.locator('[data-test=groep-groeit]').count()==1)
    ck("Zwolle (22000) = groeit met niveau A", 'A' in (pg.text_content('.kaart:has-text(\"Zwolle\") .niveau') or ''))
    ck("kaart toont next-step hint", '→' in (pg.text_content('.kaart:has-text(\"Kampen\")') or ''))
    # filter op stagneert
    pg.click('[data-test=filter-stagneert]'); pg.wait_for_timeout(300)
    ck("filter stagneert -> alleen Deventer zichtbaar", pg.locator('[data-test=tappunt-rij]').count()==1 and 'Deventer' in (pg.text_content('.kaart') or ''))
    pg.click('[data-test=filter-alle]'); pg.wait_for_timeout(300)

    # open Deventer -> situatie-switch
    pg.click('.kaart:has-text("Deventer")'); pg.wait_for_timeout(700)
    ck("situatieblok: auto = Stagneert", 'Stagneert' in (pg.text_content('[data-test=sit-auto]') or ''))
    pg.click('[data-test=sit-top]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("handmatig op Top -> statusManual='top'", d.get('statusManual')=='top')
    pg.click('[data-test=sit-auto]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("terug op Auto -> statusManual leeg", d.get('statusManual')=='')
    # klanten-teller
    pg.fill('[data-test=klanten-in]','42'); pg.locator('[data-test=klanten-in]').blur(); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("vaste klanten -> t.klanten=42", d.get('klanten')==42)

    # open Kampen -> markeer break-even
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(400)
    pg.click('.kaart:has-text("Kampen")'); pg.wait_for_timeout(700)
    pg.click('[data-test=markeer-be]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("markeer break-even -> beDone + beDoneAt + viering", d.get('beDone')==True and d.get('beDoneAt')==VANDAAG and any(v.get('type')=='be' for v in d.get('vieringen',[])))

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
