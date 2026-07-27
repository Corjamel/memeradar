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
    pg.click('[data-test=nav-geuren]'); pg.wait_for_timeout(500)
    ck("14 geuren in de bibliotheek", pg.locator('[data-test=geur-kaart]').count()==14)
    ck("6 lijnfilters (Alle/Dames/Heren/Unisex/Exclusive/Niventi)", all(pg.locator(f'[data-test=lijn-{l}]').count()==1 for l in ['Alle','Dames','Heren','Unisex','Exclusive','Niventi']))
    pg.click('[data-test=lijn-Heren]'); pg.wait_for_timeout(300)
    ck("filter Heren -> 4 geuren", pg.locator('[data-test=geur-kaart]').count()==4)
    pg.click('[data-test=lijn-Alle]'); pg.wait_for_timeout(200)
    pg.fill('[data-test=geur-zoek]','saffraan'); pg.wait_for_timeout(300)
    ck("zoek op geurnoot 'saffraan' -> TN056", pg.locator('[data-test=geur-kaart]').count()==1 and 'TN056' in (pg.text_content('[data-test=geur-kaart]') or ''))
    pg.fill('[data-test=geur-zoek]',''); pg.wait_for_timeout(200)
    # refill bestellen -> winkelvraag
    pg.click('[data-test=refill-LA569]'); pg.wait_for_timeout(500)
    ins=pg.evaluate("window.__INSERTS.filter(i=>i[0]==='winkelvragen').slice(-1)[0][1]")
    ck("refill -> winkelvraag met 'Refill besteld: LA569'", 'Refill besteld: LA569' in ins['txt'] and ins['tappunt_snelstart']=='kl-1')
    ck("melding bevestigt refill", 'LA569' in (pg.text_content('[data-test=refill-melding]') or ''))
    ck("merk & materialen: 4 asset-kaarten", pg.locator('[data-test=merk-asset]').count()==4)
    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
