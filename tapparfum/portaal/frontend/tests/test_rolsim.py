from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(800)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[
        {snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:'am-1',
         data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:12000,vorigJaar:6000,setup:{skipped:true},doel:20000,
               goal:{doel:20000,flJaar:260,flWeek:5},bp:{prijzen:true,presentatie:true,zichtbaar:true,home:true},
               flesLog:[{at:'2026-01-05',n:80,ti:1}]}},
        {snelstart:'kl-2',name:'Emmen',geblokkeerd:false,am_id:'am-1',
         data:{snelstart:'kl-2',name:'Emmen',jaaromzet:1800,vorigJaar:5200,setup:{skipped:true}}}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"m@tp.nl")

    # Winkeldetail -> knop "Bekijk als partner"
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(600)
    pg.click('[data-test=tappunt-rij]:has-text("Zwolle")'); pg.wait_for_timeout(600)
    ck("knop 'Bekijk als partner' zichtbaar voor AM", pg.locator('[data-test=bekijk-als-partner]').count()==1)
    pg.click('[data-test=bekijk-als-partner]'); pg.wait_for_timeout(700)

    # Nu de partnerweergave van kl-1
    ck("terug-banner (accountmanager) zichtbaar", pg.locator('[data-test=sim-terug]').count()==1)
    ck("banner noemt de winkel", 'Zwolle' in (pg.text_content('[data-test=sim-terug]') or ''))
    ck("partner stats-KPI-rij verschijnt", pg.locator('[data-test=pstats]').count()==1)
    ck("spotlight (partner) verschijnt", pg.locator('[data-test=spotlight]').count()==1)
    ck("berichtkaart (partner) verschijnt", pg.locator('[data-test=berichtkaart]').count()==1)
    # tegel toont 1 winkel (deze), niet de hele portefeuille
    ck("winkel-tegel toont 1", (pg.text_content('[data-test=tile-winkels] .cijfer') or '').strip()=='1')
    # AM-cockpit-secties zijn verborgen in simulatie
    ck("AM-aandachtslijst verborgen in simulatie", pg.locator('[data-test=aandacht]').count()==0)
    ck("AM top-winkels verborgen in simulatie", pg.locator('[data-test=top-winkel]').count()==0)

    # Terug naar accountmanager-weergave
    pg.click('[data-test=sim-terug]'); pg.wait_for_timeout(600)
    ck("terug op winkeldetail", pg.locator('[data-test=metricrow]').count()==1)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
