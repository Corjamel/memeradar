// Mail-import (.eml) — 1-op-1 uit v71 (r.1357-1394): Outlook-berichten inlezen
// en automatisch aan de juiste winkel hangen op basis van het klant-mailadres.
//   afzender = klant       -> ↓ ontvangen (dir 'in')
//   klant in aan/cc        -> ↑ verstuurd (dir 'uit')
// Dedupe op Message-ID zodat dubbel importeren geen dubbele logregels geeft.

function _b64t(x) {
  try {
    const bin = typeof atob !== 'undefined' ? atob(String(x).replace(/\s+/g, '')) : ''
    try { return decodeURIComponent(escape(bin)) } catch (e) { return bin }
  } catch (e) { return '' }
}
function _qp(x) {
  x = String(x || '').replace(/=\r?\n/g, '').replace(/=([0-9A-Fa-f]{2})/g, (m, h) => String.fromCharCode(parseInt(h, 16)))
  try { return decodeURIComponent(escape(x)) } catch (e) { return x }
}
function _rfc2047(x) {
  return String(x || '').replace(/=\?[^?]+\?([BQbq])\?([^?]*)\?=/g,
    (m, enc, t) => (enc.toUpperCase() === 'B' ? _b64t(t) : _qp(t.replace(/_/g, ' '))))
}

export function parseEml(raw) {
  raw = String(raw || '')
  const ix = raw.search(/\r?\n\r?\n/)
  const head = ix < 0 ? raw : raw.slice(0, ix)
  const body = ix < 0 ? '' : raw.slice(ix).replace(/^\r?\n\r?\n?/, '')
  const H = {}
  let cur = ''
  head.split(/\r?\n/).forEach(l => {
    if (/^[ \t]/.test(l) && cur) { H[cur] += ' ' + l.trim() } else {
      const m = l.match(/^([\w-]+):\s*(.*)$/)
      if (m) { cur = m[1].toLowerCase(); H[cur] = (H[cur] ? H[cur] + ', ' : '') + m[2] }
    }
  })
  const strip = h => h.replace(/<style[\s\S]*?<\/style>/gi, ' ').replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
  const dec = (b, cte, isHtml) => {
    cte = String(cte || '').toLowerCase()
    let t = b
    if (cte.indexOf('base64') >= 0) t = _b64t(b)
    else if (cte.indexOf('quoted-printable') >= 0) t = _qp(b)
    return isHtml ? strip(t) : t
  }
  let txt = ''
  const ct = H['content-type'] || ''
  const bm = ct.match(/boundary="?([^";]+)"?/i)
  if (bm) {
    const esc2 = bm[1].replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const parts = body.split(new RegExp('--' + esc2))
    let plain = null, html = null
    parts.forEach(p => {
      const pi = p.search(/\r?\n\r?\n/)
      if (pi < 0) return
      const ph = p.slice(0, pi).toLowerCase()
      const pb = p.slice(pi).trim()
      const cte = (ph.match(/content-transfer-encoding:\s*([^\r\n;]+)/) || [])[1] || ''
      if (/content-type:\s*text\/plain/.test(ph) && plain == null) plain = dec(pb, cte, false)
      else if (/content-type:\s*text\/html/.test(ph) && html == null) html = dec(pb, cte, true)
    })
    txt = plain != null ? plain : (html || '')
  } else txt = dec(body, H['content-transfer-encoding'], /text\/html/i.test(ct))
  const adres = x => String(x || '').toLowerCase().match(/[\w.+-]+@[\w.-]+\.\w+/g) || []
  let at = ''
  const dt = H['date'] && new Date(H['date'])
  if (dt && !isNaN(dt)) at = dt.toISOString().slice(0, 10)
  return {
    from: adres(H['from']),
    to: adres(H['to']).concat(adres(H['cc'])),
    subject: _rfc2047(H['subject'] || '').trim() || '(geen onderwerp)',
    at: at || new Date().toISOString().slice(0, 10),
    msgId: String(H['message-id'] || '').trim(),
    snippet: String(txt).replace(/\s+/g, ' ').trim().slice(0, 220)
  }
}

/* Koppelt geparste mails aan winkels op mailadres. Puur: geeft de bijgewerkte
   kopieën terug ({ gewijzigd: [t2, ...], ok, dup, onbekend }); het wegschrijven
   doet de aanroeper via de tappunten-store (RLS bewaakt wie wat mag). */
export function koppelEmlAanWinkels(mails, tappunten) {
  const kopie = new Map()
  let ok = 0, dup = 0, onbekend = 0
  const uid = () => 'm-' + Math.random().toString(36).slice(2, 10)
  mails.forEach(m => {
    let matched = false
    tappunten.forEach(t => {
      const em = String(t.email || '').toLowerCase().trim()
      if (!em) return
      let dir = null
      if (m.from.indexOf(em) >= 0) dir = 'in'
      else if (m.to.indexOf(em) >= 0) dir = 'uit'
      if (!dir) return
      matched = true
      const t2 = kopie.get(t.snelstart) || { ...t, logboek: [...(t.logboek || [])] }
      if (m.msgId && t2.logboek.some(e => e.msgId === m.msgId)) { dup++; kopie.set(t.snelstart, t2); return }
      t2.logboek.unshift({
        id: uid(), at: m.at, type: 'mail', dir, msgId: m.msgId,
        subject: m.subject, body: m.snippet || '',
        txt: '✉️ ' + m.subject + (m.snippet ? ' — ' + m.snippet : ''),
        nextDate: '', nextDone: false
      })
      t2.logboek.sort((a, b) => (a.at < b.at ? 1 : -1))
      kopie.set(t.snelstart, t2)
      ok++
    })
    if (!matched) onbekend++
  })
  return { gewijzigd: [...kopie.values()], ok, dup, onbekend }
}
