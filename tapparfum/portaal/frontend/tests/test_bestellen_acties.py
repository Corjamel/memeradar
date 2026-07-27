from playwright.sync_api import sync_playwright
from datetime import date, timedelta
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1

INIT=open("/tmp/claude-0/-home-user-memeradar/b0dc4ae2-3376-5404-9da1-5b0364a4f411/scratchpad/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
VANDAAG=date.today().isoformat()
GISTER=(date.today()-timedelta(days=1)).isoformat()
VOLGWEEK=(date.today()+timedelta(days=7)).isoformat()

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

    # ===== PARTNER: bestelscherm + actie-deelname + feedback =====
    # actie A1 loopt (10 punten), actie A0 is gisteren afgelopen en heeft deelname zonder resultaat.
    pg.evaluate(f"""window.__DB.central=[
        {{ns:'acties',data:[
          {{id:'a1',titel:'Zomeractie',omschrijving:'Gratis flesje bij zomergeur',start:null,eind:'{VOLGWEEK}',punten:10,video:'https://youtu.be/abc123xyz',materialen:'poster, flyers',archived:false}},
          {{id:'a0',titel:'Lenteactie',omschrijving:'',start:null,eind:'{GISTER}',punten:5,video:'',materialen:'',archived:false}}]}},
        {{ns:'shopUrl',data:'https://voorbeeld.nl/bestel'}}];
      window.__DB.tappunten=[{{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
        data:{{snelstart:'kl-1',name:'Zwolle',jaaromzet:6000,
              actieDeelname:{{a0:{{done:true,at:'{GISTER}',by:'partner'}}}}}}}}];
      window.__MOCK.signin={{data:{{user:{{id:'u-p',app_metadata:{{}}}}}},error:null}};""")
    login(pg,"winkel@tp.nl")

    # Bestellen-scherm
    pg.click('nav >> text=Bestellen'); pg.wait_for_timeout(600)
    ck("shopUrl-knop naar bestelportaal", pg.locator('[data-test=shop-knop]').count()==1)
    ck("4 pakket-segmenten uit v71", all(pg.locator(f'[data-test="seg-{s}"]').count()==1 for s in ['Klein assortiment','Tapbar (vanaf 160)','Winkel','PRFM']))
    ck("13 startpakketten + 10 uitbreidingen", pg.locator('[data-test^=pak-]').count()==13 and pg.locator('[data-test=bijproduct]').count()==10)
    pg.click('[data-test="bom-knop-80 geuren"]'); pg.wait_for_timeout(300)
    bomtxt=pg.text_content('[data-test="bom-80 geuren"]') or ''
    ck("stuklijst 80 geuren: inhoud + gratis + prijs", 'Labelprinter QL700' in bomtxt and 'Beachvlag' in bomtxt and '3.950' in bomtxt)
    ck("gratis materialen gemarkeerd", 'Gratis erbij' in bomtxt)
    # v71-diepte: samenstelling + incl. btw + per geur op de pakketkaart
    sv=pg.text_content('[data-test="samenvat-100 geuren (incl. 15 Exclusive)"]') or ''
    ck("samenstelling: 100 geuren · 15 Exclusive + 85 regulier", '100 geuren' in sv and '15 Exclusive' in sv and '85 regulier' in sv)
    ck("prijs incl. btw getoond (4702.5 -> 5690)", '5.690' in sv and 'incl. btw' in sv)
    ck("prijs per geur getoond", 'per geur' in sv)

    # Acties: meedoen + gezien-markering
    pg.click('nav >> text=Acties'); pg.wait_for_timeout(700)
    ck("actiepunten-chip (+10) op lopende actie", '+10' in (pg.text_content('[data-test=actie-chip-punten]') or ''))
    ck("YouTube-video privacyvriendelijk embed", pg.locator('iframe[src*="youtube-nocookie.com/embed/abc123xyz"]').count()==1)
    ck("materialen zichtbaar", 'poster, flyers' in (pg.text_content('[data-test=actie]') or ''))
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("bekijken -> actiesGezienP=[a1] (melding weg)", 'a1' in d.get('actiesGezienP',[]))
    pg.click('[data-test=meedoen-a1]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("Wij doen mee -> actieDeelname[a1]={done,at,by:'partner'}", d['actieDeelname']['a1']['done']==True and d['actieDeelname']['a1']['by']=='partner' and d['actieDeelname']['a1']['at']==VANDAAG)
    ck("badge 'Jullie doen mee'", pg.locator('[data-test=mee-badge]').count()==1)

    # Feedbackronde (a0 afgelopen, deelname zonder res)
    ck("feedback-due kaart voor Lenteactie", pg.locator('[data-test=feedback-due]').count()==1 and 'Lenteactie' in (pg.text_content('[data-test=feedback-due]') or ''))
    pg.select_option('[data-test=fb-werkte-kl-1]','ja')
    pg.click('[data-test=fb-opslaan-kl-1]'); pg.wait_for_timeout(600)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    dl=d['actieDeelname']['a0']
    ck("feedback -> res{werkte:'ja',at,by:'partner'} + 5 punten", dl['res']['werkte']=='ja' and dl['res']['by']=='partner' and dl.get('punten')==5)
    ck("logboek-notitie 'Actie afgerond … +5 punten'", any('Actie afgerond' in (l.get('txt') or '') and '+5' in (l.get('txt') or '') for l in d.get('logboek',[])))
    ck("melding toont toegekende punten", '+5' in (pg.text_content('[data-test=actie-melding]') or ''))
    ck("feedback-due kaart verdwenen", pg.locator('[data-test=feedback-due]').count()==0)
    uitloggen(pg)

    # ===== AM: uitrol per winkel + stats =====
    pg.evaluate(f"""window.__DB.accountmanagers=[{{id:'am-1',naam:'Marian',auth_user_id:'u-am'}}];
      window.__DB.tappunten=[
        {{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
         data:{{snelstart:'kl-1',name:'Zwolle',jaaromzet:6000,
               actieDeelname:{{a0:{{done:true,at:'{GISTER}',by:'partner',res:{{werkte:'ja',tekst:'liep goed',at:'{VANDAAG}',by:'partner'}},punten:5}}}}}}}},
        {{snelstart:'kl-2',name:'Deventer',email:null,geblokkeerd:false,am_id:'am-1',
         data:{{snelstart:'kl-2',name:'Deventer',jaaromzet:3000}}}}];
      window.__MOCK.signin={{data:{{user:{{id:'u-am',app_metadata:{{}}}}}},error:null}};""")
    login(pg,"marian@tp.nl")
    pg.click('nav >> text=Acties'); pg.wait_for_timeout(700)
    ck("AM ziet deelname-telling 0/2 op lopende actie", '0/2' in (pg.text_content('[data-test=actie-mee]') or ''))
    pg.locator('details.uitrol summary').click(); pg.wait_for_timeout(200)
    pg.check('[data-test=mee-kl-2-a1]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("AM rolt uit -> actieDeelname[a1] by:'am' op Deventer", d['actieDeelname']['a1']['by']=='am' and d['name']=='Deventer')
    ck("telling naar 1/2", '1/2' in (pg.text_content('[data-test=actie-mee]') or ''))
    ck("resultaat-stats a0: 1 afgerond, 1x ja, 5 punten", '1 afgerond' in (pg.text_content('[data-test=stats-a0]') or '') and '5 punten' in (pg.text_content('[data-test=stats-a0]') or ''))
    ck("AM ziet Bestellen-link NIET in nav (partner-scherm)", pg.locator('nav >> text=/^Bestellen$/').count()==0)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
