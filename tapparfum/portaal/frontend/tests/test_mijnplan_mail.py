from playwright.sync_api import sync_playwright
URL="http://localhost:4173/"
R={"ok":0,"fail":0}
def ck(n,c): print(("OK " if c else "XX ")+n); R["ok" if c else "fail"]+=1
INIT=open("tests/test_fase4.py").read().split('INIT = r"""')[1].split('"""')[0]
def login(pg,email):
    pg.fill('input[type=email]',email); pg.fill('input[type=password]','x'); pg.click('button[type=submit]'); pg.wait_for_timeout(800)
def uitloggen(pg):
    pg.click('button:has-text("Uitloggen")'); pg.wait_for_timeout(400)

# Een .eml zoals Outlook hem exporteert — afzender is de klant (dir 'in').
EML = ("Message-ID: <abc-123@mail.test>\r\nDate: Mon, 20 Jul 2026 10:00:00 +0200\r\n"
       "From: Winkel Zwolle <a@a.nl>\r\nTo: am@tapparfum.nl\r\n"
       "Subject: Voorraad bijna op\r\nContent-Type: text/plain\r\n\r\n"
       "Hoi, de 50ml flesjes zijn bijna op. Kun je langskomen?\r\n")
eml_pad="/tmp/claude-0/-home-user-memeradar/b0dc4ae2-3376-5404-9da1-5b0364a4f411/scratchpad/test_mail.eml"
open(eml_pad,"w").write(EML)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path="/opt/pw-browsers/chromium")
    pg=b.new_context().new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)[:180]))
    pg.add_init_script(INIT); pg.goto(URL); pg.wait_for_timeout(400)

    # ===== PARTNER: Mijn plan toont t.be en t.goal met voortgang =====
    pg.evaluate("""window.__DB.tappunten=[{snelstart:'kl-1',name:'Zwolle',email:'a@a.nl',geblokkeerd:false,am_id:null,auth_user_id:'u-p',
      data:{snelstart:'kl-1',name:'Zwolle',email:'a@a.nl',contact:'Piet Jansen',liveDate:'2026-07-01',jaaromzet:6000,setup:{skipped:true},
        be:{inv:3950,rev:16.53,perWk:25,days:70,bottles:239},
        goal:{doel:15000,klanten:114,flWeek:19.7,flJaar:1026,flDag:2.8,refills:8},
        flesLog:[{d:'2026-07-10',n:100,src:'kassa'},{d:'2026-07-15',n:20,src:'kassa'}]}}];
      window.__MOCK.signin={data:{user:{id:'u-p',app_metadata:{}}},error:null};""")
    login(pg,"winkel@tp.nl")
    ck("partner-nav heeft Mijn plan", pg.locator('nav >> text=Mijn plan').count()==1)
    pg.click('nav >> text=Mijn plan'); pg.wait_for_timeout(500)
    ck("terugverdien-kaart: 120/239 flessen", '120 / 239' in (pg.text_content('[data-test=be-stand]') or ''))
    ck("jaardoel-kaart: 120/1026 flessen", '120 / 1026' in (pg.text_content('[data-test=goal-stand]') or ''))
    ck("streefdatum + tempo zichtbaar", '25 flessen per week' in (pg.text_content('[data-test=plan-be]') or ''))
    uitloggen(pg)

    # ===== AM: mail schrijven wordt gelogd + .eml-import koppelt =====
    pg.evaluate("""window.__DB.tappunten[0].auth_user_id=null; window.__DB.tappunten[0].am_id='am-1';
      window.__DB.accountmanagers=[{id:'am-1',naam:'Marian',auth_user_id:'u-am'}];
      window.__MOCK.signin={data:{user:{id:'u-am',app_metadata:{}}},error:null};""")
    login(pg,"am@tp.nl")
    pg.click('nav >> text=Bezoeken'); pg.wait_for_timeout(500)
    ck("mail-werkbalk aanwezig", pg.locator('[data-test=mailbalk]').count()==1)

    # compose: registreert in het logboek (dir 'uit', subject+body)
    pg.select_option('[data-test=mail-winkel]','kl-1'); pg.wait_for_timeout(150)
    pg.click('[data-test=mail-open]'); pg.wait_for_timeout(300)
    ck("compose vooringevuld (aan + aanhef)", (pg.input_value('[data-test=mail-aan]')=='a@a.nl')
       and 'Beste Piet' in (pg.input_value('[data-test=mail-bericht]') or ''))
    pg.fill('[data-test=mail-onderwerp]','Afspraak volgende week')
    pg.fill('[data-test=mail-bericht]','Beste Piet, ik kom dinsdag langs. Groet, Marian')
    pg.click('[data-test=mail-verstuur]'); pg.wait_for_timeout(600)
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    m=[e for e in d.get('logboek',[]) if e.get('type')=='mail']
    ck("mail gelogd met dir 'uit' + subject", len(m)==1 and m[0]['dir']=='uit' and m[0]['subject']=='Afspraak volgende week')

    # .eml-import: match op klant-mailadres -> dir 'in', dedupe op Message-ID
    pg.set_input_files('[data-test=eml-input]', eml_pad); pg.wait_for_timeout(700)
    ck("import-melding: 1 gekoppeld", '1 mail gekoppeld' in (pg.text_content('[data-test=eml-melding]') or ''))
    d=pg.evaluate("window.__UPSERTS.filter(u=>u[0]==='tappunten').slice(-1)[0][1]['data']")
    inm=[e for e in d.get('logboek',[]) if e.get('type')=='mail' and e.get('dir')=='in']
    ck("ontvangen mail in logboek (subject + snippet)", len(inm)==1 and inm[0]['subject']=='Voorraad bijna op'
       and '50ml' in inm[0].get('body',''))
    ck("Message-ID bewaard voor dedupe", inm[0].get('msgId')=='<abc-123@mail.test>')

    ck("geen pageerrors", len(errs)==0)
    for e in errs[:5]: print("   XX", e)
    b.close()
print(f"\n{R['ok']} geslaagd, {R['fail']} gefaald")
