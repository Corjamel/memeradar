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
    pg.click('button[type=submit]'); pg.wait_for_timeout(600)
def uitloggen(pg):
    pg.click('button:has-text("Uitloggen")'); pg.wait_for_timeout(400)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT)
    pg.goto(URL); pg.wait_for_timeout(500)

    # ===== PARTNER: topwinkel — auto-uitkering home + niveau-korting A+/A++ =====
    # jaaromzet 60000, vorig jaar 6000 (serieuze basis -> groei-eis telt en is ruim
    # gehaald), setup overgeslagen, Tapbar-cursus (5 lessen) afgerond, marge-factor 2.
    pg.evaluate("""window.__DB.central=[{ns:'margeFactor',data:2}];
      window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
        data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:60000,vorigJaar:6000,liveDate:'2026-01-01',
              setup:{skipped:true},academy:{tapbar:{0:true,1:true,2:true,3:true,4:true}}}}];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    ck("dashboard: niveau A++ (60000 x factor 2 = 120000)", (pg.text_content('[data-test=niveau-naam]') or '').strip()=='A++')

    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(900)   # partner -> direct eigen detail
    ck("niveau-badge A++", (pg.text_content('[data-test=niveau-badge]') or '').strip()=='A++')
    ck("status-badge Top (A++ -> top)", 'Top' in (pg.text_content('[data-test=status-badge]') or ''))
    ck("winkelomzet 120.000 (schatting inkoop x 2)", '120.000' in (pg.text_content('[data-test=wo-bedrag]') or ''))
    ck("hoogste niveau bereikt", 'Hoogste niveau' in (pg.text_content('.nivo') or ''))
    ck("niveaubeloning actief: 10% korting", '10% korting' in (pg.text_content('.nivo') or ''))

    # Automatische uitkering: home (5000+groei+tapbar) + lvl-A+ + lvl-A++
    ck("3 vieringen (home + A+ + A++)", pg.locator('[data-test=viering]').count()==3)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    bel=d.get('beloond',{})
    ck("t.beloond.home = vandaag", bel.get('home')==VANDAAG)
    ck("t.beloond['lvl-A+'] en ['lvl-A++'] = vandaag", bel.get('lvl-A+')==VANDAAG and bel.get('lvl-A++')==VANDAAG)
    ck("3 vieringen in t.vieringen (type beloning)", len([v for v in d.get('vieringen',[]) if v.get('type')=='beloning'])==3)
    ins=pg.evaluate("window.__INSERTS")
    mijlpalen=[i for i in ins if i[0]=='winkelvragen' and i[1].get('type')=='mijlpaal']
    ck("3 mijlpaal-meldingen op de berichtlijn ('regel de uitkering')", len(mijlpalen)==3 and all('regel de uitkering' in m[1]['txt'] for m in mijlpalen))

    ck("home-kaart: VRIJGESPEELD", pg.locator('[data-test=rew-won-home]').count()==1)
    ck("kaarsen nog dicht: zwakste schakel = funnel-cursus 0%", (pg.text_content('[data-test=rew-pct-kaarsen]') or '').strip()=='0%')
    ck("vials nog dicht: 0/70 basispunten -> 0%", (pg.text_content('[data-test=rew-pct-vials]') or '').strip()=='0%')

    # Geen dubbele uitkering: pagina verlaten en terugkomen mag niets nieuws uitkeren
    n1=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').length")
    pg.evaluate("window.__DB.tappunten[0].data.beloond="+str(bel).replace("True","true"))  # alsof Supabase het bewaarde
    pg.evaluate("window.__DB.tappunten[0].data.vieringen=[]")
    pg.click('nav >> text=Start'); pg.wait_for_timeout(300)
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(900)
    n2=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').length")
    ck("eenmalig uitkeren: geen nieuwe upsert bij herbezoek", n1==n2)

    # Beloningen-pagina partner: eigen engine, geen winkellijst
    pg.click('nav >> text=Beloningen'); pg.wait_for_timeout(700)
    ck("beloningen-pagina: 5 spaarcadeaus", all(pg.locator(f'[data-test=rew-{k}]').count()==1 for k in ['vials','home','kaarsen','bodymist','promodag']))
    ck("productfoto op bodymist/vials/promodag-kaart", all(pg.locator(f'[data-test=rew-foto-{k}]').count()==1 for k in ['bodymist','vials','promodag']))
    ck("beloningen-pagina: geen winkel-overzicht voor partner", pg.locator('[data-test=winkel-niveau]').count()==0)
    uitloggen(pg)

    # ===== AM: statuslogica (nieuw / stagneert) + overzicht =====
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[
        {snelstart:'kl-2',name:'Nieuwe Winkel',email:null,geblokkeerd:false,am_id:'am-1',
         data:{snelstart:'kl-2',name:'Nieuwe Winkel',jaaromzet:500}},
        {snelstart:'kl-3',name:'Stille Winkel',email:null,geblokkeerd:false,am_id:'am-1',
         data:{snelstart:'kl-3',name:'Stille Winkel',jaaromzet:0,vorigJaar:5000,setup:{skipped:true}}}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"marian@tp.nl")
    pg.click('nav >> text=Beloningen'); pg.wait_for_timeout(700)
    ck("AM-overzicht: 2 winkels met niveau", pg.locator('[data-test=winkel-niveau]').count()==2)
    ck("AM-overzicht: statusbadges Nieuw + Stagneert", 'Nieuw' in (pg.text_content('.kaart') or '') and 'Stagneert' in (pg.text_content('.kaart') or ''))
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(400)
    pg.locator('[data-test=tappunt-rij]', has_text='Nieuwe Winkel').click(); pg.wait_for_timeout(800)
    ck("winkel zonder afgeronde checklist: status Nieuw", 'Nieuw' in (pg.text_content('[data-test=status-badge]') or ''))
    ck("winkel-detail: niveau D (omzet 500)", (pg.text_content('[data-test=niveau-badge]') or '').strip()=='D')

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
