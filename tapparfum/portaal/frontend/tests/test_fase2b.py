from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1

# Mock-Supabase incl. Storage (voor documenten).
INIT = r"""
window.__DB = { tappunten: [], accountmanagers: [], berichten: [], agenda: [], winkelvragen: [] };
window.__UPSERTS=[]; window.__INSERTS=[]; window.__UPDATES=[]; window.__UPLOADS=[];
window.__FILES = {};   // prefix -> [namen]
window.__MOCK = { session:null, signin:{data:null,error:{message:'x'}} };
function _q(table){
  var api={ _f:[],
    select:function(){return api;}, order:function(){return api;}, limit:function(){return api;},
    eq:function(c,v){api._f.push([c,v]);return api;},
    insert:function(row){window.__INSERTS.push([table,row]);
      if(table==='agenda'){row=Object.assign({id:'ag-'+(window.__DB.agenda.length+1),status:'voorgesteld'},row);window.__DB.agenda.push(row);}
      if(table==='winkelvragen'){row=Object.assign({id:'wv-'+(window.__DB.winkelvragen.length+1),status:'open',antwoord:null,created_at:'2026-07-20'},row);window.__DB.winkelvragen.unshift(row);}
      return Promise.resolve({error:null});},
    upsert:function(row,o){window.__UPSERTS.push([table,row]);return Promise.resolve({error:null});},
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
  storage:{ from:function(bucket){ return {
    list:function(prefix,opts){ return Promise.resolve({data:(window.__FILES[prefix]||[]).map(function(n){return {name:n};}),error:null}); },
    upload:function(pad,f){ window.__UPLOADS.push(pad);
      var i=pad.indexOf('/');var pre=pad.slice(0,i);var naam=pad.slice(i+1);
      (window.__FILES[pre]=window.__FILES[pre]||[]).push(naam);
      return Promise.resolve({error:null}); },
    createSignedUrl:function(pad,ttl){ window.__lastSigned=pad; return Promise.resolve({data:{signedUrl:'https://signed.example/'+pad},error:null}); }
  };}},
  auth:{
    getSession:function(){return Promise.resolve({data:{session:window.__MOCK.session}});},
    signInWithPassword:function(c){return Promise.resolve(window.__MOCK.signin);},
    signOut:function(){return Promise.resolve({});}
  }
};
"""

def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x')
    pg.click('button[type=submit]'); pg.wait_for_timeout(500)
