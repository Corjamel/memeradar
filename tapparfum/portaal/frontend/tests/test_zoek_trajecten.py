from playwright.sync_api import sync_playwright
from datetime import date, timedelta
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1

INIT=open("/tmp/claude-0/-home-user-memeradar/b0dc4ae2-3376-5404-9da1-5b0364a4f411/scratchpad/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
VANDAAG=date.today().isoformat()
GISTER=(date.today()-timedelta(days=1)).isoformat()

def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x')
    pg.click('button[type=submit]'); pg.wait_for_timeout(700)
def uitloggen(pg):
    pg.click('button:has-text("Uitloggen")'); pg.wait_for_timeout(400)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT)
    pg.goto(URL); pg.wait_for_timeout(500)

    # ===== AM: trajecten + heractiveren =====
    pg.evaluate(f"""window.__DB.accountmanagers=[{{id:'am-1',naam:'Marian',auth_user_id:'u-am'}}];
      window.__DB.tappunten=[
        {{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
         data:{{snelstart:'kl-1',name:'Zwolle',tel:'038-111',jaaromzet:12000,setup:{{skipped:true}},contact:'Karin',
               logboek:[{{id:'l1',at:'{GISTER}',type:'bezoek',txt:'Tapbar verplaatst naar de ingang',nextDate:'',nextDone:false}}],
               afspraken:[{{id:'a1',at:'{GISTER}',txt:'Zomerposter ophangen',done:false}}],
               bestellingen:[{{id:'b1',at:'{GISTER}',ref:'F7788',totaal:950,omschrijving:'refill pakket',bron:'handmatig'}}]}}}},
        {{snelstart:'kl-2',name:'Deventer',email:null,geblokkeerd:false,am_id:'am-1',
         data:{{snelstart:'kl-2',name:'Deventer',jaaromzet:0,vorigJaar:5000,setup:{{skipped:true}}}}}},
        {{snelstart:'kl-3',name:'Kampen',email:null,geblokkeerd:false,am_id:'am-1',
         data:{{snelstart:'kl-3',name:'Kampen',jaaromzet:400}}}}];
      window.__MOCK.signin={{data:{{user:{{id:'u-am',app_metadata:{{}}}}}},error:null}};""")
    login(pg,"marian@tp.nl")
    pg.click('nav >> text=Trajecten'); pg.wait_for_timeout(700)

    ck("4 traject-tegels (v71 TRAJ)", all(pg.locator(f'[data-test=traj-tegel-{k}]').count()==1 for k in ['nieuw','groeit','stagneert','top']))
    ck("verdeling: groeit=1, stagneert=1, nieuw=1", '1' in (pg.text_content('[data-test=traj-tegel-groeit]') or '') and '1' in (pg.text_content('[data-test=traj-tegel-stagneert]') or '') and '1' in (pg.text_content('[data-test=traj-tegel-nieuw]') or ''))
    ck("Deventer in stagneert-groep", pg.locator('[data-test=traj-stagneert-kl-2]').count()==1)
    ck("Kampen (checklist open) in nieuw-groep met calculator-hint", 'break-evenplan' in (pg.text_content('[data-test=traj-nieuw-kl-3]') or ''))
    # heractivatie-actie vastleggen bij Deventer
    pg.select_option('[data-test=react-actie-kl-2]','Gebeld / langsgegaan — situatie besproken')
    pg.fill('[data-test=react-opvolg-kl-2]', GISTER)   # bewust in het verleden -> meteen 'te laat' op Vandaag
    pg.click('[data-test=react-vastleggen-kl-2]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    r0=d['react'][0]
    ck("vastleggen -> t.react[{date,actie,opvolg,done:false}] (v71-veld)", r0['date']==VANDAAG and 'Gebeld' in r0['actie'] and r0['opvolg']==GISTER and r0['done']==False)
    ck("react-rij zichtbaar met opvolgdatum", pg.locator('[data-test=react-rij-kl-2]').count()==1)

    # Vandaag: heractivatie-opvolging als 'te laat'
    pg.evaluate("window.__DB.tappunten[1].data.react=[{date:'"+VANDAAG+"',actie:'Gebeld / langsgegaan — situatie besproken',opvolg:'"+GISTER+"',done:false}]")
    pg.click('nav >> text=Vandaag'); pg.wait_for_timeout(800)
    ck("Vandaag: heractivatie-item te laat in Nu", pg.locator('[data-test=item-react]').count()==1 and 'te laat' in (pg.text_content('[data-test=item-react]') or ''))
    pg.locator('[data-test=vink-react-kl-2]').click(); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("afvinken op Vandaag -> react.done=true", d['react'][0]['done']==True)

    # ===== Globale zoekfunctie =====
    pg.click('[data-test=zoek-knop]'); pg.wait_for_timeout(400)
    ck("zoek-overlay opent met uitleg (min 2 tekens)", 'minimaal 2 tekens' in (pg.text_content('.paneel') or ''))
    pg.fill('[data-test=zoek-veld]','tapbar'); pg.wait_for_timeout(400)
    ck("notitie gevonden op inhoud ('Tapbar verplaatst')", pg.locator('[data-test=zoek-hit-log]').count()==1 and 'Tapbar verplaatst' in (pg.text_content('[data-test=zoek-hit-log]') or ''))
    pg.fill('[data-test=zoek-veld]','F7788'); pg.wait_for_timeout(400)
    ck("bestelling gevonden op ordernummer", pg.locator('[data-test=zoek-hit-bestelling]').count()==1 and '950' in (pg.text_content('[data-test=zoek-hit-bestelling]') or ''))
    pg.fill('[data-test=zoek-veld]','zomerposter'); pg.wait_for_timeout(400)
    ck("afspraak gevonden + status open", 'open' in (pg.text_content('[data-test=zoek-hit-afspraak]') or ''))
    pg.fill('[data-test=zoek-veld]','karin'); pg.wait_for_timeout(400)
    ck("winkel gevonden op contactpersoon", pg.locator('[data-test=zoek-hit-tp]').count()==1 and 'Zwolle' in (pg.text_content('[data-test=zoek-hit-tp]') or ''))
    pg.fill('[data-test=zoek-veld]','xyzniets'); pg.wait_for_timeout(400)
    ck("niets gevonden-melding", pg.locator('[data-test=zoek-leeg]').count()==1)
    pg.fill('[data-test=zoek-veld]','karin'); pg.wait_for_timeout(400)
    pg.locator('[data-test=zoek-hit-tp]').click(); pg.wait_for_timeout(700)
    ck("klik op hit -> winkelpagina open + overlay dicht", 'Zwolle' in (pg.text_content('h1') or '') and pg.locator('[data-test=zoek-veld]').count()==0)
    uitloggen(pg)

    # ===== PARTNER: geen zoekknop, geen Trajecten =====
    pg.evaluate("""window.__DB.tappunten=[window.__DB.tappunten[0]];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    ck("partner: geen zoekknop en geen Trajecten-link", pg.locator('[data-test=zoek-knop]').count()==0 and pg.locator('nav >> text=Trajecten').count()==0)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
