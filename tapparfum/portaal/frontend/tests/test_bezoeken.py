from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(700)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[
        {snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle',email:'z@w.nl',logboek:[{id:'l1',at:new Date().toISOString().slice(0,10),type:'bezoek',txt:'Langs geweest',duurMin:45,nextDate:'2026-08-01',nextDone:false},{id:'l2',at:'2026-05-01',type:'mail',txt:'Mail gestuurd',dir:'uit'}]}},
        {snelstart:'kl-2',name:'Deventer',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-2',name:'Deventer',email:'d@w.nl',logboek:[{id:'l3',at:'2026-01-01',type:'telefoon',txt:'Gebeld'}]}}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"m@t.nl")
    pg.click('nav >> text=Bezoeken'); pg.wait_for_timeout(600)
    ck("KPI bezoeken deze maand = 1", (pg.locator('.kpi b').nth(0).text_content() or '').strip()=='1')
    ck("KPI open opvolgingen = 1", (pg.locator('.kpi b').nth(1).text_content() or '').strip()=='1')
    ck("bezoekritme: 2 winkels", pg.locator('[data-test=ritme-rij]').count()==2)
    ck("mail-de-klant links (2 winkels met e-mail)", pg.locator('[data-test=mail-klant]').count()==2)
    ck("netwerklog: 3 regels", pg.locator('[data-test=netlog-rij]').count()==3)
    pg.click('[data-test=filter-mail]'); pg.wait_for_timeout(300)
    ck("filter 'mail' -> 1 regel", pg.locator('[data-test=netlog-rij]').count()==1)
    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
