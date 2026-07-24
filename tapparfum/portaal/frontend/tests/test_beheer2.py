from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1

INIT=open("/tmp/claude-0/-home-user-memeradar/b0dc4ae2-3376-5404-9da1-5b0364a4f411/scratchpad/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]

def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x')
    pg.click('button[type=submit]'); pg.wait_for_timeout(600)
def uitloggen(pg):
    pg.click('button:has-text("Uitloggen")'); pg.wait_for_timeout(400)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context(accept_downloads=True).new_page()
    errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT)
    pg.goto(URL); pg.wait_for_timeout(500)

    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:null,
      data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:2400,contact:'Anja',tel:'0612345678',
            logboek:[{id:'l1',at:'2026-07-01',type:'bezoek',txt:'test'}],flesLog:[{at:'2026-07-01',n:2,ti:1}],verkopen:{}}}];
      window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',email:'m@tp.nl',auth_user_id:'u-am'}];
      window.__DB.beheerlog=[{id:'bl1',at:'2026-07-22T10:00:00Z',wie:'k@tp.nl',txt:'Testactie eerder'}];
      window.__MOCK.signin={data:{user:{id:'u-staff',email:'kantoor@tp.nl',app_metadata:{role:'staff'}}},error:null};""")
    login(pg,"kantoor@tp.nl")
    pg.click('nav >> text=Beheer'); pg.wait_for_timeout(500)

    # tabs
    ck("6 tabbladen zichtbaar", pg.locator('.tabs button').count()==6)
    ck("Mensen-tab is standaard actief", pg.locator('[data-test=am-naam]').count()==1)

    # winkel blokkeren via Winkels-tab
    pg.click('[data-test=tab-winkels]'); pg.wait_for_timeout(300)
    ck("Winkels-tab: blokkeer-knop aanwezig", pg.locator('[data-test=winkel-blok]').count()==1)
    pg.click('[data-test=winkel-blok]'); pg.wait_for_timeout(500)
    upd=pg.evaluate("window.__UPDATES")
    ck("blokkeren -> update geblokkeerd=true + audit-insert",
       any(u[0]=='tappunten' and u[1].get('geblokkeerd')==True for u in upd)
       and pg.evaluate("window.__INSERTS.some(i=>i[0]==='beheerlog'&&i[1].txt.indexOf('Geblokkeerd')>=0)"))
    ck("badge 'geblokkeerd' verschijnt", pg.locator('[data-test=winkel-blok-badge]').count()==1)

    # AVG: export + anonimiseren (twee-staps)
    pg.click('[data-test=tab-avg]'); pg.wait_for_timeout(300)
    ck("AVG-tab: export + wis-knoppen", pg.locator('[data-test=avg-export]').count()==1 and pg.locator('[data-test=avg-anon]').count()==1)
    with pg.expect_download() as dl:
        pg.click('[data-test=avg-export]')
    ck("AVG-export downloadt JSON", dl.value.suggested_filename.startswith('AVG_export_'))
    pg.click('[data-test=avg-anon]'); pg.wait_for_timeout(200)
    ck("anonimiseren vraagt bevestiging ('Zeker?')", 'Zeker' in (pg.text_content('[data-test=avg-anon]') or ''))
    pg.click('[data-test=avg-anon]'); pg.wait_for_timeout(600)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("anonimiseren wist v71-velden (naam/contact/log/flesLog leeg, omzet 0)",
       d.get('name')=='Verwijderd tappunt' and d.get('contact')=='' and d.get('logboek')==[] and d.get('flesLog')==[] and d.get('jaaromzet')==0)
    ck("anonimiseren blokkeert de winkel", pg.evaluate("window.__UPDATES.some(u=>u[0]==='tappunten'&&u[1].geblokkeerd===true)"))

    # back-up export
    with pg.expect_download() as dl2:
        pg.click('[data-test=backup-export]')
    ck("back-up downloadt JSON", dl2.value.suggested_filename.startswith('TapParfum_backup_'))

    # modules: kassa uitzetten
    pg.click('[data-test=tab-instellingen]'); pg.wait_for_timeout(300)
    pg.uncheck('[data-test=mod-kassa]')
    pg.click('[data-test=inst-opslaan]'); pg.wait_for_timeout(500)
    ck("modules opgeslagen met kassa=false", pg.evaluate("window.__UPSERTS.some(u=>u[0]==='central'&&u[1].ns==='modules'&&u[1].data.kassa===false)"))

    # audit-tab toont regels
    pg.click('[data-test=tab-audit]'); pg.wait_for_timeout(400)
    ck("audit-log toont eerdere actie", pg.locator('[data-test=audit-rij]').count()>=1)

    # kassa verborgen op winkelpagina nu module uit staat
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(400)
    pg.click('[data-test=tappunt-rij]'); pg.wait_for_timeout(600)
    ck("kassa-module uit -> kassablok verborgen", pg.locator('[data-test=kassa-maat]').count()==0)
    ck("flessenteller blijft gewoon zichtbaar", pg.locator('[data-test=fles-registreer]').count()==1)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
