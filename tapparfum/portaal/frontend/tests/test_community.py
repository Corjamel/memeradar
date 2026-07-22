from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x')
    pg.click('button[type=submit]'); pg.wait_for_timeout(700)
SEED="""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
  window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',auth_user_id:'u-p',data:{snelstart:'kl-1',name:'Zwolle'}}];
  window.__DB.community=[
    {id:'c2',am_id:'am-1',author:'TapPunt Utrecht',role:'partner',txt:'Tip: eerst de parfum-quiz, dan 2 matches tappen.',created_at:'2026-07-22T09:00:00Z'},
    {id:'c1',am_id:'am-1',author:'TapParfum HQ',role:'hq',txt:'Niventi-collectie uitgebreid met 4 geuren.',created_at:'2026-07-22T08:00:00Z'}];"""
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    errs=[]
    # ---- Accountmanager: leest + plaatst ----
    pg=b.new_context().new_page(); pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate(SEED+"window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};")
    login(pg,"marian@tp.nl")
    pg.click('nav >> text=Community'); pg.wait_for_timeout(500)
    ck("AM ziet de tijdlijn (2 posts)", pg.locator('[data-test=com-post]').count()==2)
    ck("AM ziet de composer", pg.locator('[data-test=com-tekst]').count()==1)
    ck("HQ-badge zichtbaar", pg.locator('.rol.r-hq').count()==1)
    pg.fill('[data-test=com-tekst]','Complimenten aan Zwolle — mooie groei deze maand!')
    pg.click('[data-test=com-plaats]'); pg.wait_for_timeout(500)
    ins=pg.evaluate("window.__INSERTS.filter(i=>i[0]==='community')")
    ck("plaatsen -> insert met alleen de tekst (guard vult de rest server-side)",
       len(ins)==1 and 'Complimenten aan Zwolle' in ins[0][1]['txt'] and 'am_id' not in ins[0][1] and 'author' not in ins[0][1])
    ck("tijdlijn herladen -> 3 posts", pg.locator('[data-test=com-post]').count()==3)
    ck("bevestiging getoond", 'geplaatst' in (pg.text_content('[data-test=com-melding]') or '').lower())
    ck("AM ziet geen wis-knop (geen moderatie)", pg.locator('[data-test^=com-wis-]').count()==0)

    # ---- Kantoor: modereert (geen composer, wel verwijderen) ----
    pg2=b.new_context().new_page(); pg2.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg2.add_init_script(INIT); pg2.goto(URL); pg2.wait_for_timeout(400)
    pg2.evaluate(SEED+"window.__MOCK.signin={data:{user:{id:'u-staff',email:'kantoor@tp.nl',app_metadata:{role:'staff'}}},error:null};")
    login(pg2,"kantoor@tp.nl")
    pg2.click('nav >> text=Community'); pg2.wait_for_timeout(500)
    ck("kantoor: geen composer (modereert)", pg2.locator('[data-test=com-tekst]').count()==0)
    ck("kantoor: moderatie-notitie zichtbaar", pg2.locator('.mod').count()==1)
    ck("kantoor: wis-knoppen aanwezig", pg2.locator('[data-test^=com-wis-]').count()==2)
    pg2.click('[data-test=com-wis-c2]'); pg2.wait_for_timeout(500)
    dels=pg2.evaluate("window.__DELETES.filter(d=>d[0]==='community')")
    ck("verwijderen -> delete-call op community", len(dels)>=1)
    ck("tijdlijn na verwijderen -> 1 post", pg2.locator('[data-test=com-post]').count()==1)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
