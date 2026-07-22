from playwright.sync_api import sync_playwright
from datetime import date, timedelta
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1

INIT=open("/tmp/claude-0/-home-user-memeradar/b0dc4ae2-3376-5404-9da1-5b0364a4f411/scratchpad/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
VANDAAG=date.today().isoformat()
D40=(date.today()-timedelta(days=40)).isoformat()   # live-datum: d30 net te laat, d60/d90 komen later
D120=(date.today()-timedelta(days=120)).isoformat()
MORGEN=(date.today()+timedelta(days=1)).isoformat()

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

    # ===== AM: logboek op de winkelpagina =====
    # Zwolle: live 40 dgn geleden (d7/d30 te laat), nooit bezocht, claim op 'geuren'
    # (bezoek-gebonden), open afspraak; Deventer: laatste bezoek 120 dgn geleden.
    pg.evaluate(f"""window.__DB.accountmanagers=[{{id:'am-1',naam:'Marian',auth_user_id:'u-am'}}];
      window.__DB.tappunten=[
        {{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
         data:{{snelstart:'kl-1',name:'Zwolle',tel:'038-123',jaaromzet:6000,liveDate:'{D40}',
               be:{{inv:3950,rev:16.53,perWk:20,days:84,bottles:239}},
               bpClaim:{{geuren:true}},
               afspraken:[{{id:'a1',at:'{VANDAAG}',txt:'Poster ophangen',done:false}}]}}}},
        {{snelstart:'kl-2',name:'Deventer',email:null,geblokkeerd:false,am_id:'am-1',
         data:{{snelstart:'kl-2',name:'Deventer',jaaromzet:3000,laatsteBezoek:'{D120}',
               bestellingen:[{{id:'b1',at:'{VANDAAG}',ref:'F1',totaal:500,omschrijving:'',bron:'handmatig'}}]}}}}];
      window.__MOCK.signin={{data:{{user:{{id:'u-am',app_metadata:{{}}}}}},error:null}};""")
    login(pg,"marian@tp.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(400)
    pg.locator('[data-test=tappunt-rij]', has_text='Zwolle').click(); pg.wait_for_timeout(800)

    ck("ritme-badge: nog nooit bezocht", 'nooit bezocht' in (pg.text_content('[data-test=bezoek-ritme]') or ''))
    ck("claims-banner: 1 punt controleren bij bezoek", '1' in (pg.text_content('[data-test=claims-banner]') or ''))
    # bezoek plannen
    pg.fill('[data-test=plan-datum]', MORGEN)
    pg.click('[data-test=plan-knop]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("plannen -> t.bezoekGepland", d.get('bezoekGepland')==MORGEN)
    # verslag schrijven met opvolgdatum
    pg.fill('[data-test=log-tekst]','Goede sfeer, tapbar staat top. Voorraad check volgende week.')
    pg.fill('[data-test=log-next]', MORGEN)
    pg.click('[data-test=log-toevoegen]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    e=d['logboek'][0]
    ck("bezoekverslag -> logboek[{at,type:'bezoek',txt,nextDate}]", e['type']=='bezoek' and e['at']==VANDAAG and e['nextDate']==MORGEN and 'sfeer' in e['txt'])
    # v71-regel: alleen planningen op/vóór de verslagdatum worden afgeboekt — morgen blijft staan
    ck("bezoek -> laatsteBezoek vooruit, planning van morgen blijft", d.get('laatsteBezoek')==VANDAAG and d.get('bezoekGepland')==MORGEN)
    ck("ritme-badge nu groen (0 dgn)", 'niet bezocht' not in (pg.text_content('[data-test=bezoek-ritme]') or '') and 'nooit' not in (pg.text_content('[data-test=bezoek-ritme]') or ''))
    # afspraak afvinken + nieuwe vastleggen (2 regels)
    aid=pg.evaluate("window.__DB.tappunten[0].data.afspraken[0].id") if False else 'a1'
    pg.locator('[data-test=afspraak-a1] input').click(); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("afspraak afgevinkt door AM (doneBy 'am')", d['afspraken'][0]['done']==True and d['afspraken'][0]['doneBy']=='am')
    pg.fill('[data-test=afspraak-tekst]','Nieuwe testers bestellen\nDemodagposter mailen')
    pg.click('[data-test=afspraak-toevoegen]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("2 regels -> 2 nieuwe open afspraken", len([a for a in d['afspraken'] if not a['done']])==2)
    uitloggen(pg)

    # ===== AM: Vandaag-werklijst =====
    # verse staat: Zwolle live 40 dgn (d7+d30 te laat, d60 over 20, d90 buiten week),
    # nooit bezocht+claim, geen bestellingen; Deventer 120 dgn geen bezoek, wel besteld vandaag.
    pg.evaluate(f"""window.__DB.tappunten[0].data={{snelstart:'kl-1',name:'Zwolle',tel:'038-123',jaaromzet:6000,
        liveDate:'{D40}',be:{{inv:3950,rev:16.53,perWk:20,days:84,bottles:239}},bpClaim:{{geuren:true}},
        afspraken:[{{id:'a2',at:'{VANDAAG}',txt:'Poster ophangen',done:false}}]}};
      window.__DB.winkelvragen=[{{id:'w1',tappunt_snelstart:'kl-1',type:'vraag',txt:'Wanneer komen de zomergeuren?',status:'open',created_at:'{VANDAAG}T10:00:00Z'}}];
      window.__MOCK.signin={{data:{{user:{{id:'u-am',app_metadata:{{}}}}}},error:null}};""")
    login(pg,"marian@tp.nl")
    pg.click('nav >> text=Vandaag'); pg.wait_for_timeout(800)

    ck("kop 🔥 Nu aanwezig", pg.locator('[data-test=kop-nu]').count()==1)
    ck("fu d7 én d30 te laat in Nu (2 cadans-items)", pg.locator('[data-test=item-fu]').count()>=2 and 'te laat' in (pg.text_content('[data-test=item-fu]') or ''))
    ck("fu-target uit break-evenplan zichtbaar", 'flessen' in (pg.locator('[data-test=item-fu]').first.text_content() or ''))
    ck("open winkelvraag in Nu met Beantwoord-link", pg.locator('[data-test=item-vraag]').count()==1 and 'zomergeuren' in (pg.text_content('[data-test=item-vraag]') or ''))
    ck("open afspraak in Deze week", pg.locator('[data-test=item-afspraak]').count()==1)
    ck("punten-controle-bezoek (claim zonder plan)", pg.locator('[data-test=item-controle]').count()==1)
    ck("bezoekritme: Zwolle nooit + Deventer 120 dgn", pg.locator('[data-test=item-bezoek]').count()==2)
    ck("bestelritme: alleen Zwolle (Deventer bestelde vandaag)", pg.locator('[data-test=item-bestel]').count()==1 and 'Zwolle' in (pg.text_content('[data-test=item-bestel]') or ''))
    ck("belknopje bij winkel met telefoonnummer", pg.locator('a[href="tel:038-123"]').count()>=1)
    # fu afvinken -> t.fu.d7 = vandaag
    pg.locator('[data-test=vink-fu-d7]').first.click(); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("afvinken cadans -> t.fu.d7 = vandaag", d.get('fu',{}).get('d7')==VANDAAG)
    # bezoek plannen vanuit de lijst
    pg.locator('[data-test=plan-kl-2]').click(); pg.wait_for_timeout(200)
    pg.fill('[data-test=plan-datum]', MORGEN)
    pg.click('[data-test=plan-ok]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("Plan vanuit Vandaag -> bezoekGepland op Deventer", d.get('bezoekGepland')==MORGEN and d.get('name')=='Deventer')
    uitloggen(pg)

    # ===== PARTNER: ziet afspraken (en vinkt), geen logboek/Vandaag =====
    pg.evaluate("""window.__DB.tappunten=[window.__DB.tappunten[0]];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    ck("partner: geen Vandaag in nav", pg.locator('nav >> text=Vandaag').count()==0)
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(800)
    ck("partner ziet open afspraak, géén logboek-formulier", pg.locator('[data-test=afspraak-a2]').count()==1 and pg.locator('[data-test=log-toevoegen]').count()==0)
    pg.locator('[data-test=afspraak-a2] input').click(); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    afgerond=[a for a in d['afspraken'] if a['id']=='a2'][0]
    ck("partner vinkt af -> doneBy 'partner' + logboek-notitie", afgerond['doneBy']=='partner' and any('door partner' in (l.get('txt') or '') for l in d.get('logboek',[])))

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
