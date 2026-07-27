from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c):
    print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(700)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:null,geblokkeerd:false,am_id:null,auth_user_id:'u-p',data:{snelstart:'kl-1',name:'Zwolle'}}];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    pg.click('nav >> text=Merk & Assets'); pg.wait_for_timeout(500)
    ck("merkwereld: 8 kaarten", pg.locator('[data-test=merkwereld-kaart]').count()==8)
    ck("materialen: 4 assets", pg.locator('[data-test=merk-asset]').count()==4)
    # Beeldlaag: productfoto's hier; de video's staan in de Academy (videotheek)
    ck("producten: 5 foto's", pg.locator('[data-test=merk-product] img').count()==5)
    ck("productfoto laadt echt", pg.evaluate("fetch('/assets/bodymist.jpg').then(r=>r.ok)"))
    ck("download-links op producten", pg.locator('[data-test=merk-product] a[download]').count()==5)
    ck("geen video's meer op merk", pg.locator('[data-test=concept-video]').count()==0)
    ck("brandbook aanwezig", 'Brandbook 2026' in (pg.text_content('body') or ''))
    ck("merkregels-tekst aanwezig", 'nooit onder de adviesprijs' in (pg.text_content('body') or ''))
    pg.locator('[data-test=merk-asset] button').first.click(); pg.wait_for_timeout(200)
    ck("download -> melding", 'volgt zodra' in (pg.text_content('[data-test=merk-melding]') or ''))
    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
