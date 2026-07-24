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
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:5000}},
        {snelstart:'kl-2',name:'Emmen',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-2',name:'Emmen',jaaromzet:0}}];
      window.__MOCK.signin={data:{user:{id:'u-am',email:'m@tp.nl',app_metadata:{}}},error:null};""")
    login(pg,"m@tp.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(600)
    ck("AM ziet '+ Nieuwe winkel'-knop", pg.locator('[data-test=winkel-nieuw-knop]').count()==1)
    pg.click('[data-test=winkel-nieuw-knop]'); pg.wait_for_timeout(200)
    ck("formulier verschijnt", pg.locator('[data-test=winkel-nieuw-vorm]').count()==1)
    pg.fill('[data-test=nieuw-naam]','Parfumerie Kampen'); pg.fill('[data-test=nieuw-snelstart]','kl-30'); pg.fill('[data-test=nieuw-plaats]','Kampen')
    pg.click('[data-test=nieuw-opslaan]'); pg.wait_for_timeout(600)
    up=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]")
    ck("winkel weggeschreven (naam+code)", up['name']=='Parfumerie Kampen' and up['snelstart']=='kl-30')
    ck("am_id NIET meegestuurd (guard doet dat server-side)", 'am_id' not in up)
    ck("data: plaats + setup overgeslagen", up['data'].get('plaats')=='Kampen' and up['data'].get('setup',{}).get('skipped')==True)
    ck("bevestigings-toast verschenen", pg.locator('[data-test=toast]').count()>=1)
    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
