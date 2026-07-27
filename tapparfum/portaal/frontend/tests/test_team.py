from playwright.sync_api import sync_playwright
from datetime import date, timedelta
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("/tmp/claude-0/-home-user-memeradar/b0dc4ae2-3376-5404-9da1-5b0364a4f411/scratchpad/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
VANDAAG=date.today().isoformat()
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x')
    pg.click('button[type=submit]'); pg.wait_for_timeout(700)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(500)
    pg.evaluate(f"""window.__DB.accountmanagers=[{{id:'am-1',naam:'Marian',auth_user_id:'u-am'}},{{id:'am-2',naam:'Peter',auth_user_id:'u-p2'}}];
      window.__DB.tappunten=[
        {{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
         data:{{snelstart:'kl-1',name:'Zwolle',jaaromzet:22000,vorigJaar:12000,setup:{{skipped:true}},
               logboek:[{{id:'l1',at:'{VANDAAG}',type:'bezoek',txt:'Tapbar verplaatst',nextDate:'',nextDone:false}}],
               bestellingen:[{{id:'b1',at:'{VANDAAG}',ref:'F1',totaal:900,omschrijving:'',bron:'handmatig'}}]}}}},
        {{snelstart:'kl-2',name:'Deventer',email:null,geblokkeerd:false,am_id:'am-1',
         data:{{snelstart:'kl-2',name:'Deventer',jaaromzet:0,vorigJaar:5000,setup:{{skipped:true}}}}}},
        {{snelstart:'kl-3',name:'Kampen',email:null,geblokkeerd:false,am_id:'am-2',
         data:{{snelstart:'kl-3',name:'Kampen',jaaromzet:8000,vorigJaar:6000,setup:{{skipped:true}}}}}}];
      window.__MOCK.signin={{data:{{user:{{id:'u-staff',email:'kantoor@tp.nl',app_metadata:{{role:'staff'}}}}}},error:null}};""")
    login(pg,"kantoor@tp.nl")
    pg.click('[data-test=nav-team]'); pg.wait_for_timeout(600)
    ck("2 AM-blokken (Marian + Peter)", pg.locator('[data-test=team-am]').count()==2)
    ck("AM-score zichtbaar", pg.locator('[data-test=am-score]').count()>=1)
    ck("Marian-blok toont stagneert-badge (Deventer)", 'stagneert' in (pg.locator('[data-test=team-am]', has_text='Marian').text_content() or '').lower())
    # drilldown openen
    pg.locator('[data-test=team-am]', has_text='Marian').locator('.amkop').click(); pg.wait_for_timeout(300)
    ck("drilldown: 2 winkels van Marian", pg.locator('[data-test=team-winkel]').count()>=2)
    # opdracht sturen over Deventer
    pg.click('[data-test=opdracht-kl-2]'); pg.wait_for_timeout(200)
    pg.fill('[data-test=opdracht-txt]','Bel Deventer over de stilstand')
    pg.click('[data-test=opdracht-verstuur]'); pg.wait_for_timeout(500)
    ins=pg.evaluate("window.__INSERTS.filter(i=>i[0]==='berichten').slice(-1)[0][1]")
    ck("opdracht -> bericht aan am-1 type taak met winkelnaam", ins['aan_am']=='am-1' and ins['type']=='taak' and 'Deventer' in ins['txt'])
    ck("bevestiging getoond", 'verstuurd' in (pg.text_content('[data-test=team-melding]') or ''))
    # activiteitenfeed
    ck("activiteitenfeed toont logboek + bestelling", pg.locator('[data-test=feed-rij]').count()>=2 and 'Tapbar' in (pg.text_content('.kaart:has-text(\"Recente activiteit\")') or ''))
    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
