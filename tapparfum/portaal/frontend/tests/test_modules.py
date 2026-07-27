from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1

# Mock-Supabase met een mini-database. RLS simuleren we door __DB per rol te vullen
# (de echte scoping is server-side bewezen met de PG16-gedragstesten).
INIT = r"""
window.__TP_NO_WELKOM=true;
window.__DB = { tappunten: [], accountmanagers: [], berichten: [], agenda: [], winkelvragen: [] };
window.__UPSERTS=[]; window.__INSERTS=[]; window.__UPDATES=[];
window.__MOCK = { session:null, signin:{data:null,error:{message:'x'}} };
function _q(table){
  var api={ _f:[],
    select:function(){return api;}, order:function(){return api;}, limit:function(){return api;},
    eq:function(c,v){api._f.push([c,v]);return api;},
    insert:function(row){window.__INSERTS.push([table,row]);return Promise.resolve({error:null});},
    upsert:function(row,o){window.__UPSERTS.push([table,row]);return Promise.resolve({error:null});},
    update:function(patch){api._patch=patch;return api;},
    then:function(res){
      if(api._patch){window.__UPDATES.push([table,api._patch,api._f.slice()]);
        // pas toe op de mini-db zodat herladen klopt
        var rows=window.__DB[table]||[];rows.forEach(function(r){var hit=api._f.every(function(f){return r[f[0]]===f[1];});if(hit)Object.assign(r,api._patch);});
        return Promise.resolve({error:null}).then(res);}
      var rows=(window.__DB[table]||[]).slice();
      api._f.forEach(function(f){rows=rows.filter(function(r){return r[f[0]]===f[1];});});
      return Promise.resolve({data:rows,error:null}).then(res);
    }
  };
  return api;
}
window.__TP_SUPABASE_MOCK = {
  from:_q,
  auth:{
    getSession:function(){return Promise.resolve({data:{session:window.__MOCK.session}});},
    signInWithPassword:function(c){return Promise.resolve(window.__MOCK.signin);},
    signOut:function(){return Promise.resolve({});}
  }
};
"""

def login(pg, email):
    pg.fill('input[type=email]', email); pg.fill('input[type=password]', 'x')
    pg.click('button[type=submit]'); pg.wait_for_timeout(500)

def uitloggen(pg):
    pg.click('button:has-text("Uitloggen")'); pg.wait_for_timeout(400)

