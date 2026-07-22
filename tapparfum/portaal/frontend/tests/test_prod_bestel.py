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

    # ===== KANTOOR: product lanceren + fase schuiven + CSV-import =====
    pg.evaluate("""window.__DB.tappunten=[
      {snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
       data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:5000}},
      {snelstart:'kl-2',name:'Deventer',email:null,geblokkeerd:false,am_id:'am-1',
       data:{snelstart:'kl-2',name:'Deventer',jaaromzet:3000,
             bestellingen:[{id:'b1',at:'2026-01-05',ref:'F900',totaal:400,omschrijving:'',bron:'handmatig'}]}}];
      window.__MOCK.signin={data:{user:{id:'u-staff',email:'kantoor@tp.nl',app_metadata:{role:'staff'}}},error:null};""")
    login(pg,"kantoor@tp.nl")

    # Producten
    pg.click('nav >> text=Producten'); pg.wait_for_timeout(600)
    pg.fill('[data-test=prod-naam]','Niventi Bodymist')
    pg.select_option('[data-test=prod-fase]','1')
    pg.click('[data-test=prod-opslaan]'); pg.wait_for_timeout(500)
    ups=pg.evaluate("window.__UPSERTS")
    ck("lanceren -> upsert central ns 'producten'", any(u[0]=='central' and u[1]['ns']=='producten' and u[1]['data'][0]['naam']=='Niventi Bodymist' for u in ups))
    ck("productkaart zichtbaar met tijdlijn", pg.locator('[data-test=product]').count()==1 and 'In productie' in (pg.text_content('[data-test=product]') or ''))
    pid=pg.evaluate("window.__DB.central.find(r=>r.ns==='producten').data[0].id")
    pg.click(f'[data-test=fase-plus-{pid}]'); pg.wait_for_timeout(400)
    pg.click(f'[data-test=fase-plus-{pid}]'); pg.wait_for_timeout(400)
    ck("fase 2x vooruit -> Leverbaar (fase 3)", pg.evaluate("window.__DB.central.find(r=>r.ns==='producten').data[0].fase")==3)
    ck("tijdlijn zegt 'Nu leverbaar'", 'Nu leverbaar' in (pg.text_content('[data-test=tijdlijn-status]') or ''))
    # adoptie + per winkel afvinken
    pg.locator('details.adoptie summary').click(); pg.wait_for_timeout(200)
    ck("adoptie 0 van 2", '0' in (pg.text_content('[data-test=adoptie]') or '') and 'van 2' in (pg.text_content('[data-test=adoptie]') or ''))
    pg.check(f'[data-test=prod-w-kl-1-{pid}]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("afvinken -> t.prodBesteld[pid]={done,at,by:'am'}", d.get('prodBesteld',{}).get(pid,{}).get('done')==True and d['prodBesteld'][pid]['by']=='am' and d['prodBesteld'][pid]['at']==VANDAAG)
    ck("logboek-notitie 'Besteld' geschreven", any('Besteld' in (l.get('txt') or '') for l in d.get('logboek',[])))

    # Bestellingen-pagina + CSV
    pg.click('nav >> text=Bestellingen'); pg.wait_for_timeout(600)
    ck("stiltelijst: Deventer 60+ dagen stil", pg.locator('[data-test=stil-winkel]').count()==1 and 'Deventer' in (pg.text_content('[data-test=stil-winkel]') or ''))
    pg.locator('details.imp summary').click(); pg.wait_for_timeout(200)
    pg.fill('[data-test=csv-tekst]',"datum;snelstart;ordernr;totaal\n15-07-2026;kl-1;F1001;€ 1.234,56\n15-07-2026;kl-2;F900;250\n15-07-2026;kl-9;F1002;100")
    ck("preview herkent 3 regels", '3 regels' in (pg.text_content('[data-test=csv-preview]') or ''))
    pg.click('[data-test=csv-import]'); pg.wait_for_timeout(600)
    res=pg.text_content('[data-test=csv-resultaat]') or ''
    ck("import: 1 ok, 1 dubbel (F900), kl-9 niet gevonden", '1 geïmporteerd' in res and '1 dubbel' in res and 'kl-9' in res)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    bst=d.get('bestellingen',[])[0]
    ck("EU-bedrag geparsed: 1234.56 + datum 15-07 -> 2026-07-15", bst['totaal']==1234.56 and bst['at']=='2026-07-15' and bst['bron']=='csv')
    uitloggen(pg)

    # ===== AM: winkel-detail — handmatig registreren + dedupe + ritme =====
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"marian@tp.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(400)
    pg.locator('[data-test=tappunt-rij]', has_text='Deventer').click(); pg.wait_for_timeout(800)
    ck("ritme-badge: stil (jan-bestelling)", 'stil' in (pg.text_content('[data-test=bestel-ritme]') or ''))
    ck("inkoop dit jaar = 400", '400' in (pg.text_content('[data-test=inkoop-jaar]') or ''))
    pg.fill('[data-test=best-totaal]','850')
    pg.fill('[data-test=best-ref]','F2000')
    pg.click('[data-test=best-toevoegen]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("registreren -> bestelling bovenaan met vandaag", d['bestellingen'][0]['ref']=='F2000' and d['bestellingen'][0]['at']==VANDAAG and d['bestellingen'][0]['totaal']==850)
    ck("ritme-badge nu groen (0 dagen)", 'stil' not in (pg.text_content('[data-test=bestel-ritme]') or ''))
    n1=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').length")
    pg.fill('[data-test=best-totaal]','850'); pg.fill('[data-test=best-ref]','F2000')
    pg.click('[data-test=best-toevoegen]'); pg.wait_for_timeout(400)
    n2=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').length")
    ck("dubbel ordernr geweigerd (geen upsert + melding)", n1==n2 and 'dubbel' in (pg.text_content('section.blok:has-text(\"Bestellingen\")') or ''))
    # twee-staps verwijderen
    wisknop=pg.locator('[data-test^=best-wis-]').first
    wisknop.click(); pg.wait_for_timeout(200)
    ck("eerste klik = 'Zeker?'", 'Zeker' in (wisknop.text_content() or ''))
    wisknop.click(); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("tweede klik verwijdert (F2000 weg)", all(x['ref']!='F2000' for x in d.get('bestellingen',[])))
    uitloggen(pg)

    # ===== PARTNER: producten zien + zelf 'besteld' melden; geen registratie-UI =====
    pg.evaluate("""window.__DB.tappunten=[window.__DB.tappunten[0]];
      window.__DB.tappunten[0].data.prodGezienP=[];
      window.__DB.central.push({ns:'shopUrl',data:'https://voorbeeld.nl/bestel'});
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    pg.click('nav >> text=Producten'); pg.wait_for_timeout(700)
    ck("partner ziet de lancering + tijdlijn", pg.locator('[data-test=product]').count()==1)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("bekijken markeert prodGezienP (v71-melding weg)", pid in d.get('prodGezienP',[]))
    pg.click(f'[data-test=prod-bestel-{pid}]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("partner meldt besteld -> by:'partner' + badge", d.get('prodBesteld',{}).get(pid,{}).get('by')=='partner' and pg.locator('[data-test=prod-besteld-badge]').count()==1)
    ck("partner: geen Bestellingen-link in nav", pg.locator('nav >> text=Bestellingen').count()==0)
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(800)
    ck("winkel-detail partner: wel bestelportaal-knop, geen registratieformulier", pg.locator('[data-test=best-toevoegen]').count()==0 and pg.locator('a:has-text("bestelportaal")').count()==1)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
