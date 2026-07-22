from playwright.sync_api import sync_playwright
from datetime import date, timedelta
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1

INIT=open("/tmp/claude-0/-home-user-memeradar/b0dc4ae2-3376-5404-9da1-5b0364a4f411/scratchpad/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
VANDAAG=date.today().isoformat()
GISTER=(date.today()-timedelta(days=1)).isoformat()
D40=(date.today()-timedelta(days=40)).isoformat()

def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x')
    pg.click('button[type=submit]'); pg.wait_for_timeout(700)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT)
    pg.goto(URL); pg.wait_for_timeout(500)

    # break-even fase: 40 dgn live, plan 239 flessen/84 dgn -> verwacht ~114; 50 verkocht -> achter
    pg.evaluate(f"""window.__DB.accountmanagers=[{{id:'am-1',naam:'Marian',auth_user_id:'u-am'}}];
      window.__DB.tappunten=[{{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
        data:{{snelstart:'kl-1',name:'Zwolle',jaaromzet:2000,doel:5000,liveDate:'{D40}',dagType:3,
              be:{{inv:3950,rev:16.53,perWk:20,days:84,bottles:239}},
              flesLog:[{{at:'{D40}',n:50,ti:1}}]}}}}];
      window.__MOCK.signin={{data:{{user:{{id:'u-am',app_metadata:{{}}}}}},error:null}};""")
    login(pg,"marian@tp.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(400)
    pg.locator('[data-test=tappunt-rij]').first.click(); pg.wait_for_timeout(800)

    ck("schema-strip: achter op break-evenplan", pg.locator('[data-test=schema-strip]').count()==1 and 'achter' in (pg.text_content('[data-test=schema-strip]') or ''))
    ck("doelbalk toont 50 / 239 flessen tot break-even", '50' in (pg.text_content('[data-test=doelbalk]') or '') and '239' in (pg.text_content('[data-test=doelbalk]') or '') and 'break-even' in (pg.text_content('[data-test=doelbalk]') or ''))
    ck("week-invulrij: 7 dagvakjes", pg.locator('[data-test^=week-]').count()==7)
    ck("type-keuze: 12 SALE_TYPES", pg.locator('[data-test=fles-type] option').count()==12)

    # week-invulrij: vandaag op 4 zetten -> flesLog krijgt regel met dagType 3
    pg.fill(f'[data-test=week-{VANDAAG}]','4'); pg.locator(f'[data-test=week-{VANDAAG}]').blur(); pg.wait_for_timeout(600)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    vandaag_regels=[e for e in d['flesLog'] if e['at']==VANDAAG]
    ck("dag op 4 -> flesLog-regel(s) vandaag = 4 met ti=dagType(3)", sum(e['n'] for e in vandaag_regels)==4 and all(e['ti']==3 for e in vandaag_regels))
    pg.evaluate("window.__DB.tappunten[0].data.flesLog="+str(d['flesLog']).replace("'",'"'))

    # dag verlagen naar 1 -> regels teruggedraaid
    pg.fill(f'[data-test=week-{VANDAAG}]','1'); pg.locator(f'[data-test=week-{VANDAAG}]').blur(); pg.wait_for_timeout(600)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("dag verlaagd naar 1 -> teruggedraaid", sum(e['n'] for e in d['flesLog'] if e['at']==VANDAAG)==1)
    pg.evaluate("window.__DB.tappunten[0].data.flesLog="+str(d['flesLog']).replace("'",'"'))

    # registreer met specifiek type (index 6 = 30ml Exclusive + flesje)
    pg.select_option('[data-test=fles-type]','6')
    pg.fill('[data-test=fles-aantal]','2')
    pg.click('[data-test=fles-registreer]'); pg.wait_for_timeout(600)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("registreer met type 6 -> flesLog-regel ti=6 n=2", any(e['ti']==6 and e['n']==2 for e in d['flesLog']))
    ck("loglijst toont het gekozen type-label", 'Exclusive' in (pg.text_content('[data-test=fles-regel]') or ''))

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
