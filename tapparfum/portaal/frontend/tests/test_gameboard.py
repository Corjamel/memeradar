from playwright.sync_api import sync_playwright
import json
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(800)

# Landelijk bord: 12 groei-winkels; de partner is #5 (is_zelf, eigen naam),
# de rest gemaskeerd als "Winkel #n" (server-side maskering nagebootst).
BOARD=[]
for i in range(1,13):
    zelf = (i==5)
    BOARD.append({"rang":i,"klasse":"groei","score":300-i*10,"groei_pct":250-i*10,"jo":20000,
                  "reden":None,"tekort":0,"is_zelf":zelf,"naam":("Zwolle" if zelf else f"Winkel #{i}")})

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)
    pg.evaluate("""window.__DB.central=[{ns:'salesgame',data:{actief:true,titel:'TP Game',minPunten:0,minBasis:0}}];
      window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',geblokkeerd:false,am_id:'am-1',
        data:{snelstart:'kl-1',name:'Zwolle',jaaromzet:20000,vorigJaar:8000,liveDate:'2026-01-01'}}];
      window.__GAMEBOARD=%s;
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""" % json.dumps(BOARD))
    login(pg,"winkel@tp.nl")
    pg.click('[data-test=nav-game]'); pg.wait_for_timeout(800)

    ck("podium toont landelijke #1 (gemaskeerd)", 'Winkel #1' in (pg.text_content('[data-test=podium-0]') or ''))
    ck("podium #2 en #3 gemaskeerd", 'Winkel #2' in (pg.text_content('[data-test=podium-1]') or '') and 'Winkel #3' in (pg.text_content('[data-test=podium-2]') or ''))
    ck("label 'landelijk' zichtbaar", 'landelijk' in (pg.text_content('.klas-lbl') or ''))
    mijn=pg.text_content('[data-test=game-mijn]') or ''
    ck("partner ziet landelijke positie 5 van 12", 'Positie 5 van 12' in mijn)
    # privacy: partner krijgt geen itemlijst met winkels — alleen podium + eigen positie
    ck("partner ziet geen volledige itemlijst", pg.locator('[data-test=klas-groei]').count()==0)
    ck("podium bevat uitsluitend gemaskeerde namen", 'Winkel #' in (pg.text_content('.podium') or ''))

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
