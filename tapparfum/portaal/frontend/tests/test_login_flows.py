from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1

# generieke mock + auth-uitbreidingen (signUp, rpc, resetPasswordForEmail)
BASIS=open("/tmp/claude-0/-home-user-memeradar/b0dc4ae2-3376-5404-9da1-5b0364a4f411/scratchpad/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
EXTRA = r"""
window.__MOCK.signup={data:null,error:{message:'x'}};
window.__RPC={data:null,error:null};
window.__resetCalled=null; window.__lastRpc=null; window.__lastSignup=null;
window.__TP_SUPABASE_MOCK.rpc=function(name,args){window.__lastRpc={name:name,args:args};
  if(name==='claim_tappunt'&&!(__RPC.error)){
    window.__DB.tappunten=[{snelstart:args.p_snelstart,name:'Nieuwe Winkel',email:null,geblokkeerd:false,am_id:null,
      data:{snelstart:args.p_snelstart,name:'Nieuwe Winkel',jaaromzet:0,flesLog:[]}}];
  }
  return Promise.resolve(window.__RPC);};
window.__TP_SUPABASE_MOCK.auth.signUp=function(c){window.__lastSignup=c;return Promise.resolve(window.__MOCK.signup);};
window.__TP_SUPABASE_MOCK.auth.resetPasswordForEmail=function(e){window.__resetCalled=e;return Promise.resolve({error:null});};
"""
INIT=BASIS+EXTRA

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT)
    pg.goto(URL); pg.wait_for_timeout(500)

    ck("login toont link 'eerste keer (winkel)'", pg.locator('[data-test=naar-nieuw]').count()==1)
    ck("login toont link 'wachtwoord vergeten'", pg.locator('[data-test=naar-reset]').count()==1)

    # 1. Eerste keer MET directe sessie -> claim -> binnen als partner
    pg.click('[data-test=naar-nieuw]'); pg.wait_for_timeout(300)
    pg.evaluate("window.__MOCK.signup={data:{user:{id:'nw-1',app_metadata:{}},session:{access_token:'x',user:{id:'nw-1'}}},error:null}")
    pg.fill('[data-test=su-code]','kl-77')
    pg.fill('[data-test=su-email]','nieuw@winkel.nl')
    pg.fill('[data-test=su-pass]','wachtwoord8'); pg.fill('[data-test=su-pass2]','wachtwoord8')
    pg.click('[data-test=su-maak]'); pg.wait_for_timeout(700)
    rpc=pg.evaluate("window.__lastRpc")
    ck("claim_tappunt aangeroepen met snelstartcode", bool(rpc) and rpc['name']=='claim_tappunt' and rpc['args']['p_snelstart']=='kl-77')
    ck("direct ingelogd als partner", 'Partner' in (pg.text_content('.rol') or ''))
    ck("ziet zijn gekoppelde winkel op dashboard", 'Nieuwe Winkel' in (pg.text_content('[data-test=eigen-kaart]') or ''))
    pg.click('button:has-text("Uitloggen")'); pg.wait_for_timeout(400)

    # 2. Wachtwoorden ongelijk -> nette fout, geen signup
    pg.click('[data-test=naar-nieuw]'); pg.wait_for_timeout(300)
    pg.evaluate("window.__lastSignup=null")
    pg.fill('[data-test=su-code]','kl-88'); pg.fill('[data-test=su-email]','x@y.nl')
    pg.fill('[data-test=su-pass]','wachtwoord8'); pg.fill('[data-test=su-pass2]','anders123')
    pg.click('[data-test=su-maak]'); pg.wait_for_timeout(300)
    ck("ongelijke wachtwoorden -> foutmelding, geen signup", pg.locator('.err').count()==1 and pg.evaluate("window.__lastSignup===null"))

    # 3. Eerste keer ZONDER sessie (e-mailbevestiging) -> pending, daarna login koppelt
    pg.evaluate("window.__MOCK.signup={data:{user:{id:'nw-2',app_metadata:{}},session:null},error:null}")
    pg.fill('[data-test=su-pass2]','wachtwoord8')
    pg.click('[data-test=su-maak]'); pg.wait_for_timeout(500)
    ck("bevestig-pad: terug op login met uitleg", pg.locator('.okmsg').count()==1)
    ck("pending claim onthouden", pg.evaluate("localStorage.getItem('tp_pending_claim::x@y.nl')==='kl-88'"))
    # nu inloggen na 'bevestiging'
    pg.evaluate("""window.__MOCK.signin={data:{user:{id:'nw-2',app_metadata:{}}},error:null};window.__lastRpc=null;""")
    pg.fill('input[type=password]','wachtwoord8')
    pg.click('button[type=submit]'); pg.wait_for_timeout(700)
    rpc=pg.evaluate("window.__lastRpc")
    ck("na login: pending claim uitgevoerd (kl-88)", bool(rpc) and rpc['args']['p_snelstart']=='kl-88')
    ck("pending claim opgeruimd", pg.evaluate("localStorage.getItem('tp_pending_claim::x@y.nl')===null"))
    ck("binnen als partner", 'Partner' in (pg.text_content('.rol') or ''))
    pg.click('button:has-text("Uitloggen")'); pg.wait_for_timeout(400)

    # 4. Wachtwoord vergeten
    pg.click('[data-test=naar-reset]'); pg.wait_for_timeout(300)
    pg.fill('[data-test=reset-email]','vergeten@winkel.nl')
    pg.click('[data-test=reset-stuur]'); pg.wait_for_timeout(400)
    ck("resetmail aangevraagd bij Supabase", pg.evaluate("window.__resetCalled==='vergeten@winkel.nl'"))
    ck("nette melding (geen adres-lek)", 'bekend is' in (pg.text_content('.okmsg') or ''))

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
