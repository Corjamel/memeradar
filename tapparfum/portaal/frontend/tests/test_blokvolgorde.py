from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(800)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")

    # ===== 1) KANTOOR: herschik + opslaan =====
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:null,data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:5000}}];
      window.__MOCK.signin={data:{user:{id:'u-staff',email:'k@tp.nl',app_metadata:{role:'staff'}}},error:null};""")
    login(pg,"k@tp.nl")
    pg.click('nav >> text=Beheer'); pg.wait_for_timeout(400)
    pg.click('[data-test=tab-instellingen]'); pg.wait_for_timeout(300)
    ck("blokvolgorde-lijst aanwezig (3 blokken)", pg.locator('.blokorder li').count()==3)
    ck("standaardvolgorde: fase bovenaan", 'fase' in (pg.locator('.blokorder li').first.get_attribute('data-test') or ''))
    # 'trofee' twee keer omhoog -> naar boven
    pg.click('[data-test=blok-op-trofee]'); pg.wait_for_timeout(150)
    pg.click('[data-test=blok-op-trofee]'); pg.wait_for_timeout(150)
    ck("trofee nu bovenaan in de editor", 'trofee' in (pg.locator('.blokorder li').first.get_attribute('data-test') or ''))
    pg.click('[data-test=inst-opslaan]'); pg.wait_for_timeout(500)
    up=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='central' && u[1]['ns']==='layout').slice(-1)[0][1]['data']")
    ck("volgorde opgeslagen: partner start met trofee", (up.get('volgorde') or {}).get('partner',[None])[0]=='trofee')
    ck("volgorde bevat alle 3", sorted((up.get('volgorde') or {}).get('partner',[]))==['fase','trofee','week'])

    # ===== 2) PARTNER: CSS-order toegepast =====
    pg2=b.new_context().new_page(); pg2.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg2.add_init_script(INIT); pg2.goto(URL); pg2.wait_for_timeout(400)
    pg2.evaluate("""window.__DB.central=[{ns:'layout',data:{volgorde:{partner:['trofee','fase','week']}}}];
      window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',
        data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:12000,setup:{skipped:true},doel:20000,
              goal:{doel:20000,flJaar:260,flWeek:5},bp:{prijzen:true,presentatie:true,zichtbaar:true,home:true},
              flesLog:[{at:'2026-01-05',n:80,ti:1}]}}];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg2,"winkel@tp.nl"); pg2.wait_for_timeout(500)
    ck("alle drie blokken zichtbaar", pg2.locator('.movable .kaart').count()>=3)
    o_trofee=pg2.eval_on_selector('[data-test=trofeeen]', "el=>el.style.order")
    o_week=pg2.eval_on_selector('[data-test=weekkaart]', "el=>el.style.order")
    o_fase=pg2.eval_on_selector('.movable .fasekaart', "el=>el.style.order")
    ck("trofee order=0 (bovenaan)", o_trofee=='0')
    ck("fase order=1", o_fase=='1')
    ck("week order=2", o_week=='2')

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
