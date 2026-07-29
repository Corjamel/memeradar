from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1

INIT = r"""
window.__DB = { tappunten:[], accountmanagers:[], berichten:[], agenda:[], winkelvragen:[], central:[], contacten:[], deals:[], taken:[] };
window.__UPSERTS=[]; window.__INSERTS=[]; window.__UPDATES=[]; window.__DELETES=[];
window.__TP_NO_WELKOM=true;
window.__MOCK = { session:null, signin:{data:null,error:{message:'x'}} };
var __seq=0;
function _q(table){
  var api={ _f:[],
    select:function(){return api;}, order:function(){return api;}, limit:function(){return api;},
    eq:function(c,v){api._f.push([c,v]);return api;},
    insert:function(row){window.__INSERTS.push([table,row]);
      row=Object.assign({id:table+'-'+(++__seq)},row);
      if(row.klaar===undefined&&table==='taken')row.klaar=false;
      if(row.fase===undefined&&table==='deals')row.fase='lead';
      if(row.status===undefined&&table==='agenda')row.status='voorgesteld';
      if(row.status===undefined&&table==='winkelvragen')row.status='open';
      (window.__DB[table]=window.__DB[table]||[]).unshift(row);
      return Promise.resolve({error:null});},
    upsert:function(row,o){window.__UPSERTS.push([table,row]);
      if(table==='central'){var rows=window.__DB.central;var i=rows.findIndex(function(r){return r.ns===row.ns;});
        if(i>=0)rows[i]=row;else rows.push(row);}
      return Promise.resolve({error:null});},
    update:function(patch){api._patch=patch;return api;},
    delete:function(){api._del=true;return api;},
    then:function(res){
      if(api._del){window.__DELETES.push([table,api._f.slice()]);
        window.__DB[table]=(window.__DB[table]||[]).filter(function(r){return !api._f.every(function(f){return r[f[0]]===f[1];});});
        return Promise.resolve({error:null}).then(res);}
      if(api._patch){window.__UPDATES.push([table,api._patch,api._f.slice()]);
        (window.__DB[table]||[]).forEach(function(r){if(api._f.every(function(f){return r[f[0]]===f[1];}))Object.assign(r,api._patch);});
        return Promise.resolve({error:null}).then(res);}
      var rows=(window.__DB[table]||[]).slice();
      api._f.forEach(function(f){rows=rows.filter(function(r){return r[f[0]]===f[1];});});
      return Promise.resolve({data:rows,error:null}).then(res);
    }
  };
  return api;
}
window.__TP_SUPABASE_MOCK = {
  rpc:function(naam){window.__RPCS=window.__RPCS||[];window.__RPCS.push(naam);
    if(naam==='tp_winkelvraag_gezien')(window.__DB.winkelvragen||[]).forEach(function(r){r.nieuw_voor_partner=false;});
    return Promise.resolve({data:null,error:null});},
  from:_q,
  storage:{ from:function(){ return { list:function(){return Promise.resolve({data:[],error:null});},
    upload:function(){return Promise.resolve({error:null});},
    createSignedUrl:function(){return Promise.resolve({data:{signedUrl:'x'},error:null});} };}},
  auth:{
    getSession:function(){return Promise.resolve({data:{session:window.__MOCK.session}});},
    signInWithPassword:function(){return Promise.resolve(window.__MOCK.signin);},
    signOut:function(){return Promise.resolve({});}
  }
};
"""

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

    # ===== AM: deals + taken + contacten =====
    pg.evaluate("""window.__DB.tappunten=[
      {snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:2400}},
      {snelstart:'kl-2',name:'Deventer',email:null,geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-2',name:'Deventer',jaaromzet:900}}];
      window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.taken=[{id:'t0',titel:'Bestaande taak',am_id:'am-1',tappunt_snelstart:null,deadline:'2026-07-25',klaar:false}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"marian@tp.nl")
    ck("dashboard: taken-tegel toont 1 open", '1' in (pg.text_content('[data-test=tile-taken]') or ''))

    # Deals
    pg.click('nav >> text=Deals'); pg.wait_for_timeout(500)
    pg.select_option('[data-test=deal-winkel]','kl-1')
    pg.fill('[data-test=deal-titel]','Tweede display')
    pg.fill('[data-test=deal-waarde]','1500')
    pg.click('[data-test=deal-toevoegen]'); pg.wait_for_timeout(500)
    ins=pg.evaluate("window.__INSERTS")
    ck("deal toegevoegd -> insert (kl-1, 1500)", any(i[0]=='deals' and i[1]['tappunt_snelstart']=='kl-1' and i[1]['waarde']==1500 for i in ins))
    ck("deal in kolom Lead", pg.locator('[data-test=kolom-lead] >> [data-test=deal-kaart]').count()==1)
    ck("kolomtotaal Lead = 1.500", '1.500' in (pg.text_content('[data-test=totaal-lead]') or ''))
    pg.select_option('[data-test=deal-fase]','voorstel'); pg.wait_for_timeout(500)
    ck("fase-wijziging -> update + verschuift naar Voorstel",
       pg.locator('[data-test=kolom-voorstel] >> [data-test=deal-kaart]').count()==1 and
       pg.locator('[data-test=kolom-lead] >> [data-test=deal-kaart]').count()==0)
    # gewogen forecast: 1.500 in voorstel (30%) -> € 450
    ck("gewogen forecast = € 450 (1.500 × 30%)", '450' in (pg.text_content('[data-test=forecast-gewogen]') or ''))
    # won/lost-reden: deal afsluiten en de reden vastleggen (CRM)
    pg.select_option('[data-test=deal-fase]','verloren'); pg.wait_for_timeout(500)
    ck("verloren-deal toont reden-veld", pg.locator('[data-test^=deal-reden-]').count()==1)
    ck("win-rate 0% (1 verloren, 0 gewonnen)", '0%' in (pg.text_content('[data-test=forecast-winrate]') or ''))
    pg.fill('[data-test^=deal-reden-]','Te duur gevonden'); pg.locator('[data-test^=deal-reden-]').blur(); pg.wait_for_timeout(500)
    upd=pg.evaluate("window.__UPDATES")
    ck("reden -> update deals.reden", any(u[0]=='deals' and u[1].get('reden')=='Te duur gevonden' for u in upd))

    # Taken
    pg.click('nav >> text=Taken'); pg.wait_for_timeout(500)
    ck("AM ziet bestaande open taak", pg.locator('[data-test=taak-item]').count()==1)
    ck("AM heeft GEEN AM-keuzeveld (taak is voor zichzelf)", pg.locator('[data-test=taak-am]').count()==0)
    pg.fill('[data-test=taak-titel]','Bel Deventer over voorraad')
    pg.click('[data-test=taak-toevoegen]'); pg.wait_for_timeout(500)
    ins=pg.evaluate("window.__INSERTS")
    ck("nieuwe taak -> insert met eigen am_id", any(i[0]=='taken' and i[1]['am_id']=='am-1' and 'Deventer' in i[1]['titel'] for i in ins))
    ck("2 open taken", pg.locator('[data-test=taak-item]').count()==2)
    pg.locator('[data-test=taak-item]:has-text("Bestaande taak") >> [data-test=taak-check]').click(); pg.wait_for_timeout(500)
    upd=pg.evaluate("window.__UPDATES")
    ck("afvinken -> update klaar=true", any(u[0]=='taken' and u[1].get('klaar')==True for u in upd))
    ck("1 open over + 1 afgerond", pg.locator('[data-test=taak-item]').count()==1 and pg.locator('[data-test=taak-klaar]').count()==1)

    # Contacten op winkelpagina
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(400)
    pg.click('[data-test=tappunt-rij]:has-text("Zwolle")'); pg.wait_for_timeout(500)
    pg.click('[data-test=contact-nieuw]')
    pg.fill('[data-test=contact-naam]','Anja de Vries')
    pg.click('[data-test=contact-opslaan]'); pg.wait_for_timeout(500)
    ins=pg.evaluate("window.__INSERTS")
    ck("contact toegevoegd -> insert bij kl-1", any(i[0]=='contacten' and i[1]['tappunt_snelstart']=='kl-1' and i[1]['naam']=='Anja de Vries' for i in ins))
    ck("contact in de lijst", pg.locator('[data-test=contact-item]').count()==1)
    ck("AM heeft verwijderknop", pg.locator('[data-test=contact-verwijder]').count()==1)
    pg.click('[data-test=contact-verwijder]'); pg.wait_for_timeout(200)
    pg.click('[data-test=contact-verwijder]'); pg.wait_for_timeout(400)  # 2e klik = bevestigen
    dels=pg.evaluate("window.__DELETES")
    ck("verwijderen -> delete-call", any(d[0]=='contacten' for d in dels))
    uitloggen(pg)

    # ===== KANTOOR: taak toewijzen aan AM =====
    pg.evaluate("""window.__MOCK.signin={data:{user:{id:'u-staff',email:'kantoor@tp.nl',app_metadata:{role:'staff'}}},error:null};""")
    login(pg,"kantoor@tp.nl")
    pg.click('[data-test=nav-taken]'); pg.wait_for_timeout(500)
    ck("kantoor heeft AM-keuzeveld", pg.locator('[data-test=taak-am]').count()==1)
    pg.fill('[data-test=taak-titel]','Rapport Q3 opleveren')
    pg.select_option('[data-test=taak-am]','am-1')
    pg.click('[data-test=taak-toevoegen]'); pg.wait_for_timeout(500)
    ins=pg.evaluate("window.__INSERTS")
    ck("kantoor wijst toe -> insert met am_id am-1", any(i[0]=='taken' and i[1]['am_id']=='am-1' and 'Rapport' in i[1]['titel'] for i in ins))
    uitloggen(pg)

    # ===== PARTNER: geen Deals/Taken, wel contacten (zonder verwijderknop) =====
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:2400}}];
      window.__DB.contacten=[{id:'c9',tappunt_snelstart:'kl-1',naam:'Anja de Vries',functie:'eigenaar',tel:null,email:null}];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    ck("partner: geen Deals-tab", pg.locator('nav >> text=Deals').count()==0)
    ck("partner: geen Taken-tab", pg.locator('nav >> text=Taken').count()==0)
    ck("partner: geen taken-tegel op dashboard", pg.locator('[data-test=tile-taken]').count()==0)
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(700)
    ck("partner ziet contactpersonen op eigen winkelpagina", pg.locator('[data-test=contact-item]').count()==1)
    ck("partner heeft GEEN verwijderknop", pg.locator('[data-test=contact-verwijder]').count()==0)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
