from playwright.sync_api import sync_playwright
from datetime import date, timedelta
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(800)
FUT=(date.today()+timedelta(days=20)).isoformat()
PAST=(date.today()-timedelta(days=5)).isoformat()
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.central=[{ns:'acties',data:[
        {id:'a-open',titel:'Zomeractie',omschrijving:'Doe mee',punten:5,
         materialen:'poster, flyers',artikelnrs:'#A102, #A103',bestelDeadline:'"""+FUT+"""',
         todo:'1 · Poster ophangen\\n2 · Social-post plaatsen',archived:false},
        {id:'a-dicht',titel:'Lenteactie',omschrijving:'',materialen:'flyer',bestelDeadline:'"""+PAST+"""',archived:false}]}];
      window.__MOCK.signin={data:{user:{id:'u-staff',email:'k@tp.nl',app_metadata:{role:'staff'}}},error:null};""")
    login(pg,"k@tp.nl")
    pg.click('nav >> text=Acties'); pg.wait_for_timeout(700)

    det=pg.locator('[data-test=actie-detail]').first
    ck("campagne-detailblok aanwezig", pg.locator('[data-test=actie-detail]').count()>=1)
    ck("materialen getoond", 'poster' in (pg.text_content('[data-test=detail-materialen]') or ''))
    ck("artikelnummers getoond", '#A102' in (pg.text_content('[data-test=detail-artikelnrs]') or ''))
    ck("open deadline: 'Bestel materialen vóór'", 'vóór' in (pg.locator('[data-test=detail-deadline]').first.text_content() or ''))
    ck("stappenplan: 2 stappen", pg.locator('[data-test=detail-stappen] ol li').count()==2)
    # gesloten deadline op de tweede actie
    txt=' '.join(pg.locator('[data-test=detail-deadline]').all_text_contents())
    ck("gesloten deadline getoond", 'gesloten' in txt.lower())

    # kantoor-formulier heeft de nieuwe velden
    ck("form-veld artikelnrs", pg.locator('[data-test=actie-artikelnrs]').count()==1)
    ck("form-veld deadline", pg.locator('[data-test=actie-deadline]').count()==1)
    ck("form-veld stappenplan", pg.locator('[data-test=actie-todo]').count()==1)

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
