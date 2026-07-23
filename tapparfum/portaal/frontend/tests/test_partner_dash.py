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
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
        data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:12000,vorigJaar:6000,setup:{skipped:true},doel:20000,
              goal:{doel:20000,flJaar:260,flWeek:5},
              bp:{prijzen:true,presentatie:true,zichtbaar:true,home:true},
              flesLog:[{at:'2026-01-05',n:80,ti:1}]}}];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")   # partner blijft op Start (dashboard)
    pg.wait_for_timeout(500)
    ck("stats-KPI-rij aanwezig", pg.locator('[data-test=pstats]').count()==1)
    ck("basispunten-tegel toont /70", '/70' in (pg.text_content('[data-test=pstats]') or ''))
    ck("trofeeen-strip: 5 spaarcadeaus", pg.locator('[data-test=trofeeen] .trof').count()==5)
    ck("spotlight geur van de week (TN056)", pg.locator('[data-test=spotlight]').count()==1 and 'TN056' in (pg.text_content('[data-test=spotlight]') or ''))
    ck("USP-blok: 4 kaarten", pg.locator('[data-test=usps] .usp').count()==4)
    # berichtenkaart met 4 knoppen (vraag/bezoek/probleem/retour)
    ck("berichtenkaart met 4 soorten", pg.locator('[data-test=berichtkaart]').count()==1 and pg.locator('[data-test^=ber-soort-]').count()==4)
    # bezoek aanvragen (datum)
    pg.click('[data-test=ber-soort-bezoek]'); pg.wait_for_timeout(200)
    pg.fill('[data-test=ber-datum]','2026-08-15')
    pg.click('[data-test=ber-verstuur]'); pg.wait_for_timeout(500)
    ins=pg.evaluate("window.__INSERTS.filter(i=>i[0]==='winkelvragen').slice(-1)[0][1]")
    ck("bezoek -> winkelvraag type vraag met datum", ins['type']=='vraag' and 'Bezoek aangevraagd' in ins['txt'] and '2026-08-15' in ins['txt'])
    ck("bevestiging getoond", 'antwoord terug' in (pg.text_content('[data-test=bezoek-melding]') or ''))
    # probleem melden (type probleem)
    pg.click('[data-test=ber-soort-probleem]'); pg.wait_for_timeout(200)
    pg.fill('[data-test=ber-txt]','Tapbar lekt')
    pg.click('[data-test=ber-verstuur]'); pg.wait_for_timeout(500)
    ins=pg.evaluate("window.__INSERTS.filter(i=>i[0]==='winkelvragen').slice(-1)[0][1]")
    ck("probleem -> winkelvraag type probleem", ins['type']=='probleem' and 'Tapbar lekt' in ins['txt'])
    # deze-week-ring + projectie aanwezig (winkel heeft goal.flWeek + omzet)
    ck("deze-week-kaart aanwezig", pg.locator('[data-test=weekkaart]').count()==1)
    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
