// Endpoint del form contatti di gruppoaet.it: riceve il POST JSON e invia l'email con Resend.
// Variabili d'ambiente: RESEND_API_KEY (obbligatoria), TO_EMAIL (default info@gruppoaet.it),
// FROM_EMAIL (mittente verificato su Resend, es. "Sito Gruppo AET <sito@gruppoaet.it>"), ALLOWED_ORIGINS (CSV), PORT.
import http from 'node:http';

const PORT = process.env.PORT || 3000;
const TO = process.env.TO_EMAIL || 'info@gruppoaet.it';
const FROM = process.env.FROM_EMAIL || 'Sito Gruppo AET <sito@gruppoaet.it>';
const ORIGINS = (process.env.ALLOWED_ORIGINS || 'https://gruppoaet.it,https://www.gruppoaet.it,https://aet.zerofloor.it').split(',');
const KEY = process.env.RESEND_API_KEY;

const hits = new Map(); // rate limit minimo per IP: 5 invii / 10 minuti
function limited(ip) {
  const now = Date.now(); const arr = (hits.get(ip) || []).filter(t => now - t < 600000);
  arr.push(now); hits.set(ip, arr); return arr.length > 5;
}
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

http.createServer(async (req, res) => {
  const origin = req.headers.origin || '';
  const cors = ORIGINS.includes(origin) ? origin : ORIGINS[0];
  res.setHeader('Access-Control-Allow-Origin', cors);
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Vary', 'Origin');
  if (req.method === 'OPTIONS') { res.writeHead(204); return res.end(); }
  if (req.method === 'GET' && req.url === '/health') { res.writeHead(200); return res.end('ok'); }
  if (req.method !== 'POST' || !req.url.startsWith('/api/contact')) { res.writeHead(404); return res.end(); }
  let body = ''; req.on('data', c => { body += c; if (body.length > 20000) req.destroy(); });
  req.on('end', async () => {
    try {
      const d = JSON.parse(body || '{}');
      const ip = (req.headers['x-forwarded-for'] || req.socket.remoteAddress || '').split(',')[0].trim();
      if (d.website) { res.writeHead(200, { 'Content-Type': 'application/json' }); return res.end('{"ok":true}'); } // honeypot
      if (limited(ip)) { res.writeHead(429); return res.end('{"error":"too many requests"}'); }
      const name = String(d.name || '').trim().slice(0, 120), email = String(d.email || '').trim().slice(0, 200);
      const subject = String(d.subject || '').trim().slice(0, 200), message = String(d.message || '').trim().slice(0, 5000);
      if (!name || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || !message || !d.privacy) { res.writeHead(400); return res.end('{"error":"invalid"}'); }
      if (!KEY) { res.writeHead(503); return res.end('{"error":"not configured"}'); }
      const html = `<p><strong>Nome:</strong> ${esc(name)}<br><strong>Email:</strong> ${esc(email)}<br><strong>Oggetto:</strong> ${esc(subject)}<br><strong>Lingua:</strong> ${esc(d.lang || '')}<br><strong>IP:</strong> ${esc(ip)}</p><p>${esc(message).replace(/\n/g, '<br>')}</p>`;
      const r = await fetch('https://api.resend.com/emails', {
        method: 'POST', headers: { Authorization: `Bearer ${KEY}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ from: FROM, to: [TO], reply_to: email, subject: `[gruppoaet.it] ${subject || 'Richiesta dal sito'} — ${name}`, html })
      });
      if (!r.ok) { console.error('resend', r.status, await r.text()); res.writeHead(502); return res.end('{"error":"send failed"}'); }
      res.writeHead(200, { 'Content-Type': 'application/json' }); res.end('{"ok":true}');
    } catch (e) { console.error(e); res.writeHead(500); res.end('{"error":"server"}'); }
  });
}).listen(PORT, () => console.log('gruppoaet-form on', PORT));
