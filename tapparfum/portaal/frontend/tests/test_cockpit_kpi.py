from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'},{id:'am-2',naam:'Kees',auth_user_id:'u-x'}];
      window.__DB.tappunten=[
        {snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:24000,statusManual:'stagneert',bestellingen:[{id:'b1',at:'2026-07-10',ref:'F1',totaal:1200,bron:'handmatig'}]}},
        {snelstart:'kl-2',name:'Deventer',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-2',name:'Deventer',jaaromzet:9000,statusManual:'stagneert',bestellingen:[{id:'b2',at:'2026-01-02',ref:'F2',totaal:400,bron:'handmatig'}]}},
        {snelstart:'kl-3',name:'Kampen',geblokkeerd:false,am_id:'am-2',data:{snelstart:'kl-3',name:'Kampen',jaaromzet:15000,statusManual:'top',bestellingen:[{id:'b3',at:'2026-07-20',ref:'F3',totaal:800,bron:'handmatig'}]}}];
      window.__MOCK.signin={data:{user:{id:'u-staff',email:'k@tp.nl',app_metadata:{role:'staff'}}},error:null};""")
    pg.fill('input[type=email]','k@tp.nl'); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(900)
    ck("accountmanagers-tegel = 2", pg.text_content('[data-test=tile-ams] .cijfer').strip()=='2')
    ck("stagneert-tegel = 2", pg.text_content('[data-test=tile-stagneert] .cijfer').strip()=='2')
    kpi=(pg.text_content('[data-test=bestel-kpi]') or '')
    ck("bestel-KPI inkoop dit jaar = 2.400", '2.400' in kpi)
    ck("bestel-KPI 2 bestellingen deze maand", '2' in kpi and 'deze maand' in kpi)
    ck("bestel-KPI 1 stil (60+ dgn)", '60+ dgn' in kpi)
    ck("aandachtslijst: 2 stagnerende winkels", pg.locator('[data-test=aandacht-rij]').count()==2)
    ck("aandacht-rij linkt naar heractiveren", '→ heractiveren' in (pg.text_content('[data-test=aandacht-rij]') or ''))
    # klik opent de winkelpagina (waar het heractiveer-blok staat)
    pg.locator('[data-test=aandacht-rij]', has_text='Zwolle').click(); pg.wait_for_timeout(700)
    ck("klik opent winkelpagina met heractiveer-blok", pg.locator('[data-test=heractiveer]').count()==1)
    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
