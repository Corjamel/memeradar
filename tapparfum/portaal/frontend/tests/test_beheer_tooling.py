from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
import os
open("/tmp/tp_backup.json","w").write('{"_tp":"portaal-backup","at":"2026-01-01","instellingen":{"margeFactor":2.5,"shopUrl":"https://hersteld.example","modules":{"game":false,"kassa":true,"producten":true},"b2bApi":{"url":"https://b2b.hersteld","actief":true},"flesMaten":[{"m":"30ml","p":9}]}}')
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:null,data:{snelstart:'kl-1',name:'Zwolle'}}];
      window.__MOCK.signin={data:{user:{id:'u-staff',email:'k@tp.nl',app_metadata:{role:'staff'}}},error:null};""")
    pg.fill('input[type=email]','k@tp.nl'); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(800)
    pg.click('nav >> text=Beheer'); pg.wait_for_timeout(400)
    pg.click('[data-test=tab-instellingen]'); pg.wait_for_timeout(300)
    # B2B-koppeling opslaan
    pg.fill('[data-test=inst-b2b-url]','https://b2b.test'); pg.check('[data-test=inst-b2b-actief]')
    pg.click('[data-test=inst-opslaan]'); pg.wait_for_timeout(500)
    up=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='central' && u[1]['ns']==='b2bApi').slice(-1)[0][1]['data']")
    ck("B2B-koppeling opgeslagen (url + actief)", up.get('url')=='https://b2b.test' and up.get('actief')==True)
    # Back-up herstellen
    pg.click('[data-test=tab-avg]'); pg.wait_for_timeout(300)
    ck("herstel-knop aanwezig", pg.locator('[data-test=backup-herstel]').count()==1)
    pg.set_input_files('[data-test=backup-herstel]','/tmp/tp_backup.json'); pg.wait_for_timeout(700)
    marge=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='central' && u[1]['ns']==='margeFactor').slice(-1)[0][1]['data']")
    shop=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='central' && u[1]['ns']==='shopUrl').slice(-1)[0][1]['data']")
    ck("herstel zet margeFactor terug (2.5)", float(marge)==2.5)
    ck("herstel zet bestelportaal-URL terug", 'hersteld' in str(shop))
    ck("herstel-bevestiging getoond", 'hersteld' in (pg.text_content('body') or '').lower())
    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
