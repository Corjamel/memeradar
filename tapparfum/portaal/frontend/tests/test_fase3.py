from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1

INIT = r"""
window.__TP_NO_WELKOM=true;
window.__DB = { tappunten: [], accountmanagers: [], berichten: [], agenda: [], winkelvragen: [], central: [] };
window.__UPSERTS=[]; window.__INSERTS=[]; window.__UPDATES=[]; window.__UPLOADS=[]; window.__FILES={};
window.__MOCK = { session:null, signin:{data:null,error:{message:'x'}} };
function _q(table){
  var api={ _f:[],
    select:function(){return api;}, order:function(){return api;}, limit:function(){return api;},
    eq:function(c,v){api._f.push([c,v]);return api;},
    insert:function(row){window.__INSERTS.push([table,row]);return Promise.resolve({error:null});},
    upsert:function(row,o){window.__UPSERTS.push([table,row]);
      if(table==='central'){var rows=window.__DB.central;var i=rows.findIndex(function(r){return r.ns===row.ns;});
        if(i>=0)rows[i]=row;else rows.push(row);}
      return Promise.resolve({error:null});},
    update:function(patch){api._patch=patch;return api;},
    then:function(res){
      if(api._patch){window.__UPDATES.push([table,api._patch,api._f.slice()]);
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
  storage:{ from:function(){ return { list:function(){return Promise.resolve({data:[],error:null});},
    upload:function(p){window.__UPLOADS.push(p);return Promise.resolve({error:null});},
    createSignedUrl:function(p){return Promise.resolve({data:{signedUrl:'x'},error:null});} };}},
  auth:{
    getSession:function(){return Promise.resolve({data:{session:window.__MOCK.session}});},
    signInWithPassword:function(){return Promise.resolve(window.__MOCK.signin);},
    signOut:function(){return Promise.resolve({});}
  }
};
"""

DATA_K = """window.__DB.tappunten=[
 {snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:2400}},
 {snelstart:'kl-2',name:'Deventer',email:null,geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-2',name:'Deventer',jaaromzet:900}},
 {snelstart:'kl-3',name:'Kampen',email:null,geblokkeerd:true,am_id:'am-2',data:{snelstart:'kl-3',name:'Kampen',jaaromzet:0}}];
window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'},{id:'am-2',naam:'Kees',auth_user_id:'u-x'}];
window.__DB.winkelvragen=[{id:'w1',tappunt_snelstart:'kl-1',type:'vraag',txt:'Wanneer komt de nieuwe geur?',status:'open',antwoord:null,created_at:'2026-07-20'}];
window.__DB.agenda=[{id:'a1',tappunt_snelstart:'kl-1',am_id:'am-1',datum:'2026-08-01',tijd:'10:00',type:'bezoek',status:'voorgesteld',notitie:null}];
window.__DB.central=[{ns:'acties',data:[
  {id:'act1',titel:'Lopende actie',omschrijving:'Doe mee',start:null,eind:'2099-01-01',archived:false},
  {id:'act2',titel:'Oude actie',omschrijving:'',start:null,eind:'2020-01-01',archived:false}]}];"""

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

    # ===== KANTOOR =====
    pg.evaluate(DATA_K)
    pg.evaluate("window.__MOCK.signin={data:{user:{id:'u-staff',email:'kantoor@tp.nl',app_metadata:{role:'staff'}}},error:null}")
    login(pg,"kantoor@tp.nl")
    ck("dashboard: 3 winkels", '3' in (pg.text_content('[data-test=tile-winkels]') or ''))
    ck("dashboard: omzet-tegel toont som (3.300)", '3.300' in (pg.text_content('[data-test=tile-omzet]') or ''))
    ck("dashboard: 1 open melding", '1' in (pg.text_content('[data-test=tile-open]') or ''))
    ck("dashboard: 1 geblokkeerd", '1' in (pg.text_content('[data-test=tile-blok]') or ''))
    ck("dashboard: per-AM rijen (2)", pg.locator('[data-test=am-rij]').count()==2)
    ck("dashboard: eerstvolgend bezoek zichtbaar", pg.locator('[data-test=komend-item]').count()==1)

    # Acties: kantoor voegt toe + archiveert
    pg.click('nav >> text=Acties'); pg.wait_for_timeout(500)
    ck("kantoor ziet 1 lopende actie (verlopen weggefilterd)", pg.locator('[data-test=actie]').count()==1)
    pg.fill('[data-test=actie-titel]','Zomeractie 2026')
    pg.click('[data-test=actie-toevoegen]'); pg.wait_for_timeout(500)
    ups=pg.evaluate("window.__UPSERTS")
    ck("toevoegen -> upsert central ns 'acties'", any(u[0]=='central' and u[1]['ns']=='acties' and any(a['titel']=='Zomeractie 2026' for a in u[1]['data']) for u in ups))
    ck("nieuwe actie zichtbaar (2 lopend)", pg.locator('[data-test=actie]').count()==2)
    pg.locator('[data-test=actie]:has-text("Zomeractie 2026") >> [data-test=actie-archiveer]').click(); pg.wait_for_timeout(500)
    ck("archiveren -> weer 1 lopende actie", pg.locator('[data-test=actie]').count()==1)

    # Beloningen: kantoor-overzicht met v71-niveaus per winkel
    pg.click('nav >> text=Beloningen'); pg.wait_for_timeout(500)
    ck("kantoor ziet niveaus per winkel (3 rijen)", pg.locator('[data-test=winkel-niveau]').count()==3)
    uitloggen(pg)

    # ===== AM (Marian) =====
    pg.evaluate("""window.__DB.tappunten=window.__DB.tappunten.filter(function(t){return t.am_id==='am-1';});
      window.__DB.winkelvragen=[];window.__DB.agenda=[];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"marian@tp.nl")
    ck("AM-dashboard: 2 winkels", '2' in (pg.text_content('[data-test=tile-winkels]') or ''))
    ck("AM-dashboard: top-winkels lijst", pg.locator('[data-test=top-winkel]').count()==2)
    pg.click('nav >> text=Acties'); pg.wait_for_timeout(400)
    ck("AM ziet lopende actie, GEEN beheer-formulier", pg.locator('[data-test=actie]').count()==1 and pg.locator('[data-test=actie-toevoegen]').count()==0)
    uitloggen(pg)

    # ===== PARTNER (omzet 6000 -> niveau C bij marge-factor 1) =====
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-9',name:'Eigen Winkel',email:null,geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-9',name:'Eigen Winkel',jaaromzet:6000}}];
      window.__DB.central=window.__DB.central.filter(function(r){return r.ns!=='beloningen';});
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    ck("partner-dashboard: eigen winkelkaart", pg.locator('[data-test=eigen-kaart]').count()==1)
    ck("partner-dashboard: niveau C (6000 bij factor 1)", (pg.text_content('[data-test=niveau-naam]') or '').strip()=='C')
    pg.click('nav >> text=Beloningen'); pg.wait_for_timeout(500)
    ck("partner: niveau-badge C", (pg.text_content('[data-test=niveau-badge]') or '').strip()=='C')
    ck("partner: 5 spaarcadeaus zichtbaar", all(pg.locator(f'[data-test=rew-{k}]').count()==1 for k in ['vials','home','kaarsen','bodymist','promodag']))
    ck("partner: GEEN winkel-overzicht (alleen eigen winkel)", pg.locator('[data-test=winkel-niveau]').count()==0)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
