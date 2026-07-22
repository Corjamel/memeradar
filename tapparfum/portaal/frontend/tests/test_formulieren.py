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
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle'}}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"marian@tp.nl")
    pg.click('nav >> text=Formulieren'); pg.wait_for_timeout(500)
    ck("7 formulieren in de keuzelijst", pg.locator('[data-test=form-kies] option').count()==8)  # incl. placeholder
    pg.select_option('[data-test=form-kies]','vw_tappunt'); pg.wait_for_timeout(400)
    ck("tappunt-voorwaarden: 12 ja/nee-vragen", pg.locator('[data-test^=fy-vt]').count()>=12)
    ck("voortgangsteller 0/12", '0/12' in (pg.text_content('[data-test=form-voortgang]') or ''))
    # beantwoord een paar vragen + vul velden
    pg.fill('[data-test=fv-vtbedrijf]','Parfums Zwolle BV / 12345678')
    pg.click('[data-test=fy-vt1-ja]'); pg.wait_for_timeout(100)
    pg.click('[data-test=fy-vt2-ja]'); pg.wait_for_timeout(100)
    pg.click('[data-test=fy-vt3-nee]'); pg.wait_for_timeout(200)
    ck("teller naar 3/12", '3/12' in (pg.text_content('[data-test=form-voortgang]') or ''))
    pg.click('[data-test=form-opslaan]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    f=d.get('forms',{}).get('vw_tappunt',{})
    ck("opgeslagen in t.forms.vw_tappunt (v71-veld)", f.get('vt1')=='ja' and f.get('vt3')=='nee' and 'Zwolle BV' in f.get('vtbedrijf',''))
    ck("bevestiging getoond", 'opgeslagen' in (pg.text_content('[data-test=form-melding]') or '').lower())
    # demo-formulier heeft keuzevragen (opts)
    pg.select_option('[data-test=form-kies]','demo'); pg.wait_for_timeout(400)
    pg.click('[data-test=fo-d4-Goed]'); pg.wait_for_timeout(100)
    pg.click('[data-test=fo-d7-Positief]'); pg.wait_for_timeout(200)
    pg.click('[data-test=form-opslaan]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("keuzevragen opgeslagen (d4=Goed, d7=Positief)", d['forms']['demo'].get('d4')=='Goed' and d['forms']['demo'].get('d7')=='Positief')
    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
