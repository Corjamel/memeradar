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
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:null,data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:4000}}];
      window.__MOCK.signin={data:{user:{id:'u-staff',email:'k@tp.nl',app_metadata:{role:'staff'}}},error:null};""")
    login(pg,"k@tp.nl")

    # ToastHost is altijd gemount, leeg bij start
    ck("geen toast bij start", pg.locator('[data-test=toast]').count()==0)

    # Beheer -> Regels opslaan -> toast verschijnt
    pg.click('nav >> text=Beheer'); pg.wait_for_timeout(400)
    pg.click('[data-test=tab-regels]'); pg.wait_for_timeout(300)
    pg.fill('[data-test=regel-drempel-C]','5000')
    pg.click('[data-test=regels-opslaan]'); pg.wait_for_timeout(300)
    ck("toast na regels opslaan", pg.locator('[data-test=toast]').count()>=1)
    tx=(pg.text_content('[data-test=toast]') or '')
    ck("toast bevat bevestigingstekst", len(tx.strip())>0)

    # Toast verdwijnt vanzelf (levensduur ~3.2s)
    pg.wait_for_timeout(3800)
    ck("toast verdwijnt vanzelf", pg.locator('[data-test=toast]').count()==0)

    # Klik-sluiten: nieuwe toast, wegklikken
    pg.fill('[data-test=regel-drempel-C]','5500')
    pg.click('[data-test=regels-opslaan]'); pg.wait_for_timeout(300)
    if pg.locator('[data-test=toast]').count()>=1:
        pg.locator('[data-test=toast]').first.click(); pg.wait_for_timeout(400)
    ck("toast sluit bij klik", pg.locator('[data-test=toast]').count()==0)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
