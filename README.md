# gruppoaet.it — sito statico

Sito istituzionale di AET – Apparati Elettromeccanici e Telecomunicazioni S.r.l., ricostruito in HTML/CSS puro (senza WordPress né Elementor) nell'ottobre 2026.

- `site/` — il sito pubblicato: HTML, CSS, JS, immagini, PDF, firme email (`/firma-mail/`). È la document root di nginx.
- `nginx.conf` + `Dockerfile` — immagine `nginx:alpine` con redirect 301 dai vecchi URL WordPress/Polylang.
- `tools/` — generatore (Python + Jinja2) usato per produrre `site/` dai contenuti estratti dal vecchio sito (`tools/content/*.json`). Serve solo per rigenerare le pagine dopo una modifica a template o contenuti; a runtime non è usato.
- `form/` — micro-servizio Node per il form contatti (Resend → info@gruppoaet.it). Vedi `form/README.md`.

## Rigenerare il sito

```
pip install jinja2 pillow beautifulsoup4 lxml
AET_SRC_IMG=<cartella con le immagini originali> python3 tools/build.py
```

Le immagini già presenti in `site/assets/img/` non vengono toccate se esistono. Per modifiche di testo si può anche editare direttamente l'HTML in `site/`.

## Struttura URL

Italiano alla radice (`/storia/`, `/armamento/`, `/news/<slug>/`), inglese sotto `/en/` (`/en/history/`). I vecchi URL (`/en-gb/storia-copy/`, `/?p=123`, news alla radice) sono reindirizzati da nginx.