def uitloggen(pg):
    pg.click('button:has-text("Uitloggen")'); pg.wait_for_timeout(400)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT)
    pg.goto(URL); pg.wait_for_timeout(500)

    # ===== AM: bezoek plannen =====
    pg.evaluate("""window.__DB.tappunten=[
      {snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle'}},
      {snelstart:'kl-2',name:'Deventer',email:null,geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-2',name:'Deventer'}}];
      window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"marian@tp.nl")
    pg.click('nav >> text=Agenda'); pg.wait_for_timeout(500)
    pg.select_option('[data-test=winkel-select]','kl-1')
    pg.fill('[data-test=datum]','2026-08-01')
    pg.click('[data-test=plan-knop]'); pg.wait_for_timeout(500)
    ins=pg.evaluate("window.__INSERTS")
    ck("AM plant -> insert met winkel + eigen am_id", any(i[0]=='agenda' and i[1]['tappunt_snelstart']=='kl-1' and i[1]['am_id']=='am-1' for i in ins))
    ck("voorstel verschijnt in de lijst", pg.locator('[data-test=agenda-item]').count()==1)
    ck("status = wacht op winkel", 'wacht op winkel' in (pg.text_content('[data-test=status]') or ''))
    uitloggen(pg)

    # ===== PARTNER: accepteren =====
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle'}}];
      window.__DB.accountmanagers=[];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"zwolle@shop.nl")
    pg.click('nav >> text=Agenda'); pg.wait_for_timeout(500)
    ck("partner ziet het voorstel", pg.locator('[data-test=agenda-item]').count()==1)
    ck("partner heeft Accepteer/Wijs af-knoppen", pg.locator('[data-test=accepteer]').count()==1 and pg.locator('[data-test=wijs-af]').count()==1)
    ck("partner ziet GEEN plan-formulier", pg.locator('[data-test=plan-knop]').count()==0)
    pg.click('[data-test=accepteer]'); pg.wait_for_timeout(500)
    upd=pg.evaluate("window.__UPDATES")
    ck("accepteren -> update status=geaccepteerd", any(u[0]=='agenda' and u[1].get('status')=='geaccepteerd' for u in upd))
    ck("status in lijst nu geaccepteerd", 'geaccepteerd' in (pg.text_content('[data-test=status]') or ''))

    # ===== PARTNER: documenten op eigen winkelpagina =====
    pg.evaluate("window.__FILES['kl-1']=['1700000000_prijslijst.pdf']")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(700)   # partner -> direct detail
    ck("documentenblok zichtbaar op winkelpagina", pg.locator('[data-test=doc-item]').count()==1)
    ck("bestandsnaam netjes getoond (zonder tijdstempel)", 'prijslijst.pdf' in (pg.text_content('[data-test=doc-item]') or ''))
    # upload
    pg.set_input_files('[data-test=doc-upload]', {"name":"contract.pdf","mimeType":"application/pdf","buffer":b"dummy"})
    pg.wait_for_timeout(500)
    ups=pg.evaluate("window.__UPLOADS")
    ck("upload -> pad onder eigen winkel-map", len(ups)==1 and ups[0].startswith('kl-1/') and ups[0].endswith('_contract.pdf'))
    ck("lijst ververst na upload (2 documenten)", pg.locator('[data-test=doc-item]').count()==2)

    # ===== PARTNER: winkelvraag (retour) melden =====
    pg.click('nav >> text=Berichten'); pg.wait_for_timeout(500)
    ck("partner heeft meldformulier", pg.locator('[data-test=vraag-verstuur]').count()==1)
    pg.select_option('[data-test=vraag-type]','retour')
    pg.fill('[data-test=vraag-txt]','Fles lekt bij de dop, klant wil ruilen')
    pg.click('[data-test=vraag-verstuur]'); pg.wait_for_timeout(500)
    ins=pg.evaluate("window.__INSERTS")
    ck("melding -> insert winkelvraag voor eigen winkel", any(i[0]=='winkelvragen' and i[1]['tappunt_snelstart']=='kl-1' and i[1]['type']=='retour' for i in ins))
    ck("melding zichtbaar in 'Jouw meldingen'", pg.locator('[data-test=winkelvraag]').count()==1)
    uitloggen(pg)

    # ===== AM: afronden na acceptatie =====
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle'}}];
      window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"marian@tp.nl")
    pg.click('nav >> text=Agenda'); pg.wait_for_timeout(500)
    ck("AM ziet afronden-knop bij geaccepteerd bezoek", pg.locator('[data-test=afronden]').count()==1)
    pg.click('[data-test=afronden]'); pg.wait_for_timeout(500)
    upd=pg.evaluate("window.__UPDATES")
    ck("afronden -> update status=afgerond", any(u[0]=='agenda' and u[1].get('status')=='afgerond' for u in upd))

    # ===== AM: winkelvraag van zijn winkel beantwoorden =====
    pg.click('nav >> text=Berichten'); pg.wait_for_timeout(500)
    ck("AM ziet de melding uit zijn winkel", pg.locator('[data-test=winkelvraag]').count()==1)
    pg.fill('[data-test=vraag-antwoord-veld]','Nieuwe fles gaat vandaag mee, retour halen we op bij het bezoek.')
    pg.click('[data-test=vraag-antwoord-knop]'); pg.wait_for_timeout(500)
    upd=pg.evaluate("window.__UPDATES")
    ck("beantwoorden -> update status=beantwoord", any(u[0]=='winkelvragen' and u[1].get('status')=='beantwoord' for u in upd))
    ck("antwoord zichtbaar", pg.locator('[data-test=vraag-antwoord]').count()==1)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
