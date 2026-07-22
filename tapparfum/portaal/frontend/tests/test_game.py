from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("/tmp/claude-0/-home-user-memeradar/b0dc4ae2-3376-5404-9da1-5b0364a4f411/scratchpad/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x')
    pg.click('button[type=submit]'); pg.wait_for_timeout(700)
def uitloggen(pg):
    pg.click('button:has-text("Uitloggen")'); pg.wait_for_timeout(400)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(500)

    # ===== KANTOOR: game instellen =====
    pg.evaluate("""window.__DB.central=[];window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[
        {snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
         data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:12000,vorigJaar:6000,liveDate:'2026-01-01',
               bp:{prijzen:true,presentatie:true,zichtbaar:true,home:true},actieDeelname:{a0:{done:true,res:{werkte:'ja'}}}}},
        {snelstart:'kl-2',name:'Deventer',email:null,geblokkeerd:false,am_id:'am-1',
         data:{snelstart:'kl-2',name:'Deventer',jaaromzet:3000,vorigJaar:0,liveDate:'2026-01-01',bp:{prijzen:true}}}];
      window.__MOCK.signin={data:{user:{id:'u-staff',email:'kantoor@tp.nl',app_metadata:{role:'staff'}}},error:null};""")
    login(pg,"kantoor@tp.nl")
    pg.click('nav >> text=Game'); pg.wait_for_timeout(500)
    ck("game staat uit -> melding", pg.locator('[data-test=game-uit]').count()==1)
    pg.check('[data-test=game-actief]')
    pg.fill('[data-test=game-titel]','Zomer Sales Game 2026')
    pg.fill('[data-test=game-minp]','5')
    pg.click('[data-test=game-opslaan]'); pg.wait_for_timeout(500)
    ups=pg.evaluate("window.__UPSERTS")
    ck("opslaan -> central 'salesgame' actief", any(u[0]=='central' and u[1]['ns']=='salesgame' and u[1]['data']['actief']==True for u in ups))
    pg.wait_for_timeout(300)
    ck("game-hero verschijnt", pg.locator('[data-test=game-hero]').count()==1 and 'Zomer Sales Game' in (pg.text_content('[data-test=game-hero]') or ''))
    # Zwolle heeft groei (12000/mnd vs 6000/12) en vorigJaar 6000 -> groei-klassement; Deventer geen vorigJaar -> nieuwkomer
    ck("groei-klassement bevat Zwolle", pg.locator('[data-test=klas-groei]').count()>=1 and 'Zwolle' in (pg.text_content('.kaart:has-text(\"Groei-klassement\")') or ''))
    ck("nieuwkomers bevat Deventer", pg.locator('[data-test=klas-nieuw]', has_text='Deventer').count()==1)
    ck("podium toont medailles", pg.locator('[data-test=podium-0]').count()==1)
    uitloggen(pg)

    # ===== PARTNER: eigen stand, geen andere winkels =====
    pg.evaluate("""window.__DB.tappunten=[window.__DB.tappunten[0]];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    pg.click('nav >> text=Game'); pg.wait_for_timeout(500)
    ck("partner ziet eigen game-stand", pg.locator('[data-test=game-mijn]').count()==1)
    ck("partner ziet GEEN volledig klassement (geen andere winkels)", pg.locator('[data-test=klas-groei]').count()==0)
    ck("partner: geen instel-formulier", pg.locator('[data-test=game-opslaan]').count()==0)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
