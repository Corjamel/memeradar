from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+= 1

# Mock-Supabase: geïnjecteerd vóór de app laadt. Gedrag stuurbaar via window.__MOCK.
INIT = r"""
window.__TP_NO_WELKOM=true;
window.__MOCK = { session:null, signin:{data:null,error:{message:'x'}}, ams:[] };
function _thenable(getRows){
  var api={ select:function(){return api;}, eq:function(c,v){api._c=c;api._v=v;return api;}, limit:function(){return api;},
    then:function(res){ var rows=getRows(api._c,api._v); return Promise.resolve({data:rows,error:null}).then(res); } };
  return api;
}
window.__TP_SUPABASE_MOCK = {
  from:function(t){ return _thenable(function(c,v){
    if(t==='accountmanagers'){ return (window.__MOCK.ams||[]).filter(function(a){return a.auth_user_id===v;}).map(function(a){return {id:a.id};}); }
    return [];
  }); },
  auth:{
    getSession:function(){ return Promise.resolve({data:{session:window.__MOCK.session}}); },
    signInWithPassword:function(c){ window.__lastSignin=c; return Promise.resolve(window.__MOCK.signin); },
    signOut:function(){ return Promise.resolve({}); }
  }
};
"""

def login(pg, email="x@y.nl", pw="geheim"):
    pg.fill('input[type=email]', email); pg.fill('input[type=password]', pw)
    pg.click('button[type=submit]'); pg.wait_for_timeout(400)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    ctx=b.new_context(); errs=[]
    pg=ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT)

    # 1. Guard: zonder sessie naar / -> belandt op /login
    pg.goto(URL); pg.wait_for_timeout(500)
    ck("zonder sessie -> loginscherm", "login" in pg.url or pg.query_selector('input[type=email]') is not None)

    # 2. Fout wachtwoord -> foutmelding, blijft op login
    pg.evaluate("window.__MOCK.signin={data:null,error:{message:'Invalid'}}")
    login(pg, "fout@y.nl","fout")
    ck("fout wachtwoord -> melding", pg.query_selector('.err') is not None and pg.query_selector('input[type=email]') is not None)

    # 3. Staff -> kantoor
    pg.evaluate("window.__MOCK.signin={data:{user:{id:'u-staff',app_metadata:{role:'staff'}}},error:null}")
    login(pg, "kantoor@tp.nl","goed")
    ck("staff -> ingelogd als kantoor", pg.evaluate("!!document.querySelector('.rol')") and 'Kantoor' in (pg.text_content('.rol') or ''))
    ck("kantoor ziet dashboard (cockpit)", 'Kantoor-cockpit' in (pg.text_content('h1') or ''))

    # uitloggen
    pg.click('button:has-text("Uitloggen")'); pg.wait_for_timeout(300)
    ck("uitloggen -> terug naar login", pg.query_selector('input[type=email]') is not None)

    # 4. AM-account (geen staff, wel in accountmanagers) -> am
    pg.evaluate("""window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};
                   window.__MOCK.ams=[{id:'am-1',auth_user_id:'u-am'}];""")
    login(pg, "am@tp.nl","goed")
    ck("AM -> ingelogd als am", 'Accountmanager' in (pg.text_content('.rol') or ''))
    pg.click('button:has-text("Uitloggen")'); pg.wait_for_timeout(300)

    # 5. Gewoon account (geen staff, niet in accountmanagers) -> partner
    pg.evaluate("""window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};
                   window.__MOCK.ams=[];""")
    login(pg, "winkel@tp.nl","goed")
    ck("gewoon account -> partner", 'Partner' in (pg.text_content('.rol') or ''))

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:4]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
