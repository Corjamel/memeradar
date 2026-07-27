from playwright.sync_api import sync_playwright
from datetime import date
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1

INIT=open("/tmp/claude-0/-home-user-memeradar/b0dc4ae2-3376-5404-9da1-5b0364a4f411/scratchpad/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
VANDAAG=date.today().isoformat()

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

    # ===== PARTNER: cursussen + les afvinken + beloning via training =====
    # Winkel voldoet al aan de home-eisen (5000 omzet, geen serieus vorig jaar) —
    # alleen de Tapbar-cursus ontbreekt nog; de 5e les vinkt de beloning vrij.
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
        data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:6000,vorigJaar:0,setup:{skipped:true},
              academy:{tapbar:{0:true,1:true,2:true,3:true}}}}];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    pg.click('nav >> text=Academy'); pg.wait_for_timeout(700)

    ck("6 cursuskaarten (v71 COURSES)", pg.locator('[data-test=cursus]').count()==6)
    ck("teller: 4/28 lessen (14%)", '4/28' in (pg.text_content('[data-test=academy-stand]') or '') and '14%' in (pg.text_content('[data-test=academy-pct]') or ''))
    ck("tapbar-kaart: 4/5 lessen", '4/5' in (pg.text_content('[data-test=cursus-stand-tapbar]') or ''))
    pg.click('[data-test=cursus-open-tapbar]'); pg.wait_for_timeout(200)
    ck("5 lessen zichtbaar, exacte v71-titel les 1", pg.locator('[data-test^=les-tapbar-]').count()==5 and 'De Tapbar opzetten' in (pg.text_content('[data-test=cursus]:has-text("Tapbar")') or ''))
    # Lesinhoud: titel opent echte lesstof (uitleg + kernpunten + praktijktip)
    pg.click('[data-test=les-open-tapbar-0]'); pg.wait_for_timeout(200)
    stof=pg.text_content('[data-test=les-stof-tapbar-0]') or ''
    ck("lesstof open: uitleg + tip aanwezig", 'podium' in stof and '💡' in stof)
    ck("elke tapbar-les heeft een lesstof-knop", pg.locator('[data-test^=les-open-tapbar-]').count()==5)
    ck("afgeronde les heeft geen 'Les afronden'-knop", pg.locator('[data-test=les-klaar-tapbar-0]').count()==0)
    # De open les (4) afronden via de knop in de lesstof
    pg.click('[data-test=les-open-tapbar-4]'); pg.wait_for_timeout(200)
    pg.click('[data-test=les-klaar-tapbar-4]'); pg.wait_for_timeout(600)
    ck("'Les afronden' vinkt de les af", pg.locator('[data-test=les-tapbar-4]').is_checked())
    pg.check('[data-test=les-tapbar-4]'); pg.wait_for_timeout(300)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("les afvinken -> t.academy.tapbar[4]=true (v71-veld)", d['academy']['tapbar']['4']==True or d['academy']['tapbar'].get(4)==True)
    ck("training compleet -> homegeuren-beloning uitgekeerd", d.get('beloond',{}).get('home')==VANDAAG)
    ck("vieringsbanner met de beloning", 'homegeuren' in (pg.text_content('[data-test=academy-viering]') or ''))
    ck("tapbar-kaart nu Voltooid", 'Voltooid' in (pg.text_content('[data-test=cursus-stand-tapbar]') or ''))
    uitloggen(pg)

    # ===== PARTNER 2: certificaat bij 100% =====
    pg.evaluate("""var vol={};
      [['onboarding',6],['geurnoten',4],['funnel',5],['aanspreken',5],['geurnotenboek',3],['tapbar',5]].forEach(function(c){
        vol[c[0]]={}; for(var i=0;i<c[1];i++) vol[c[0]][i]=true; });
      window.__DB.tappunten[0].data.academy=vol;
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    pg.click('nav >> text=Academy'); pg.wait_for_timeout(700)
    ck("100% -> 28/28 + certificaat-kaart", '28/28' in (pg.text_content('[data-test=academy-stand]') or '') and pg.locator('[data-test=academy-cert]').count()==1)
    uitloggen(pg)

    # ===== AM: voortgang per winkel via de winkel-kiezer =====
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[
        {snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
         data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:6000,academy:{onboarding:{0:true,1:true}}}},
        {snelstart:'kl-2',name:'Deventer',email:null,geblokkeerd:false,am_id:'am-1',
         data:{snelstart:'kl-2',name:'Deventer',jaaromzet:3000}}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"marian@tp.nl")
    pg.click('nav >> text=Academy'); pg.wait_for_timeout(700)
    ck("AM ziet winkel-kiezer + voortgang Zwolle (2/28)", pg.locator('[data-test=academy-winkel]').count()==1 and '2/28' in (pg.text_content('[data-test=academy-stand]') or ''))
    pg.select_option('[data-test=academy-winkel]','kl-2'); pg.wait_for_timeout(400)
    ck("wissel naar Deventer -> 0/28", '0/28' in (pg.text_content('[data-test=academy-stand]') or ''))
    pg.click('[data-test=cursus-open-onboarding]'); pg.wait_for_timeout(200)
    pg.check('[data-test=les-onboarding-0]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("AM vinkt les af voor Deventer (trainingsdag)", d['name']=='Deventer' and (d['academy']['onboarding'].get('0')==True or d['academy']['onboarding'].get(0)==True))

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
