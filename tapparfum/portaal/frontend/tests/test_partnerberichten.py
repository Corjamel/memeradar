from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(800)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")

    # ===== PARTNER: nieuw antwoord -> banner + rij-badge + 'gezien'-RPC =====
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle'}}];
      window.__DB.winkelvragen=[
        {id:'wv-1',tappunt_snelstart:'kl-1',type:'vraag',txt:'Hoe bestel ik bij?',status:'beantwoord',antwoord:'Via Bestellen.',antwoord_door:'Marian',nieuw_voor_partner:true},
        {id:'wv-2',tappunt_snelstart:'kl-1',type:'retour',txt:'Kapotte fles',status:'open',nieuw_voor_partner:false}];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    pg.click('[data-test=nav-berichten]'); pg.wait_for_timeout(700)
    ck("partner ziet 'nieuw antwoord'-banner", pg.locator('[data-test=nieuw-antwoord-banner]').count()==1)
    ck("banner telt 1 nieuw antwoord", '1 nieuw antwoord' in (pg.text_content('[data-test=nieuw-antwoord-banner]') or ''))
    ck("beantwoorde vraag heeft 'nieuw antwoord'-badge", pg.locator('[data-test=vraag-nieuw]').count()==1)
    ck("antwoordtekst zichtbaar", 'Via Bestellen.' in (pg.text_content('[data-test=vraag-antwoord]') or ''))
    ck("gezien-RPC aangeroepen", 'tp_winkelvraag_gezien' in (pg.evaluate("window.__RPCS||[]")))
    ck("DB-vlag gewist door RPC", pg.evaluate("window.__DB.winkelvragen.find(v=>v.id==='wv-1').nieuw_voor_partner")==False)

    # ===== PARTNER: bezoek aanvragen (type 'bezoek') =====
    pg.select_option('[data-test=vraag-type]','bezoek'); pg.wait_for_timeout(150)
    pg.fill('[data-test=vraag-txt]','Graag hulp bij de tapbar'); pg.click('[data-test=vraag-verstuur]'); pg.wait_for_timeout(500)
    ins=pg.evaluate("window.__INSERTS.filter(i=>i[0]==='winkelvragen')")
    ck("bezoekaanvraag ingestuurd als type 'bezoek'", any(i[1].get('type')=='bezoek' and 'tapbar' in i[1].get('txt','') for i in ins))

    # ===== AM: beantwoorden zet nieuw_voor_partner=true =====
    pg2=b.new_context().new_page(); pg2.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg2.add_init_script(INIT); pg2.goto(URL); pg2.wait_for_timeout(400)
    pg2.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle'}}];
      window.__DB.winkelvragen=[{id:'wv-9',tappunt_snelstart:'kl-1',type:'vraag',txt:'Vraag?',status:'open',nieuw_voor_partner:false}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg2,"marian@tp.nl")
    pg2.click('[data-test=nav-berichten]'); pg2.wait_for_timeout(700)
    pg2.fill('[data-test=vraag-antwoord-veld]','Kijk op Bestellen.'); pg2.click('[data-test=vraag-antwoord-knop]'); pg2.wait_for_timeout(500)
    upd=pg2.evaluate("window.__UPDATES.filter(u=>u[0]==='winkelvragen')")
    ck("AM-antwoord zet status beantwoord + nieuw_voor_partner", any(u[1].get('status')=='beantwoord' and u[1].get('nieuw_voor_partner')==True for u in upd))

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
