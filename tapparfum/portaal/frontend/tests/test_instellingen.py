from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(600)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    # AM: ziet + bewerkt instellingen
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:12000}}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"m@t.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(400)
    pg.locator('[data-test=tappunt-rij]').first.click(); pg.wait_for_timeout(700)
    ck("AM ziet instellingen-blok", pg.locator('[data-test=instellingen]').count()==1)
    ck("pakket-keuzelijst = 6 pakketten + geen", pg.locator('[data-test=inst-pkg] option').count()==7)
    pg.fill('[data-test=inst-live]','2026-02-01')
    pg.select_option('[data-test=inst-pkg]','2')
    pg.fill('[data-test=inst-notes]','Extra display besproken')
    pg.click('[data-test=inst-opslaan]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("live-datum opgeslagen (voedt projectie/streefdatum)", d.get('liveDate')=='2026-02-01')
    ck("pakket opgeslagen (index 2)", d.get('pkg')==2)
    ck("operationele notities opgeslagen", 'Extra display' in (d.get('notes') or ''))
    ck("bevestiging getoond", 'opgeslagen' in (pg.text_content('[data-test=inst-melding]') or '').lower())
    # Partner: ziet het instellingen-blok NIET
    pg2=b.new_context().new_page(); pg2.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg2.add_init_script(INIT); pg2.goto(URL); pg2.wait_for_timeout(400)
    pg2.evaluate("""window.__DB.tappunten=[{snelstart:'kl-9',name:'Eigen',geblokkeerd:false,am_id:'am-1',auth_user_id:'u-p',data:{snelstart:'kl-9',name:'Eigen'}}];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg2,"w@t.nl")
    pg2.click('nav >> text=Winkels'); pg2.wait_for_timeout(700)  # 1 winkel -> auto detail
    ck("partner ziet GEEN instellingen-blok", pg2.locator('[data-test=instellingen]').count()==0)
    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