TAPPUNTEN_K = """window.__DB.tappunten=[
 {snelstart:'kl-1',name:'Zwolle',email:'z@s.nl',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle',plaats:'Zwolle',tel:'0611111111',jaaromzet:2400}},
 {snelstart:'kl-2',name:'Deventer',email:null,geblokkeerd:true,am_id:'am-1',data:{snelstart:'kl-2',name:'Deventer',plaats:'Deventer'}},
 {snelstart:'kl-3',name:'Kampen',email:null,geblokkeerd:false,am_id:'am-2',data:{snelstart:'kl-3',name:'Kampen',plaats:'Kampen'}}];
window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'},{id:'am-2',naam:'Kees',auth_user_id:'u-x'}];"""

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT)
    pg.goto(URL); pg.wait_for_timeout(500)

    # ===== KANTOOR =====
    pg.evaluate(TAPPUNTEN_K)
    pg.evaluate("window.__MOCK.signin={data:{user:{id:'u-staff',email:'kantoor@tp.nl',app_metadata:{role:'staff'}}},error:null}")
    login(pg,"kantoor@tp.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(500)
    rijen=pg.locator('[data-test=tappunt-rij]').count()
    ck("kantoor ziet alle 3 winkels", rijen==3)
    ck("geblokkeerde winkel heeft badge", pg.locator('.badge:has-text("geblokkeerd")').count()==1)

    # detail openen + bewerken
    pg.click('[data-test=tappunt-rij]:has-text("Zwolle")'); pg.wait_for_timeout(400)
    pg.fill('form.vorm >> nth=0 >> input >> nth=0', 'Zwolle Centrum')  # winkelnaam
    pg.click('button:has-text("Opslaan")'); pg.wait_for_timeout(400)
    ups=pg.evaluate("window.__UPSERTS")
    ok_up = len(ups)==1 and ups[0][0]=='tappunten' and ups[0][1]['name']=='Zwolle Centrum'
    ck("opslaan -> upsert met nieuwe naam", ok_up)
    keys=set(ups[0][1].keys()) if ups else set()
    ck("upsert bevat GEEN beschermde velden", not ({'geblokkeerd','am_id','auth_user_id'} & keys))
    ck("jaaromzet blijft behouden in data", ups and ups[0][1]['data'].get('jaaromzet')==2400)

    # blokkeren (alleen kantoor)
    ck("blokkeer-knop zichtbaar voor kantoor", pg.locator('[data-test=blok-knop]').count()==1)
    pg.click('[data-test=blok-knop]'); pg.wait_for_timeout(400)
    upd=pg.evaluate("window.__UPDATES")
    ck("blokkeren -> update geblokkeerd=true", any(u[0]=='tappunten' and u[1].get('geblokkeerd')==True for u in upd))

    # bericht sturen aan AM
    pg.click('[data-test=nav-berichten]'); pg.wait_for_timeout(400)
    pg.select_option('[data-test=am-select]','am-1')
    pg.fill('textarea','Bel Zwolle over de zomeractie')
    pg.click('[data-test=verstuur]'); pg.wait_for_timeout(400)
    ins=pg.evaluate("window.__INSERTS")
    ck("kantoor verstuurt -> insert bericht aan am-1", any(i[0]=='berichten' and i[1]['aan_am']=='am-1' and 'zomeractie' in i[1]['txt'] for i in ins))
    uitloggen(pg)

    # ===== AM (Marian) =====
    pg.evaluate("""window.__DB.tappunten=window.__DB.tappunten.filter(function(t){return t.am_id==='am-1';});
      window.__DB.berichten=[{id:'b1',aan_am:'am-1',van:'kantoor@tp.nl',type:'taak',txt:'Bel Zwolle over de zomeractie',status:'open',antwoord:null,created_at:'2026-07-20'}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"marian@tp.nl")
    ck("AM ingelogd als accountmanager", 'Accountmanager' in (pg.text_content('.rol') or ''))
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(400)
    ck("AM ziet alleen eigen winkels (2)", pg.locator('[data-test=tappunt-rij]').count()==2)
    # bericht beantwoorden
    pg.click('[data-test=nav-berichten]'); pg.wait_for_timeout(400)
    ck("AM ziet het bericht van kantoor", pg.locator('[data-test=bericht]').count()==1)
    pg.fill('[data-test=antwoord-veld]','Gedaan — gebeld en actie staat.')
    pg.click('[data-test=antwoord-knop]'); pg.wait_for_timeout(400)
    upd=pg.evaluate("window.__UPDATES")
    ck("antwoord -> update status=klaar + antwoord", any(u[0]=='berichten' and u[1].get('status')=='klaar' and 'gebeld' in (u[1].get('antwoord') or '') for u in upd))
    ck("antwoord zichtbaar in de lijst", pg.locator('[data-test=antwoord]').count()==1)
    uitloggen(pg)

    # ===== PARTNER (1 winkel -> direct naar detail) =====
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-9',name:'Eigen Winkel',email:'e@w.nl',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-9',name:'Eigen Winkel',plaats:'Urk'}}];
      window.__DB.accountmanagers=[];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(600)
    ck("partner -> direct op eigen winkel-detail", 'Eigen Winkel' in (pg.text_content('h1') or ''))
    ck("partner ziet GEEN blokkeer-knop", pg.locator('[data-test=blok-knop]').count()==0)
    ck("partner ziet WEL een Berichten-tab (winkelvragen)", pg.locator('[data-test=nav-berichten]').count()==1)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
