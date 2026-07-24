from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(800)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    ctx=b.new_context(); pg=ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT)
    pg.add_init_script("window.__TP_NO_WELKOM=false;")  # rondleiding juist wél tonen
    pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:6000}}];
      window.__MOCK.signin={data:{user:{id:'u-am',email:'m@tp.nl',app_metadata:{}}},error:null};""")
    login(pg,"m@tp.nl")

    # Eerste login: rondleiding verschijnt met 4 stappen (AM-variant)
    ck("welkom-rondleiding verschijnt bij eerste login", pg.locator('[data-test=welkom]').count()==1)
    ck("vier stappen", pg.locator('[data-test=welkom-stap]').count()==4)
    ck("AM-stap 'Vandaag' aanwezig", 'Vandaag' in (pg.text_content('[data-test=welkom]') or ''))
    pg.click('[data-test=welkom-start]'); pg.wait_for_timeout(300)
    ck("na 'Aan de slag' is de rondleiding weg", pg.locator('[data-test=welkom]').count()==0)
    ck("gezien opgeslagen in localStorage", pg.evaluate("localStorage.getItem('tp_welkom::am::m@tp.nl')")=='1')

    # ❓ opent de rondleiding opnieuw
    pg.click('[data-test=help-knop]'); pg.wait_for_timeout(300)
    ck("❓ heropent de rondleiding", pg.locator('[data-test=welkom]').count()==1)
    pg.click('[data-test=welkom-sluit]'); pg.wait_for_timeout(300)
    ck("kruisje sluit de rondleiding", pg.locator('[data-test=welkom]').count()==0)

    # Contextuele terug-knop: niet op home, wel op een subscherm
    ck("geen terug-knop op home", pg.locator('[data-test=terug-knop]').count()==0)
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(500)
    ck("terug-knop op subscherm", pg.locator('[data-test=terug-knop]').count()==1)
    pg.click('[data-test=terug-knop]'); pg.wait_for_timeout(500)
    ck("terug brengt naar home", pg.locator('[data-test=terug-knop]').count()==0)

    # Tweede login (nieuwe pagina, zelfde storage): rondleiding niet meer
    pg.reload(); pg.wait_for_timeout(700)
    ck("na 'gezien' verschijnt de rondleiding niet meer", pg.locator('[data-test=welkom]').count()==0)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
