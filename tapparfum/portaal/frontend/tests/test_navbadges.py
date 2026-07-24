from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(700)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle'}}];
      window.__DB.winkelvragen=[{id:'w1',tappunt_snelstart:'kl-1',type:'vraag',txt:'hoi',status:'open'},{id:'w2',tappunt_snelstart:'kl-1',type:'probleem',txt:'x',status:'open'},{id:'w3',tappunt_snelstart:'kl-1',type:'vraag',txt:'y',status:'beantwoord'}];
      window.__DB.taken=[{id:'t1',titel:'Bel',am_id:'am-1',klaar:false},{id:'t2',titel:'Mail',am_id:'am-1',klaar:true}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"m@t.nl")
    ck("berichten-badge = 2 open vragen", pg.locator('[data-test=bdg-berichten]').count()==1 and (pg.text_content('[data-test=bdg-berichten]') or '').strip()=='2')
    ck("taken-badge = 1 open taak", pg.locator('[data-test=bdg-taken]').count()==1 and (pg.text_content('[data-test=bdg-taken]') or '').strip()=='1')
    pg.click('nav >> text=Berichten'); pg.wait_for_timeout(400)
    ck("nav-klik Berichten werkt met badge erin", '/berichten' in pg.url)
    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
