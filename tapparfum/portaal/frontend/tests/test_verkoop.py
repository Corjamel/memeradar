import datetime
from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
VANDAAG=datetime.date.today().isoformat()
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1

# hergebruik de generieke mock uit fase 4
INIT=open("/tmp/claude-0/-home-user-memeradar/b0dc4ae2-3376-5404-9da1-5b0364a4f411/scratchpad/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]

def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x')
    pg.click('button[type=submit]'); pg.wait_for_timeout(600)
def uitloggen(pg):
    pg.click('button:has-text("Uitloggen")'); pg.wait_for_timeout(400)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT)
    pg.goto(URL); pg.wait_for_timeout(500)

    # ===== AM registreert verkoop bij een winkel =====
    pg.evaluate("""window.__DB.tappunten=[
      {snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
       data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:2400,doel:6000,
             flesLog:[{at:'2026-01-05',n:4,ti:1}]}}];
      window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"marian@tp.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(400)
    pg.click('[data-test=tappunt-rij]'); pg.wait_for_timeout(500)

    ck("verkoopblok zichtbaar met bestaande data", pg.locator('[data-test=fles-jaar]').count()==1)
    ck("jaar-totaal telt bestaande log (4)", (pg.text_content('[data-test=fles-jaar]') or '')=='4')
    ck("jaaromzet-veld vooringevuld (2400)", pg.input_value('[data-test=omzet-jaaromzet]')=='2400')

    # 3 flessen vandaag registreren
    pg.fill('[data-test=fles-aantal]','3')
    pg.click('[data-test=fles-registreer]'); pg.wait_for_timeout(500)
    ups=pg.evaluate("window.__UPSERTS")
    fl=[u[1]['data'].get('flesLog') for u in ups if u[0]=='tappunten']
    ok = fl and any(l and len(l)==2 and any(e['at']==VANDAAG and e['n']==3 and e['ti']==1 for e in l) for l in fl)
    ck("registreren -> upsert met v71-compatibele flesLog {at,n,ti}", bool(ok))
    ck("tegel vandaag = 3", (pg.text_content('[data-test=fles-vandaag]') or '')=='3')
    ck("tegel dit jaar = 7 (4 oud + 3 nieuw)", (pg.text_content('[data-test=fles-jaar]') or '')=='7')
    ck("laatste registraties tonen 2 regels", pg.locator('[data-test=fles-regel]').count()==2)

    # jaaromzet + doel bijwerken
    pg.fill('[data-test=omzet-jaaromzet]','2500')
    pg.fill('[data-test=omzet-doel]','8000')
    pg.click('[data-test=omzet-opslaan]'); pg.wait_for_timeout(500)
    ups=pg.evaluate("window.__UPSERTS")
    ok = any(u[0]=='tappunten' and u[1]['data'].get('jaaromzet')==2500 and u[1]['data'].get('doel')==8000 for u in ups)
    ck("omzet opslaan -> upsert jaaromzet=2500, doel=8000", ok)
    ck("beschermde velden ook hier NIET meegestuurd", all(not ({'geblokkeerd','am_id','auth_user_id'} & set(u[1].keys())) for u in ups if u[0]=='tappunten'))

    # regel verwijderen
    pg.locator('[data-test=fles-verwijder]').first.click(); pg.wait_for_timeout(200)
    pg.locator('[data-test=fles-verwijder]').first.click(); pg.wait_for_timeout(500)  # 2e klik = bevestigen
    ck("na verwijderen 1 regel over", pg.locator('[data-test=fles-regel]').count()==1)
    uitloggen(pg)

    # ===== Partner registreert op zijn eigen winkel =====
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
      data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:2400,flesLog:[]}}];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(700)
    ck("partner ziet verkoopblok op eigen winkel", pg.locator('[data-test=fles-registreer]').count()==1)
    pg.click('[data-test=fles-registreer]'); pg.wait_for_timeout(500)
    ck("partner registreert 1 fles", (pg.text_content('[data-test=fles-vandaag]') or '')=='1')

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
