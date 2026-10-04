# gruppoaet-form

Micro-servizio Node (zero dipendenze) che riceve il POST del form contatti e invia l'email con Resend.

Deploy su Coolify come seconda applicazione del progetto "Gruppo AET Web" (build pack Dockerfile, base directory `/form`, porta 3000).

Variabili d'ambiente:

- `RESEND_API_KEY` — chiave API Resend (obbligatoria)
- `TO_EMAIL` — destinatario, default `info@gruppoaet.it`
- `FROM_EMAIL` — mittente verificato su Resend, es. `Sito Gruppo AET <sito@gruppoaet.it>` (richiede il dominio verificato su Resend: record SPF/DKIM su Cloudflare)
- `ALLOWED_ORIGINS` — origini ammesse (CSV), default `https://gruppoaet.it,https://www.gruppoaet.it,https://aet.zerofloor.it`

Il sito statico chiama `/api/contact`: in `nginx.conf` sostituire il `return 503` con un `proxy_pass` verso questo servizio, oppure impostare nel form l'URL assoluto del servizio.
