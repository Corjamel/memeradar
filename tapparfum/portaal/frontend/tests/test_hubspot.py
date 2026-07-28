from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1

INIT=open("/tmp/claude-0/-home-user-memeradar/b0dc4ae2-3376-5404-9da1-5b0364a4f411/scratchpad/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]

def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x')
    pg.click('button[type=submit]'); pg.wait_for_timeout(600)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)

    # ===== AM opent een winkel — HubSpot gemockt via window.__MOCK.hubspot =====
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[{snelstart:'kl-1',name:'BLISS TAPPARFUMBAR',email:'anja@bliss.nl',geblokkeerd:false,am_id:'am-1',
        data:{snelstart:'kl-1',name:'BLISS TAPPARFUMBAR',email:'anja@bliss.nl',jaaromzet:8000}}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};
      window.__MOCK.hubspot={companies:[{id:'c1',name:'BLISS TAPPARFUMBAR',city:'Winschoten',phone:'0597-123456'}],
        contacts:[{id:'k1',firstname:'Anja',lastname:'Bakker',email:'anja@bliss.nl',jobtitle:'Eigenaar'}],
        deals:[{id:'d1',dealname:'Tweede display',amount:'1500',dealstage:'presentationscheduled'}]};""")
    login(pg,"marian@tp.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(500)
    pg.locator('[data-test=tappunt-rij]').first.click(); pg.wait_for_timeout(900)

    ck("HubSpot-paneel zichtbaar voor AM", pg.locator('[data-test=hubspot-paneel]').count()==1)
    ck("gematcht bedrijf getoond", 'BLISS TAPPARFUMBAR' in (pg.text_content('[data-test=hs-bedrijven]') or '') and 'Winschoten' in (pg.text_content('[data-test=hs-bedrijven]') or ''))
    ck("contactpersoon getoond", 'Anja Bakker' in (pg.text_content('[data-test=hs-contacten]') or '') and 'anja@bliss.nl' in (pg.text_content('[data-test=hs-contacten]') or ''))
    ck("deal + bedrag getoond", 'Tweede display' in (pg.text_content('[data-test=hs-deals]') or '') and '1.500' in (pg.text_content('[data-test=hs-deals]') or ''))

    # ===== Geen match -> rustige melding (leeg resultaat, zonder reload) =====
    pg.evaluate("window.__MOCK.hubspot={companies:[],contacts:[],deals:[]}")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(400)
    pg.locator('[data-test=tappunt-rij]').first.click(); pg.wait_for_timeout(700)
    ck("geen match -> rustige melding", pg.locator('[data-test=hs-leeg]').count()==1)
    # (Partner ziet het paneel niet: structureel geborgd via v-if="!auth.isPartner"
    #  in TappuntDetailView — net als de andere AM/kantoor-only blokken.)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX",e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
