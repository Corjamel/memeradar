import datetime
from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
VANDAAG=datetime.date.today().isoformat()
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
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT)
    pg.goto(URL); pg.wait_for_timeout(500)

    # ===== KASSA (AM op winkelpagina) =====
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
      data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:2400,flesLog:[],verkopen:{}}}];
      window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"marian@tp.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(400)
    pg.click('[data-test=tappunt-rij]'); pg.wait_for_timeout(600)

    ck("kassa toont 4 standaardmaten", pg.locator('[data-test=kassa-maat]').count()==4)
    # 2x 50ml tikken
    pg.click('[data-test=kassa-plus-50ml]'); pg.wait_for_timeout(300)
    pg.click('[data-test=kassa-plus-50ml]'); pg.wait_for_timeout(400)
    ck("teller 50ml = 2x vandaag", '2×' in (pg.text_content('[data-test=kassa-n-50ml]') or ''))
    ck("dagtotaal = €59 (2 × €29,50)", '59' in (pg.text_content('[data-test=kassa-vandaag]') or ''))
    ups=pg.evaluate("window.__UPSERTS")
    d=[u[1]['data'] for u in ups if u[0]=='tappunten'][-1]
    ck("v71-model: verkopen[vandaag]['50ml']==2", d.get('verkopen',{}).get(VANDAAG,{}).get('50ml')==2)
    kassaregels=[e for e in d.get('flesLog',[]) if e.get('src')=='kassa']
    ck("brug naar flessenlog: 2 regels {at,n:1,ti,src:'kassa'}",
       len(kassaregels)==2 and all(e['at']==VANDAAG and e['n']==1 and e['ti']==1 for e in kassaregels))
    ck("flessenteller telt kassa mee (vandaag=2)", (pg.text_content('[data-test=fles-vandaag]') or '')=='2')
    # correctie
    pg.click('[data-test=kassa-min-50ml]'); pg.wait_for_timeout(400)
    ck("correctie: teller terug naar 1x", '1×' in (pg.text_content('[data-test=kassa-n-50ml]') or ''))
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("correctie draait ook flessenlog terug (1 kassaregel over)",
       len([e for e in d.get('flesLog',[]) if e.get('src')=='kassa'])==1 and d.get('verkopen',{}).get(VANDAAG,{}).get('50ml')==1)

    # ===== CALCULATOR (exacte v71-formules) =====
    pg.click('nav >> text=Calculator'); pg.wait_for_timeout(500)
    # break-even: pakket 80 geuren (inv 3950), std/fles/50 (rev 16.53), 25/wk
    ck("break-even: 239 flessen (ceil 3950/16.53)", (pg.text_content('[data-test=be-bottles]') or '')=='239')
    ck("break-even: 70 dagen (ceil(239/25)=10 wkn)", (pg.text_content('[data-test=be-days]') or '')=='70')
    # vastleggen op winkel
    pg.select_option('[data-test=calc-winkel]','kl-1')
    pg.click('[data-test=calc-vastleggen]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    be=d.get('be',{})
    ck("t.be exact {inv:3950,rev:16.53,perWk:25,days:70,bottles:239}",
       be=={'inv':3950,'rev':16.53,'perWk':25,'days':70,'bottles':239})
    ck("t.pakket='0' gezet", d.get('pakket')=='0')
    # jaardoel: 15000, 8 refills, std/50 -> revKlant 132.21 -> 114 klanten, 1026 fl, 19.7/wk, 2.8/dag
    pg.click('[data-test=tab-doel]'); pg.wait_for_timeout(300)
    ck("jaardoel: 114 klanten", (pg.text_content('[data-test=goal-klanten]') or '')=='114')
    ck("jaardoel: 19.7 flessen/week", (pg.text_content('[data-test=goal-flweek]') or '')=='19.7')
    pg.click('[data-test=calc-vastleggen]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    g=d.get('goal',{})
    ck("t.goal exact (doel/klanten/flWeek/flJaar/flDag/refills)",
       g.get('doel')==15000 and g.get('klanten')==114 and g.get('flWeek')==19.7 and g.get('flJaar')==1026 and g.get('flDag')==2.8 and g.get('refills')==8)
    ck("t.doel=15000 mee gezet", d.get('doel')==15000)
    uitloggen(pg)

    # ===== KANTOOR: instellingen in beheer =====
    pg.evaluate("""window.__MOCK.signin={data:{user:{id:'u-staff',email:'k@tp.nl',app_metadata:{role:'staff'}}},error:null};""")
    login(pg,"kantoor@tp.nl")
    pg.click('nav >> text=Beheer'); pg.wait_for_timeout(500)
    pg.fill('[data-test=inst-prijs-2]','31')     # 50ml: 29.5 -> 31
    pg.fill('[data-test=inst-marge]','2')
    pg.fill('[data-test=inst-shopurl]','https://bestel.tapparfum.nl')
    pg.click('[data-test=inst-opslaan]'); pg.wait_for_timeout(500)
    ups=pg.evaluate("window.__UPSERTS")
    ck("flesMaten opgeslagen met 50ml=31", any(u[0]=='central' and u[1]['ns']=='flesMaten' and any(x['m']=='50ml' and x['p']==31 for x in u[1]['data']) for u in ups))
    ck("margeFactor=2 opgeslagen", any(u[0]=='central' and u[1]['ns']=='margeFactor' and u[1]['data']==2 for u in ups))
    ck("shopUrl opgeslagen", any(u[0]=='central' and u[1]['ns']=='shopUrl' and 'bestel.tapparfum' in str(u[1]['data']) for u in ups))
    uitloggen(pg)

    # ===== PARTNER: kassa wel, calculator niet =====
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
      data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:2400,flesLog:[],verkopen:{}}}];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    ck("partner: geen Calculator-tab", pg.locator('nav >> text=Calculator').count()==0)
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(700)
    ck("partner heeft kassa op eigen winkel", pg.locator('[data-test=kassa-plus-50ml]').count()==1)
    pg.click('[data-test=kassa-plus-15ml]'); pg.wait_for_timeout(400)
    ck("partner tikt 15ml -> dagtotaal €13 (12,50 afgerond)", '13' in (pg.text_content('[data-test=kassa-vandaag]') or ''))

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
