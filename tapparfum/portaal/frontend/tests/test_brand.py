from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(800)
def zetkleur(pg,sel,val):
    pg.eval_on_selector(sel, "(el,v)=>{el.value=v;el.dispatchEvent(new Event('input',{bubbles:true}))}", val)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:null,data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:5000}}];
      window.__MOCK.signin={data:{user:{id:'u-staff',email:'k@tp.nl',app_metadata:{role:'staff'}}},error:null};""")
    login(pg,"k@tp.nl")

    # standaard-logo
    ck("standaard-logo TAPPARFUM", (pg.text_content('.logo b') or '').strip()=='TAPPARFUM')

    pg.click('nav >> text=Beheer'); pg.wait_for_timeout(400)
    pg.click('[data-test=tab-instellingen]'); pg.wait_for_timeout(300)
    ck("huisstijl-velden aanwezig", pg.locator('[data-test=brand-logo]').count()==1 and pg.locator('[data-test=brand-coral]').count()==1)

    pg.fill('[data-test=brand-logo]','MerkX')
    zetkleur(pg,'[data-test=brand-coral]','#123456')
    pg.click('[data-test=inst-opslaan]'); pg.wait_for_timeout(500)

    up=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='central' && u[1]['ns']==='brand').slice(-1)[0][1]['data']")
    ck("brand opgeslagen: logoTekst MerkX", up.get('logoTekst')=='MerkX')
    ck("brand opgeslagen: coral #123456", str(up.get('coral')).lower()=='#123456')

    # live toegepast: CSS-variabele + logo bijgewerkt
    coralvar=pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--coral').trim()")
    ck("--coral live toegepast", coralvar.lower()=='#123456')
    ck("logotekst live bijgewerkt naar MERKX", (pg.text_content('.logo b') or '').strip()=='MERKX')

    # reset zet velden terug naar standaard
    pg.click('[data-test=brand-reset]'); pg.wait_for_timeout(200)
    ck("reset: logoveld leeg", (pg.input_value('[data-test=brand-logo]') or '')=='')
    ck("reset: coral terug naar #ee644d", pg.input_value('[data-test=brand-coral]').lower()=='#ee644d')

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
