import os
from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(800)

CSV="winkelnaam;klantnr;plaats;tel;email;accountmanager\nZwolle;kl-1;Zwolle;038-1;a@a.nl;Marian\nBoetiek Emmen;kl-99;Emmen;0591-2;e@e.nl;Marian\nLifestyle Meppel;;Meppel;0522-3;m@m.nl;\n"
path="/tmp/claude-0/-home-user-memeradar/b0dc4ae2-3376-5404-9da1-5b0364a4f411/scratchpad/winkels.csv"
open(path,"w").write(CSV)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:null,data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:5000}}];
      window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am',email:'m@tp.nl'}];
      window.__MOCK.signin={data:{user:{id:'u-staff',email:'k@tp.nl',app_metadata:{role:'staff'}}},error:null};""")
    login(pg,"k@tp.nl")
    pg.click('nav >> text=Beheer'); pg.wait_for_timeout(400)
    ck("KPI-kop op Beheer", pg.locator('[data-test=beheer-kpis] .kpi').count()>=4)
    pg.click('[data-test=tab-winkels]'); pg.wait_for_timeout(300)
    ck("CSV-import-kaart aanwezig", pg.locator('[data-test=csv-input]').count()==1)
    ck("export-knop aanwezig", pg.locator('[data-test=csv-export]').count()==1)

    # Stap 1: bestand kiezen -> koppelscherm met automatisch geraden kolommen
    pg.set_input_files('[data-test=csv-input]', path); pg.wait_for_timeout(500)
    ck("koppelscherm verschijnt (3 rijen)", '3 rijen' in (pg.text_content('[data-test=csv-koppel]') or ''))
    ck("winkelnaam automatisch herkend (kolom 1)", pg.locator('[data-test=csv-map-name]').input_value()=='0')
    ck("code automatisch herkend (klantnr)", pg.locator('[data-test=csv-map-snelstart]').input_value()=='1')
    ck("AM-kolom automatisch herkend", pg.locator('[data-test=csv-map-am]').input_value()=='5')
    # Meppel heeft geen AM in het bestand -> vaste AM als vangnet
    pg.select_option('[data-test=csv-vaste-am]','am-1'); pg.wait_for_timeout(100)

    # Stap 2: importeren
    pg.click('[data-test=csv-import-uitvoeren]'); pg.wait_for_timeout(900)
    mel=pg.text_content('[data-test=csv-melding]') or ''
    ck("melding: 2 aan AM gekoppeld", '2 gekoppeld aan een accountmanager' in mel)
    upd=pg.evaluate("window.__UPDATES.filter(u=>u[0]==='tappunten'&&u[1]['am_id'])")
    ck("AM-koppeling weggeschreven (2x am-1)", len(upd)==2 and all(u[1]['am_id']=='am-1' for u in upd))
    ck("melding: 2 geïmporteerd", '2 winkels geïmporteerd' in mel)
    ck("melding: 1 overgeslagen (dup Zwolle)", '1 bestond al' in mel)

    ups=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').map(u=>u[1])")
    ck("2 tappunten weggeschreven", len(ups)==2)
    namen=sorted([u['name'] for u in ups])
    ck("Emmen + Meppel geïmporteerd", namen==['Boetiek Emmen','Lifestyle Meppel'])
    ck("Emmen behield snelstart kl-99", any(u['snelstart']=='kl-99' for u in ups))
    ck("Meppel kreeg gegenereerde code", any(str(u['snelstart']).startswith('csv-') for u in ups))
    emmen=[u for u in ups if u['name']=='Boetiek Emmen'][0]
    ck("veldmapping: plaats/tel/email meegenomen", emmen['data'].get('plaats')=='Emmen' and emmen['data'].get('email')=='e@e.nl')
    ck("geïmporteerd = setup overgeslagen", emmen['data'].get('setup',{}).get('skipped')==True)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
