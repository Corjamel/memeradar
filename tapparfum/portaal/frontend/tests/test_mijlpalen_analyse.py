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

    # ===== PARTNER: mijlpalen bij omzet-mutatie (niveau + jaardoel) =====
    # 2500 -> 5000: kruist niveau C (3000) én het jaardoel (5000).
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
        data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:2500,doel:5000,setup:{skipped:true}}}];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(900)
    pg.fill('[data-test=omzet-jaaromzet]','5000')
    pg.click('[data-test=omzet-opslaan]'); pg.wait_for_timeout(700)
    ck("mijlpaal-banner: niveau C én jaardoel", 'Niveau C' in (pg.text_content('[data-test=mijlpaal]') or '') and 'Jaardoel' in (pg.text_content('[data-test=mijlpaal]') or ''))
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    soorten=[v['type'] for v in d.get('vieringen',[])]
    ck("t.vieringen: level + doel (v71-veld)", 'level' in soorten and 'doel' in soorten)
    ins=pg.evaluate("window.__INSERTS.filter(i=>i[0]==='winkelvragen'&&i[1].type==='mijlpaal').length")
    ck("mijlpaal-meldingen op de berichtlijn (2)", ins==2)

    # Vieringen op het dashboard + wegklikken
    pg.evaluate("window.__DB.tappunten[0].data.vieringen="+str([{'type':'level','k':'C','r':'Groeiend tappunt','at':VANDAAG},{'type':'doel','doel':5000,'at':VANDAAG}]).replace("'",'"'))
    pg.evaluate("window.__DB.tappunten[0].data.jaaromzet=5000")
    uitloggen(pg); login(pg,"winkel@tp.nl")
    ck("dashboard: 2 vieringsbanners", pg.locator('[data-test=viering-banner]').count()==2)
    ck("banner-tekst jaardoel", 'Jaardoel' in (pg.text_content('[data-test=viering-banner]') or '') or 'Niveau' in (pg.text_content('[data-test=viering-banner]') or ''))
    pg.click('[data-test=viering-weg-0]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("wegklikken -> viering uit t.vieringen (1 over)", len(d.get('vieringen',[]))==1)
    ck("banner weg uit beeld", pg.locator('[data-test=viering-banner]').count()==1)
    uitloggen(pg)

    # ===== PARTNER 2: break-even-mijlpaal via de kassa =====
    # 2 flessen tot break-even; één kassatik erbij = 3/3 -> be gehaald.
    pg.evaluate(f"""window.__DB.tappunten=[{{snelstart:'kl-2',name:'Deventer',email:null,geblokkeerd:false,am_id:'am-1',
        data:{{snelstart:'kl-2',name:'Deventer',jaaromzet:100,setup:{{skipped:true}},
              be:{{inv:50,rev:16.53,perWk:20,days:84,bottles:3}},
              flesLog:[{{at:'{VANDAAG}',n:2,ti:1}}]}}}}];
      window.__MOCK.signin={{data:{{user:{{id:'u-p2',app_metadata:{{}}}}}},error:null}};""")
    login(pg,"winkel2@tp.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(900)
    pg.locator('[data-test="kassa-plus-15ml"]').click(); pg.wait_for_timeout(700)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("kassatik kruist break-even -> beDone + beDoneAt", d.get('beDone')==True and d.get('beDoneAt')==VANDAAG)
    ck("kassa-mijlpaalbanner 'Break-even'", 'break-even' in (pg.text_content('[data-test=kassa-mijlpaal]') or '').lower())
    ck("viering type 'be' geschreven", any(v.get('type')=='be' for v in d.get('vieringen',[])))
    uitloggen(pg)

    # ===== KANTOOR: analysepagina =====
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'},{id:'am-2',naam:'Peter',auth_user_id:null}];
      window.__DB.tappunten=[
        {snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
         data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:12000,setup:{skipped:true},
               verkopen:{'"""+VANDAAG+"""':{'15ml':4,'50ml':2}},
               bestellingen:[{id:'b1',at:'"""+VANDAAG+"""',ref:'F1',totaal:500,omschrijving:'',bron:'handmatig'}]}},
        {snelstart:'kl-2',name:'Deventer',email:null,geblokkeerd:false,am_id:'am-2',
         data:{snelstart:'kl-2',name:'Deventer',jaaromzet:0,vorigJaar:4000,setup:{skipped:true},traject:false}},
        {snelstart:'kl-3',name:'Kampen',email:null,geblokkeerd:false,am_id:'am-1',
         data:{snelstart:'kl-3',name:'Kampen',jaaromzet:800}}];
      window.__MOCK.signin={data:{user:{id:'u-staff',email:'kantoor@tp.nl',app_metadata:{role:'staff'}}},error:null};""")
    login(pg,"kantoor@tp.nl")
    pg.click('nav >> text=Analyse'); pg.wait_for_timeout(700)
    ck("per-AM rijen (Marian, Peter, evt. Geen AM)", pg.locator('[data-test=analyse-am]').count()==2)
    ck("Marian: 2 winkels, inkoop 12.800, kassa 6 st.", '12.800' in (pg.text_content('[data-test=analyse-am]') or '') and '6 st' in (pg.text_content('[data-test=analyse-am]') or ''))
    ck("statusverdeling: groeit 1 / stagneert 1 / nieuw 1", '1' in (pg.text_content('[data-test=analyse-status-groeit]') or '') and '1' in (pg.text_content('[data-test=analyse-status-stagneert]') or '') and '1' in (pg.text_content('[data-test=analyse-status-nieuw]') or ''))
    ck("traject-teller 2 (Deventer eruit)", (pg.text_content('[data-test=analyse-traject]') or '').strip()=='2')
    ck("kassa per maat: 15ml en 50ml chips", pg.locator('[data-test=analyse-maat]').count()==2)
    # Sell-through-band (kassa)
    ck("sell-through-blok aanwezig", pg.locator('[data-test=sellthrough]').count()==1)
    ck("activatie 14 dgn: 1 van 3", (pg.text_content('[data-test=st-activatie]') or '').replace(' ','').startswith('1/3'))
    ck("verkochte flesjes dit jaar = 6", (pg.text_content('[data-test=st-stuks]') or '').strip()=='6')
    ck("dekking 33% (1 van 3 met kassa)", '33%' in (pg.text_content('[data-test=st-dekking]') or ''))
    ck("top 5: Zwolle bovenaan", 'Zwolle' in (pg.locator('[data-test=analyse-top]').first.text_content() or ''))
    ck("bestelstilte: nooit besteld bovenaan", 'nooit besteld' in (pg.locator('[data-test=analyse-stil]').first.text_content() or ''))

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
