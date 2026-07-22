from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("/tmp/claude-0/-home-user-memeradar/b0dc4ae2-3376-5404-9da1-5b0364a4f411/scratchpad/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x')
    pg.click('button[type=submit]'); pg.wait_for_timeout(700)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(500)
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle'}}];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    # Kennisbank (alle rollen)
    pg.click('nav >> text=Kennis'); pg.wait_for_timeout(500)
    ck("kennisbank: 7 blokken", pg.locator('[data-test=kennis-blok]').count()==7)
    ck("eerste blok open met visie-lead", 'portemonnee' in (pg.text_content('.body') or ''))
    pg.locator('[data-test=kennis-blok]').nth(1).locator('.kop').click(); pg.wait_for_timeout(200)
    ck("tweede blok opent USP-lijst", 'Betaalbare luxe' in (pg.text_content('[data-test=kennis-blok]:nth-child(3)') or '') or 'Betaalbare luxe' in (pg.text_content('.body') or ''))
    ck("partner heeft GEEN Proces-link", pg.locator('nav >> text=Proces').count()==0)
    b.close()
    # Proces (AM)
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle'}}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"marian@tp.nl")
    pg.click('nav >> text=Proces'); pg.wait_for_timeout(500)
    ck("proces: 4 verkoopstappen", pg.locator('[data-test=sale-step]').count()==4)
    ck("proces: 6 opstart-fases", pg.locator('[data-test=proces-fase]').count()==6)
    ck("proces: 4 aftersales-stappen (dag 7/30/60/90)", pg.locator('[data-test=aftersales-stap]').count()==4 and 'Dag 90' in (pg.text_content('.cadans') or ''))
    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
