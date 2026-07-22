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

    # ===== PARTNER 1: onboarding-fase + retourfoto + dagtype =====
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
        data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:2000,setup:{done:{'0-0':true}}}}];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    ck("fase-kaart: opstartfase (1/19)", pg.locator('[data-test=fase-onboarding]').count()==1 and 'Nog 18' in (pg.text_content('[data-test=fase-onboarding]') or ''))

    # retour melden met bewijsfoto
    pg.click('nav >> text=Berichten'); pg.wait_for_timeout(500)
    pg.select_option('[data-test=vraag-type]','retour'); pg.wait_for_timeout(200)
    ck("foto-veld verschijnt bij retour", pg.locator('[data-test=vraag-foto]').count()==1)
    pg.fill('[data-test=vraag-txt]','Fles lekt bij de dop, zie foto.')
    pg.set_input_files('[data-test=vraag-foto]', {'name':'lek.jpg','mimeType':'image/jpeg','buffer':b'foto'})
    pg.click('[data-test=vraag-verstuur]'); pg.wait_for_timeout(600)
    ins=pg.evaluate("window.__INSERTS.filter(i=>i[0]==='winkelvragen').slice(-1)[0][1]")
    ck("melding -> insert met foto_pad in eigen winkelmap", ins['type']=='retour' and str(ins.get('foto_pad','')).startswith('kl-1/melding_') and ins['foto_pad'].endswith('lek.jpg'))
    ck("bewijsfoto-knop zichtbaar bij de melding", pg.locator('[data-test=vraag-foto-knop]').count()==1)

    # kassa-dagtype (winkel-detail)
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(900)
    ck("dagtype-keuze: 12 verkooptypes (v71 SALE_TYPES)", pg.locator('[data-test=kassa-dagtype] option').count()==12)
    pg.select_option('[data-test=kassa-dagtype]','5'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("dagtype kiezen -> t.dagType=5", d.get('dagType')==5)
    pg.evaluate("window.__DB.tappunten[0].data.dagType=5")   # mock bewaart upserts niet
    pg.locator('[data-test="kassa-plus-15ml"]').click(); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("kassatik logt met gekozen dagtype (ti=5)", d['flesLog'][-1]['ti']==5 and d['flesLog'][-1]['src']=='kassa')
    uitloggen(pg)

    # ===== PARTNER 2: terugverdien- en jaardoel-fase + nudges =====
    pg.evaluate(f"""window.__DB.central=[{{ns:'acties',data:[{{id:'a1',titel:'Zomeractie',eind:null,punten:0,archived:false}}]}}];
      window.__DB.tappunten=[{{snelstart:'kl-2',name:'Deventer',email:null,geblokkeerd:false,am_id:'am-1',
        data:{{snelstart:'kl-2',name:'Deventer',jaaromzet:1000,setup:{{skipped:true}},
              be:{{inv:3950,rev:16.53,perWk:20,days:84,bottles:239}},
              flesLog:[{{at:'{VANDAAG}',n:100,ti:1}}],
              afspraken:[{{id:'x1',at:'{VANDAAG}',txt:'Poster',done:false}}]}}}}];
      window.__MOCK.signin={{data:{{user:{{id:'u-p2',app_metadata:{{}}}}}},error:null}};""")
    login(pg,"winkel2@tp.nl")
    ck("fase-kaart: terugverdienfase 100/239 (42%)", pg.locator('[data-test=fase-breakeven]').count()==1 and '100 van 239' in (pg.text_content('[data-test=fase-breakeven]') or '') and '42%' in (pg.text_content('[data-test=fase-breakeven]') or ''))
    ck("nudges: nieuwe actie + open afspraak", pg.locator('[data-test=nudge]').count()==2)
    # jaardoel-fase: break-even klaar + doel gezet (verse login zodat de store herlaadt)
    uitloggen(pg)
    pg.evaluate("""window.__DB.tappunten[0].data.beDone=true;
      window.__DB.tappunten[0].data.doel=20000; window.__DB.tappunten[0].data.jaaromzet=8000;""")
    login(pg,"winkel2@tp.nl")
    ck("fase-kaart: jaardoel 40%", pg.locator('[data-test=fase-jaardoel]').count()==1 and '40%' in (pg.text_content('[data-test=fase-jaardoel]') or ''))
    uitloggen(pg)

    # ===== KANTOOR (beheer-rol): rechten-matrix vastleggen =====
    pg.evaluate("""window.__DB.central=[];window.__DB.accountmanagers=[];
      window.__MOCK.signin={data:{user:{id:'u-staff',email:'clarence@retail-brands.nl',app_metadata:{role:'staff'}}},error:null};""")
    login(pg,"clarence@retail-brands.nl")
    ck("beheer-rol: Beheer-link zichtbaar", pg.locator('nav >> text=Beheer').count()==1)
    pg.click('nav >> text=Beheer'); pg.wait_for_timeout(600)
    pg.fill('[data-test=recht-email]','collega@retail-brands.nl')
    pg.select_option('[data-test=recht-rol]','kantoor')
    pg.click('[data-test=recht-toevoegen]'); pg.wait_for_timeout(500)
    ups=pg.evaluate("window.__UPSERTS")
    ck("vastleggen -> central kantoorRechten met rol kantoor", any(u[0]=='central' and u[1]['ns']=='kantoorRechten' and u[1]['data'].get('collega@retail-brands.nl',{}).get('rol')=='kantoor' for u in ups))
    pg.uncheck('[data-test="recht-acties-collega@retail-brands.nl"]'); pg.wait_for_timeout(500)
    m=pg.evaluate("window.__DB.central.find(r=>r.ns==='kantoorRechten').data")
    ck("acties-recht uitgezet in de matrix", m['collega@retail-brands.nl']['acties']==False)
    uitloggen(pg)

    # ===== KANTOOR (kantoor-rol, beperkt): menu gefilterd =====
    pg.evaluate("""window.__MOCK.signin={data:{user:{id:'u-staff2',email:'collega@retail-brands.nl',app_metadata:{role:'staff'}}},error:null};""")
    login(pg,"collega@retail-brands.nl")
    ck("kantoor-rol: GEEN Beheer-link", pg.locator('nav >> text=Beheer').count()==0)
    pg.click('nav >> text=Acties'); pg.wait_for_timeout(500)
    ck("kantoor-rol zonder acties-recht: geen actie-formulier", pg.locator('[data-test=actie-toevoegen]').count()==0)
    pg.click('nav >> text=Producten'); pg.wait_for_timeout(500)
    ck("producten-recht staat aan: wel lanceer-formulier", pg.locator('[data-test=prod-opslaan]').count()==1)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
