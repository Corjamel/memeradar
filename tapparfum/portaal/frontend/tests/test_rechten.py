from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(700)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    # 1) Volwaardige beheerder ziet 5 rechten-vinkjes bij een kantoor-regel
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.central=[{ns:'kantoorRechten',data:{'collega@tp.nl':{rol:'kantoor',acties:True if False else true,game:true,producten:true,team:true,analyse:true}}}];
      window.__MOCK.signin={data:{user:{id:'u-staff',email:'baas@tp.nl',app_metadata:{role:'staff'}}},error:null};""".replace("True if False else true","true"))
    login(pg,"baas@tp.nl")
    pg.click('nav >> text=Beheer'); pg.wait_for_timeout(600)
    for k in ['acties','game','producten','team','analyse']:
        ck(f"rechten-vinkje '{k}' aanwezig", pg.locator(f'[data-test="recht-{k}-collega@tp.nl"]').count()==1)
    ck("volwaardige beheerder ziet Game/Team/Analyse in nav", pg.locator('nav >> text=Game').count()==1 and pg.locator('[data-test=nav-team]').count()==1 and pg.locator('nav >> text=Analyse').count()==1)

    # 2) Beperkt kantoor-account (game/team/analyse=false) ziet ze NIET
    pg2=b.new_context().new_page(); pg2.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg2.add_init_script(INIT); pg2.goto(URL); pg2.wait_for_timeout(400)
    pg2.evaluate("""window.__DB.central=[{ns:'kantoorRechten',data:{'beperkt@tp.nl':{rol:'kantoor',acties:true,producten:true,game:false,team:false,analyse:false}}}];
      window.__MOCK.signin={data:{user:{id:'u-staff2',email:'beperkt@tp.nl',app_metadata:{role:'staff'}}},error:null};""")
    login(pg2,"beperkt@tp.nl")
    pg2.wait_for_timeout(400)
    ck("beperkt account: Game verborgen", pg2.locator('nav >> text=Game').count()==0)
    ck("beperkt account: Team verborgen", pg2.locator('[data-test=nav-team]').count()==0)
    ck("beperkt account: Analyse verborgen", pg2.locator('nav >> text=Analyse').count()==0)
    ck("beperkt account: Winkels blijft zichtbaar", pg2.locator('nav >> text=Winkels').count()==1)
    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
