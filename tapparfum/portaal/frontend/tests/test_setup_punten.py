from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
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

    # ===== PARTNER: opstartchecklist =====
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
      data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:6000,doel:5000,vorigJaar:0,flesLog:[],verkopen:{},
            bp:{prijzen:true,presentatie:true,zichtbaar:true,home:true,exclusief:true,kwaliteit:true,geurnotenboek:true,
                hoek:true,voorraad:true,bodymist:true,hashtags:true,promopakket:true,certificaat:true,link:true,amcontact:true}}}];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    # bp-preset: alles behalve 'geuren'(6) = 70-6 = 64... we willen 55: prijzen5+presentatie10+zichtbaar5+home5+exclusief5+kwaliteit5+geurnotenboek5+hoek5+voorraad3+bodymist3+hashtags3+promopakket3+certificaat5+link1+amcontact1 = 64. Basis=64 -> al officieel; prima: check badge + claim-flow met 'geuren'.
    login(pg,"winkel@tp.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(700)   # partner -> direct detail

    ck("opstartchecklist zichtbaar (0/19)", '0/19' in (pg.text_content('[data-test=setup-stand]') or ''))
    ck("fase 4 op slot (demodag nog niet gepland)", pg.locator('[data-test=setup-slot]').count()==2)
    pg.check('[data-test=setup-0-0]'); pg.wait_for_timeout(400)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("vinkje -> t.setup.done['0-0']=true (v71-sleutel)", d.get('setup',{}).get('done',{}).get('0-0')==True)
    ck("teller naar 1/19", '1/19' in (pg.text_content('[data-test=setup-stand]') or ''))
    # demodag plannen -> fase 4/5 open
    pg.locator('details.fase').nth(2).click(); pg.wait_for_timeout(200)
    pg.check('[data-test=setup-2-0]'); pg.wait_for_timeout(400)
    ck("demodag gepland -> sloten weg", pg.locator('[data-test=setup-slot]').count()==0)

    # ===== PARTNER: punten claimen =====
    ck("punten-chips zichtbaar, basis=64", '64' in (pg.text_content('[data-test=punt-basis]') or ''))
    ck("officieel-badge (>=60)", pg.locator('[data-test=punt-officieel]').count()==1)
    ck("auto-bonus: jaardoel gehaald (+5)", (pg.text_content('[data-test=punt-auto]') or '').find('5')>=0)
    pg.click('[data-test=claim-geuren]'); pg.wait_for_timeout(400)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("claim -> t.bpClaim.geuren=true", d.get('bpClaim',{}).get('geuren')==True)
    ck("rij toont 'wacht op AM'", 'wacht op AM' in (pg.text_content('[data-test=punt-geuren]') or ''))
    uitloggen(pg)

    # ===== AM: claim goedkeuren =====
    # (mock-upserts muteren de nep-db niet; seed de claim expliciet zoals hij in Supabase zou staan)
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten[0].data.bpClaim={geuren:true};
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"marian@tp.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(400)
    pg.click('[data-test=tappunt-rij]'); pg.wait_for_timeout(600)
    ck("AM ziet goedkeur-knop bij claim", pg.locator('[data-test=keur-geuren]').count()==1)
    pg.click('[data-test=keur-geuren]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("goedkeuren -> bp.geuren=true, claim weg", d.get('bp',{}).get('geuren')==True and not d.get('bpClaim',{}).get('geuren'))
    ck("basis nu 70/70", '70' in (pg.text_content('[data-test=punt-basis]') or ''))
    ck("totaal = 75 (70 basis + 5 jaardoel)", '75' in (pg.text_content('[data-test=punt-totaal]') or ''))
    # AM zet bonuspunt direct
    pg.check('[data-test=zet-weekpost]'); pg.wait_for_timeout(400)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("AM zet bonuspunt direct -> bonus.weekpost=true", d.get('bonus',{}).get('weekpost')==True)
    ck("bonus-chip = 5/35", '5' in (pg.text_content('[data-test=punt-bonus]') or ''))
    # setup read-only voor AM + skip
    ck("AM kan checklist niet aanvinken (disabled)", pg.locator('[data-test=setup-0-1][disabled]').count()==1)
    pg.click('[data-test=setup-skip]'); pg.wait_for_timeout(400)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("AM slaat checklist over -> setup.skipped=true", d.get('setup',{}).get('skipped')==True)
    ck("checklist toont 'overgeslagen'", 'overgeslagen' in (pg.text_content('[data-test=setup-klaar]') or ''))

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
