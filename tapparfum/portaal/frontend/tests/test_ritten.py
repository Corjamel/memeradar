from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
# Geolocatie stubben: elke peiling schuift iets op zodat de km-keten > 0 wordt.
GEO="""
window.__geoN=0;
Object.defineProperty(navigator,'geolocation',{configurable:true,value:{
  getCurrentPosition:function(ok){window.__geoN++;ok({coords:{latitude:52.10+window.__geoN*0.01,longitude:5.10+window.__geoN*0.01,accuracy:12}});}
}});
"""
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(800)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")

    # ===== AM: werkdag + check-in + toggle =====
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.add_init_script(GEO); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:6000}}];
      window.__DB.am_locaties=[];
      window.__MOCK.signin={data:{user:{id:'u-am',email:'m@tp.nl',app_metadata:{}}},error:null};""")
    login(pg,"m@tp.nl")
    pg.click('nav >> text=Ritten'); pg.wait_for_timeout(500)
    ck("toggle staat standaard aan", pg.is_checked('[data-test=rit-toggle-input]'))
    ck("Start-knop zichtbaar", pg.locator('[data-test=rit-start]').count()==1)

    pg.click('[data-test=rit-start]'); pg.wait_for_timeout(500)
    ins=pg.evaluate("window.__INSERTS.filter(u=>u[0]==='am_locaties').map(u=>u[1])")
    ck("start-stempel met coördinaten", ins[-1]['type']=='start' and 'lat' in ins[-1] and 'lng' in ins[-1])
    ck("werkdag loopt -> Stop-knop", pg.locator('[data-test=rit-stop]').count()==1)

    # check-in bij winkel
    pg.select_option('[data-test=rit-winkel]','kl-1'); pg.wait_for_timeout(150)
    pg.click('[data-test=rit-checkin]'); pg.wait_for_timeout(500)
    ins=pg.evaluate("window.__INSERTS.filter(u=>u[0]==='am_locaties').map(u=>u[1])")
    ck("bezoek-stempel met winkel + coords", ins[-1]['type']=='bezoek' and ins[-1]['tappunt_snelstart']=='kl-1' and 'lat' in ins[-1])

    # toggle UIT -> volgende stempel zonder coords
    pg.click('[data-test=rit-toggle-input]'); pg.wait_for_timeout(150)
    ck("toggle nu uit", not pg.is_checked('[data-test=rit-toggle-input]'))
    pg.click('[data-test=rit-stop]'); pg.wait_for_timeout(500)
    ins=pg.evaluate("window.__INSERTS.filter(u=>u[0]==='am_locaties').map(u=>u[1])")
    ck("stop-stempel ZONDER coords (locatie uit)", ins[-1]['type']=='stop' and 'lat' not in ins[-1])

    # dag-render + km-indicatie
    ck("dag-kaart met stempels", pg.locator('[data-test=rit-dag]').count()>=1)
    ck("km-indicatie getoond", 'indicatie' in (pg.text_content('[data-test=rit-dag]') or ''))
    ck("AM ziet geen wis-knop", pg.locator('[data-test^=rit-wis-]').count()==0)

    # ===== KANTOOR: overzicht per AM + verwijderen =====
    pg2=b.new_context().new_page(); pg2.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg2.add_init_script(INIT); pg2.add_init_script(GEO); pg2.goto(URL); pg2.wait_for_timeout(400)
    pg2.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian'},{id:'am-2',naam:'Peter'}];
      window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle'}}];
      window.__DB.am_locaties=[
        {id:'L1',am_id:'am-1',type:'start',lat:52.1,lng:5.1,acc:10,at:'2026-07-24T08:00:00Z'},
        {id:'L2',am_id:'am-1',type:'bezoek',tappunt_snelstart:'kl-1',lat:52.2,lng:5.2,acc:10,at:'2026-07-24T10:00:00Z'},
        {id:'L3',am_id:'am-2',type:'start',lat:53.0,lng:6.0,acc:10,at:'2026-07-24T09:00:00Z'}];
      window.__MOCK.signin={data:{user:{id:'u-staff',email:'k@tp.nl',app_metadata:{role:'staff'}}},error:null};""")
    login(pg2,"k@tp.nl")
    pg2.click('nav >> text=Ritten'); pg2.wait_for_timeout(500)
    ck("kantoor ziet per-AM blokken (2)", pg2.locator('[data-test=rit-am]').count()==2)
    ck("kantoor ziet AM-namen", 'Marian' in (pg2.text_content('body') or '') and 'Peter' in (pg2.text_content('body') or ''))
    ck("kantoor heeft wis-knoppen", pg2.locator('[data-test^=rit-wis-]').count()>=1)
    pg2.click('[data-test=rit-wis-L3]'); pg2.wait_for_timeout(400)
    dels=pg2.evaluate("window.__DELETES.filter(u=>u[0]==='am_locaties')")
    ck("verwijderen gaat naar am_locaties", len(dels)>=1)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
