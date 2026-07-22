from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1

INIT=open("/tmp/claude-0/-home-user-memeradar/b0dc4ae2-3376-5404-9da1-5b0364a4f411/scratchpad/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]

def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x')
    pg.click('button[type=submit]'); pg.wait_for_timeout(700)
def uitloggen(pg):
    pg.click('button:has-text("Uitloggen")'); pg.wait_for_timeout(400)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT)
    pg.goto(URL); pg.wait_for_timeout(500)

    # ===== AM vult alle winkelvelden =====
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
        data:{snelstart:'kl-1',name:'Zwolle',contact:'Karin'}}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"marian@tp.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(400)
    pg.click('[data-test=tappunt-rij]'); pg.wait_for_timeout(700)
    ck("gegevens-teller aanwezig (2/13: name+contact)", '2/13' in (pg.text_content('[data-test=geg-teller]') or ''))
    pg.fill('[data-test=geg-postcode]','8011 AB')
    pg.select_option('[data-test=geg-type]','Kapper')
    pg.fill('[data-test=geg-jarig]','1985-06-12')
    pg.click('button:has-text("Opslaan")'); pg.wait_for_timeout(600)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("nieuwe velden opgeslagen (postcode/type/jarig)", d.get('postcode')=='8011 AB' and d.get('type')=='Kapper' and d.get('jarig')=='1985-06-12')
    ck("teller nu 5/13", '5/13' in (pg.text_content('[data-test=geg-teller]') or ''))
    ck("AM-wijziging schrijft GEEN partner-logregel", not any('Partner heeft' in (l.get('txt') or '') for l in d.get('logboek',[])))
    uitloggen(pg)

    # ===== Partner wijzigt -> 📇-logregel =====
    pg.evaluate("""window.__DB.tappunten[0].data.postcode='8011 AB';window.__DB.tappunten[0].data.type='Kapper';
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(800)
    pg.fill('[data-test=geg-name]','Zwolle Centrum')
    pg.click('button:has-text("Opslaan")'); pg.wait_for_timeout(600)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("partner-wijziging -> 📇 logboek-notitie voor de AM", any('Partner heeft de winkelgegevens' in (l.get('txt') or '') for l in d.get('logboek',[])))
    ck("naam bijgewerkt", d.get('name')=='Zwolle Centrum')

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
