from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(600)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__DB.tappunten=[
       {snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:8000,statusManual:'stagneert'}},
       {snelstart:'kl-2',name:'Deventer',geblokkeerd:false,am_id:'am-1',data:{snelstart:'kl-2',name:'Deventer',jaaromzet:20000,statusManual:'groeit'}}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"m@t.nl")
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(400)
    pg.locator('[data-test=tappunt-rij]', has_text='Zwolle').click(); pg.wait_for_timeout(700)
    ck("stagnerende winkel toont heractiveer-blok", pg.locator('[data-test=heractiveer]').count()==1)
    ck("4 stappen + 7 acties in de keuzelijst", pg.locator('[data-test=her-actie] option').count()==8)
    ck("voorraad-checklist-link aanwezig", 'voorraad-checklist' in (pg.text_content('[data-test=heractiveer]') or ''))
    pg.select_option('[data-test=her-actie]','Geuravond / proefactie ingepland'); pg.wait_for_timeout(100)
    pg.click('[data-test=her-vastleggen]'); pg.wait_for_timeout(500)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("actie -> t.react (v71-veld) met opvolgdatum", bool(d.get('react')) and d['react'][0]['actie']=='Geuravond / proefactie ingepland' and d['react'][0]['opvolg'])
    ck("react-historie zichtbaar", pg.locator('[data-test=her-rij]').count()==1)
    pg.click('[data-test=her-done-0]'); pg.wait_for_timeout(400)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    ck("afvinken -> react[0].done=true", d['react'][0]['done']==True)
    # niet-stagnerende winkel: geen blok
    pg.click('nav >> text=Winkels'); pg.wait_for_timeout(400)
    pg.locator('[data-test=tappunt-rij]', has_text='Deventer').click(); pg.wait_for_timeout(700)
    ck("groeiende winkel toont GEEN heractiveer-blok", pg.locator('[data-test=heractiveer]').count()==0)
    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
