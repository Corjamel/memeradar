from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1

BASIS=open("/tmp/claude-0/-home-user-memeradar/b0dc4ae2-3376-5404-9da1-5b0364a4f411/scratchpad/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
EXTRA = r"""
window.__MOCK.signup={data:null,error:{message:'x'}};
window.__KOPPEL={data:null,error:null};
window.__TP_SUPABASE_MOCK.rpc=function(name,args){
  if(name==='tp_koppel_am' && window.__KOPPEL && window.__KOPPEL.data){
    (window.__DB.accountmanagers||[]).forEach(function(a){if(a.id===window.__KOPPEL.data)a.auth_user_id='u-newam';});
  }
  return Promise.resolve(name==='tp_koppel_am'?(window.__KOPPEL||{data:null,error:null}):{data:null,error:null});
};
window.__TP_SUPABASE_MOCK.auth.signUp=function(c){window.__lastSignup=c;return Promise.resolve(window.__MOCK.signup);};
window.__TP_SUPABASE_MOCK.auth.resetPasswordForEmail=function(e){return Promise.resolve({error:null});};
"""
INIT=BASIS+EXTRA

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

    # ===== KANTOOR: beheer =====
    pg.evaluate("""window.__DB.tappunten=[
      {snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:null,data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:100}}];
      window.__DB.accountmanagers=[];
      window.__MOCK.signin={data:{user:{id:'u-staff',email:'kantoor@tp.nl',app_metadata:{role:'staff'}}},error:null};""")
    login(pg,"kantoor@tp.nl")
    ck("kantoor heeft Beheer-tab", pg.locator('nav >> text=Beheer').count()==1)
    pg.click('nav >> text=Beheer'); pg.wait_for_timeout(500)

    # AM uitnodigen
    pg.fill('[data-test=am-naam]','Marian')
    pg.fill('[data-test=am-email]','marian@tp.nl')
    pg.click('[data-test=am-toevoegen]'); pg.wait_for_timeout(500)
    ins=pg.evaluate("window.__INSERTS")
    ck("uitnodigen -> insert accountmanager (naam+email)", any(i[0]=='accountmanagers' and i[1]['naam']=='Marian' and i[1]['email']=='marian@tp.nl' for i in ins))
    ck("AM in lijst met status 'uitgenodigd'", pg.locator('[data-test=am-rij]').count()==1 and 'uitgenodigd' in (pg.text_content('[data-test=am-status]') or ''))

    # winkel toewijzen aan de nieuwe AM
    amid=pg.evaluate("window.__DB.accountmanagers[0].id")
    pg.select_option('[data-test=winkel-am]', amid); pg.wait_for_timeout(500)
    upd=pg.evaluate("window.__UPDATES")
    ck("toewijzen -> update tappunten.am_id", any(u[0]=='tappunten' and u[1].get('am_id')==amid for u in upd))

    # verwijderen
    pg.click('[data-test=am-verwijder]'); pg.wait_for_timeout(400)
    dels=pg.evaluate("window.__DELETES")
    ck("verwijderen -> delete accountmanager", any(d[0]=='accountmanagers' for d in dels))
    uitloggen(pg)

    # ===== AM-EERSTE-KEER: registratie zonder code, koppeling op e-mail =====
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-9',naam:'Marian',email:'marian@tp.nl',auth_user_id:null}];
      window.__DB.tappunten=[];
      window.__KOPPEL={data:'am-9',error:null};
      window.__MOCK.signup={data:{user:{id:'u-newam',app_metadata:{}},session:{access_token:'x',user:{id:'u-newam'}}},error:null};""")
    pg.click('[data-test=naar-nieuw]'); pg.wait_for_timeout(300)
    ck("keuze winkel/accountmanager zichtbaar", pg.locator('[data-test=soort-am]').count()==1)
    pg.check('[data-test=soort-am]'); pg.wait_for_timeout(200)
    ck("AM-variant: geen snelstartcode-veld", pg.locator('[data-test=su-code]').count()==0)
    pg.fill('[data-test=su-email]','marian@tp.nl')
    pg.fill('[data-test=su-pass]','wachtwoord8'); pg.fill('[data-test=su-pass2]','wachtwoord8')
    pg.click('[data-test=su-maak]'); pg.wait_for_timeout(700)
    ck("AM direct ingelogd als accountmanager (koppeling op e-mail)", 'Accountmanager' in (pg.text_content('.rol') or ''))
    ck("AM ziet GEEN Beheer-tab", pg.locator('nav >> text=Beheer').count()==0)
    uitloggen(pg)

    # ===== PARTNER: geen Beheer =====
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:null,data:{snelstart:'kl-1',name:'Zwolle'}}];
      window.__KOPPEL={data:null,error:null};
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    ck("partner: geen Beheer-tab", pg.locator('nav >> text=Beheer').count()==0)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
