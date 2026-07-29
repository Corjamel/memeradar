from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(800)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    # 1) editor slaat regels op
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:null,data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:4000}}];
      window.__MOCK.signin={data:{user:{id:'u-staff',email:'k@tp.nl',app_metadata:{role:'staff'}}},error:null};""")
    login(pg,"k@tp.nl")
    pg.click('nav >> text=Beheer'); pg.wait_for_timeout(400)
    pg.click('[data-test=tab-regels]'); pg.wait_for_timeout(300)
    pg.fill('[data-test=regel-drempel-C]','5000')
    # weging (v71: 5 componenten) moet samen 100 zijn: groei 35->40, uitv 20->15
    pg.fill('[data-test=regel-weging-groei]','40'); pg.fill('[data-test=regel-weging-uitv]','15')
    pg.click('[data-test=regels-opslaan]'); pg.wait_for_timeout(500)
    up=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='central' && u[1]['ns']==='regels').slice(-1)[0][1]['data']")
    ck("editor slaat drempels op (C=5000)", up['drempels'][1]==5000)
    ck("editor slaat weging op (groei=40)", up['weging']['groei']==40)

    # 2) verhoogde C-drempel neemt effect bij login: winkel €4000 = niveau D i.p.v. C
    pg2=b.new_context().new_page(); pg2.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg2.add_init_script(INIT); pg2.goto(URL); pg2.wait_for_timeout(400)
    pg2.evaluate("""window.__DB.central=[{ns:'regels',data:{drempels:[0,5000,10000,20000,50000,100000],weging:{groei:40,activatie:25,retentie:20,data:20}}}];
      window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:4000}}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg2,"m@t.nl")
    pg2.click('nav >> text=Beloningen'); pg2.wait_for_timeout(500)
    niveau=(pg2.text_content('[data-test=winkel-niveau] .niveau') or '').strip()
    ck("verhoogde drempel actief: €4000 -> niveau D (niet C)", niveau=='D')
    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
