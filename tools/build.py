#!/usr/bin/env python3
"""Genera il sito statico gruppoaet.it in ../site da tools/content/*.json.
Uso: python3 tools/build.py   (eseguire dalla radice del repo)
L'output è HTML puro: il sito non dipende da questo script a runtime."""
import json, os, re, shutil, html, sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / 'tools'
OUT = ROOT / 'site'
SRC_IMG = Path(os.environ.get('AET_SRC_IMG', '/home/claude/aet/src/html-mirror/gruppoaet.it'))  # mirror con gli originali
SITE = json.load(open(TOOLS / 'content/site.json', encoding='utf-8'))
CONTENT = json.load(open(TOOLS / 'content/content.json', encoding='utf-8'))
S = SITE['strings']

# ---------- URL map ----------
slug2path, id2path, slug2entry = {}, {}, {}
for e in SITE['pages']:
    for lang in ('it', 'en'):
        slug = e[lang]; p = e['path_' + lang]
        slug2path[slug] = p; id2path[str(CONTENT[slug]['id'])] = p; slug2entry[slug] = (e, lang)

ASSET_IMG = {}  # original rel path -> /assets/img/name
def asset_name(orig):
    base = os.path.basename(orig)
    base = re.sub(r'-[a-z0-9]{40,}(?=\.)', '', base)            # hash elementor thumbs
    base = re.sub(r'-\d+x\d+(?=\.)', '', base)                  # dimensioni wp
    base = re.sub(r'-scaled(?=\.)', '', base)
    base = re.sub(r'-e\d{10,}(?=\.)', '', base)
    base = base.lower().replace(' ', '-').replace('_', '-')
    base = re.sub(r'[^a-z0-9.\-]', '', base)
    return base

def image(orig, maxw=1600, quality=82):
    """Copia (e ridimensiona) un'immagine del vecchio sito in assets/img, restituisce il path web."""
    if not orig: return None
    orig = re.sub(r'^(\.\./)+', '', orig)
    if orig in ASSET_IMG: return ASSET_IMG[orig]
    src = SRC_IMG / orig
    if not src.exists():
        print('  ! immagine mancante', orig); return None
    name = asset_name(orig)
    dst = OUT / 'assets/img' / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    ext = dst.suffix.lower()
    if ext in ('.jpg', '.jpeg', '.webp', '.png'):
        im = Image.open(src)
        if ext == '.png' or im.width <= maxw:
            if not dst.exists(): shutil.copy(src, dst)
        else:
            if not dst.exists():
                im = im.convert('RGB'); im.thumbnail((maxw, maxw * 3))
                im.save(dst, quality=quality, optimize=True)
    else:
        if not dst.exists(): shutil.copy(src, dst)
    ASSET_IMG[orig] = '/assets/img/' + name
    return ASSET_IMG[orig]

def doc(orig):
    orig = re.sub(r'^(\.\./)+', '', orig)
    name = os.path.basename(orig)
    dst = OUT / 'assets/docs' / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    src = SRC_IMG / orig
    if src.exists() and not dst.exists(): shutil.copy(src, dst)
    return '/assets/docs/' + name

def rewrite_href(h):
    if not h: return h
    h = html.unescape(h).replace('%3F', '?')
    if h.startswith(('mailto:', 'tel:', '#')): return h
    m = re.search(r'\?p=(\d+)', h)
    if m and m.group(1) in id2path: return id2path[m.group(1)]
    if '.pdf' in h.lower(): return doc(h)
    if 'wp-content/uploads' in h:
        im = image(h); return im or h
    h2 = re.sub(r'^https?://(www\.)?gruppoaet\.it', '', h)
    h2 = re.sub(r'^(\.\./)+', '/', h2)
    if not h2.startswith('/') and not h2.startswith('http'): h2 = '/' + h2
    h2 = re.sub(r'/index\.html$', '/', h2)
    m = re.match(r'^/(en-gb/)?([a-z0-9\-]+)/?$', h2)
    if m and m.group(2) in slug2path: return slug2path[m.group(2)]
    if h2 == '/': return '/'
    if h.startswith('http'): return h
    return h2

TAG_WHITELIST = {'p','ul','ol','li','strong','b','em','i','a','br','h3','h4','h5','table','thead','tbody','tr','th','td','blockquote','u','sup','sub'}
def clean_html(fragment):
    """Riduce l'HTML di Elementor a markup semantico pulito."""
    from bs4 import BeautifulSoup
    s = BeautifulSoup(fragment, 'lxml')
    body = s.body or s
    for t in body.find_all(True):
        if t.name in ('script','style','iframe'): t.decompose(); continue
        if t.name == 'a':
            href = rewrite_href(t.get('href'))
            t.attrs = {'href': href}
            if href and href.startswith('http') and 'gruppoaet.it' not in href: t.attrs.update({'target':'_blank','rel':'noopener'})
        elif t.name == 'img':
            src = image(t.get('src') or t.get('data-src')); t.attrs = {'src': src, 'alt': t.get('alt',''), 'loading':'lazy'}
        elif t.name in TAG_WHITELIST:
            if t.name in ('b',): t.name = 'strong'
            if t.name in ('i',): t.name = 'em'
            t.attrs = {}
        else:
            t.unwrap()
    out = ''.join(str(c) for c in body.contents)
    out = re.sub(r'<p>\s*(&nbsp;|\u200b|\s)*</p>', '', out)
    out = out.replace('\u200b', '').replace('&nbsp;', ' ')
    out = re.sub(r'\s+', ' ', out).strip()
    # testo nudo senza <p> -> incapsula
    if out and not out.startswith('<'): out = '<p>' + out + '</p>'
    return out

def titlecase(s):
    """Titoli del vecchio sito sono in MAIUSCOLO: li porto in sentence case preservando sigle."""
    if s != s.upper() or len(s) < 4: return s
    keep = {'AET','ACC-M','ISO','UNI','EN','SOA','SSE','PCO','MT','F.M.','TVCC','EAV','RFI','AV','TE','ETS','UNI','ELITE','SUVAL','SAEL','A.E.T.','PLART','ANIE','ASSIFER','OHSAS','TAV'}
    words = s.lower().split(' ')
    res = []
    for i, w in enumerate(words):
        W = w.upper()
        core = re.sub(r'[^\w\.-]', '', W)
        if core in keep or re.fullmatch(r'[A-Z]\d+', core) or re.fullmatch(r'\d+', core): res.append(W if core in keep else w.upper())
        elif i == 0: res.append(w[:1].upper() + w[1:])
        else:
            # nomi propri frequenti
            if w.strip(',.:') in ('napoli','lecce','milano','torino','aversa','piscinola','capodichino','alifana','circumvesuviana','circumflegrea','cumana','vesuviane','flegree','vomero','volla','afragola','giugliano','sorrento','giorgio','san','poggioreale','casoria','melito','scampia','montesanto','piave','soccavo','mergellina','municipio','mostra','comasina','maciachini','stabia','castellammare','annunziata','torre','italia','puglia','campania','surbo','borsa','italiana','salvatore','paliotto','steel','beton','suval','milano','lecce'):
                res.append(w[:1].upper() + w[1:])
            else: res.append(w)
    out = ' '.join(res)
    out = re.sub(r'([–-]) ([a-z])', lambda m: m.group(1)+' '+m.group(2).upper(), out)
    out = re.sub(r'(?<=\()([a-z])', lambda m: m.group(1).upper(), out)
    return out

# ---------- blocchi -> sezioni ----------
ICON_PREFIX = ('tower','electric-panel','semaphore','electric','lightbulb','battery','ventilation','air-conditioner','fire-extinguisher','fire-sensor','security-camera','online-meeting','railroad','processor-new','building','link')
def is_icon(src): return any(os.path.basename(src).startswith(p) for p in ICON_PREFIX) and 'thumbs' in src
def is_logo(src): return 'logo' in os.path.basename(src).lower() or os.path.basename(src).lower() in ('icmspa.png','iterga.jpeg','salcefgroup.png','costruirespa.png')

def group_blocks(blocks):
    """Trasforma la sequenza piatta di widget in sezioni semantiche."""
    out = []; i = 0; n = len(blocks)
    def t(k): return blocks[k]['t'] if k < n else None
    while i < n:
        b = blocks[i]; k = b['t']
        # tripla foto + titolo + testo ripetuta -> galleria di schede
        if k == 'img' and not is_icon(b['src']) and not is_logo(b['src']) and t(i+1) == 'h' and (t(i+2) in ('txt', 'h', 'img', None)):
            cards = []; j = i
            while j < n and t(j) == 'img' and not is_icon(blocks[j]['src']) and not is_logo(blocks[j]['src']) and t(j+1) == 'h':
                desc = ''
                if t(j+2) == 'txt': desc = blocks[j+2]['html']; step = 3
                else: step = 2
                cards.append({'img': blocks[j]['src'], 'alt': blocks[j].get('alt',''), 'title': blocks[j+1]['text'], 'desc': desc}); j += step
            if len(cards) >= 2:
                out.append({'t': 'cards', 'list': cards}); i = j; continue
        # icona + testo ripetuti -> lista con icone
        if k == 'img' and is_icon(b['src']) and t(i+1) == 'txt':
            items = []; j = i
            while j < n and t(j) == 'img' and is_icon(blocks[j]['src']) and t(j+1) == 'txt':
                items.append({'icon': blocks[j]['src'], 'text': blocks[j+1]['html']}); j += 2
            out.append({'t': 'iconlist', 'list': items}); i = j; continue
        # loghi consecutivi -> parete loghi
        if k == 'img' and is_logo(b['src']):
            items = []; j = i
            while j < n and t(j) == 'img' and is_logo(blocks[j]['src']):
                items.append(blocks[j]); j += 1
            out.append({'t': 'logos', 'list': items}); i = j; continue
        # immagine singola che non è hero -> figura
        if k == 'img':
            out.append({'t': 'figure', 'img': b['src'], 'alt': b.get('alt',''), 'caption': b.get('caption'), 'href': b.get('href')}); i += 1; continue
        if k == 'iconbox':
            items = []; j = i
            while j < n and t(j) == 'iconbox':
                items.append(blocks[j]); j += 1
            out.append({'t': 'downloads', 'list': items}); i = j; continue
        if k == 'carousel':
            out.append({'t': 'gallery', 'list': [x for x in b['items'] if x.get('src')]}); i += 1; continue
        out.append(b); i += 1
    return out

# sfondi delle slide (dal CSS Elementor della home)
import glob
SLIDE_BG = {}
for f in glob.glob(str(SRC_IMG / 'wp-content/uploads/elementor/css/post-*.css*')):
    for key, url in re.findall(r'repeater-item-([a-z0-9]+) \.swiper-slide-bg\{[^}]*background-image:url\(([^)]+)\)', open(f, encoding='utf-8', errors='ignore').read()):
        SLIDE_BG[key] = 'wp-content/uploads/' + re.sub(r'^(\.\./)+', '', url.strip('"\''))

# ---------- rendering ----------
env = Environment(loader=FileSystemLoader(str(TOOLS / 'templates')), autoescape=select_autoescape(['html']), trim_blocks=True, lstrip_blocks=True)
env.filters['image'] = image
env.filters['clean'] = clean_html
env.filters['titlecase'] = lambda x: x
env.filters['clean_href'] = rewrite_href

def nav_for(lang):
    items = []
    for it in SITE['nav'][lang]:
        if 'children' in it:
            ch = []
            for label, to in it['children']:
                if to == '@wb': ch.append({'label': label, 'href': SITE['whistleblowing_portal'], 'ext': True})
                else: ch.append({'label': label, 'href': path_for(to, lang)})
            items.append({'label': it['label'], 'children': ch})
        else: items.append({'label': it['label'], 'href': path_for(it['to'], lang)})
    return items

def path_for(it_slug, lang):
    for e in SITE['pages']:
        if e['it'] == it_slug: return e['path_' + lang]
    raise KeyError(it_slug)

def write(path, htmltext):
    p = OUT / path.lstrip('/') / 'index.html'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(htmltext, encoding='utf-8')

def posts_for(lang):
    ps = [(e, CONTENT[e[lang]]) for e in SITE['pages'] if e['kind'] == 'post']
    ps.sort(key=lambda x: x[1]['date'], reverse=True)
    res = []
    for e, c in ps:
        title = c['wp_title']
        datetxt = next((re.sub('<[^>]+>','',b['html']).strip() for b in c['blocks'] if b['t'] == 'txt' and re.fullmatch(r'\s*\d{1,2} \w+ \d{4}\s*', re.sub('<[^>]+>','',b['html']))), None)
        res.append({'path': e['path_' + lang], 'title': title, 'date': c['date'][:10], 'datetxt': datetxt, 'excerpt': c['excerpt'], 'thumb': image(c['thumb']) if c['thumb'] else None})
    return res

import hashlib
def _v(rel):
    f = OUT / rel
    return hashlib.md5(f.read_bytes()).hexdigest()[:8] if f.exists() else '1'
def base_ctx(entry, lang):
    other = 'en' if lang == 'it' else 'it'
    return {'v_css': _v('assets/css/site.css'), 'v_fonts': _v('assets/css/fonts.css'), 'v_js': _v('assets/js/site.js'),'S': S[lang], 'site': SITE, 'lang': lang, 'nav': nav_for(lang), 'alt_href': entry['path_' + other],
            'path': entry['path_' + lang], 'canonical': SITE['domain'] + entry['path_' + lang],
            'legal_path': path_for('dati-societari', lang), 'privacy_path': path_for('privacy-policy-2', lang),
            'cookie_path': path_for('cookie-policy', lang), 'projects_path': path_for('progetti-in-corso', lang), 'contact_path': path_for('contatti', lang), 'news_path': path_for('news', lang),
            'footer_links': [(l, path_for(s, lang)) for l, s in (
                [('Armamento','armamento'),('Opere civili','opere-civili'),('Progetti in corso','progetti-in-corso'),('Progetti completati','progetti-completati'),('Il gruppo','il-gruppo')] if lang=='it' else
                [('Track systems','armamento'),('Civil works','opere-civili'),('Ongoing projects','progetti-in-corso'),('Completed projects','progetti-completati'),('The group','il-gruppo')])],
            'footer_logos': [(image(p), a) for p, a in SITE['footer_logos']],
            'logo_white': image('wp-content/uploads/2022/10/logo_gruppoaet_500_500-300x300.webp'), 'logo_blue': '/assets/img/logo-aet-group.png'}

def page_title_from_blocks(c):
    hs = [b for b in c['blocks'] if b['t'] == 'h']
    return hs[0]['text'] if hs else c['wp_title']

def build():
    if (OUT / 'assets/img').exists():
        for f in (OUT / 'assets/img').iterdir():
            if f.name not in ('logo-aet-group.png', 'flag-gb.svg', 'flag-it.svg'): f.unlink()
    for e in SITE['pages']:
        for lang in ('it', 'en'):
            c = CONTENT[e[lang]]; ctx = base_ctx(e, lang)
            blocks = list(c['blocks'])
            kind = e['kind']
            if kind == 'home':
                sl = [b for b in blocks if b['t'] == 'slides']
                def mk(slides, maxw):
                    return [{'heading': x['heading'], 'desc': x['desc'], 'btn': x['btn'], 'href': rewrite_href(x['href']), 'bg': image(SLIDE_BG.get((x['key'] or '').replace('elementor-repeater-item-', '')), maxw)} for x in slides]
                ctx.update({'hero_slides': mk(sl[0]['slides'], 1920), 'project_slides': mk(sl[1]['slides'], 1920),
                            'posts': posts_for(lang)[:5],
                            'areas': [{'icon': image(blocks[i]['src']), 'title': blocks[i+1]['text'], 'text': blocks[i+2]['html'], 'href': rewrite_href(blocks[i+3]['href']), 'btn': blocks[i+3]['text']} for i in range(1, 12, 4)],
                            'news_title': next((b['text'] for b in blocks if b['t'] == 'h' and b['level'] == 'h2' and 'NEWS' in b['text'].upper()), S[lang]['latest_news'])})
                ctx['title'] = 'Gruppo AET – Apparati Elettromeccanici e Telecomunicazioni'
                ctx['desc'] = S[lang]['about']; ctx['hero'] = ctx['hero_slides'][0]['bg']
                write(e['path_' + lang], env.get_template('home.html').render(**ctx)); continue
            # hero: prima immagine + primo titolo
            hero = None
            if blocks and blocks[0]['t'] == 'img' and not is_icon(blocks[0]['src']) and not is_logo(blocks[0]['src']):
                hero = image(blocks.pop(0)['src'], 1920)
            title = c['wp_title']
            if blocks and blocks[0]['t'] == 'h':
                title = blocks.pop(0)['text']
            # per i post: la data è il primo txt dopo il titolo
            datetxt = None
            if kind == 'post' and blocks and blocks[0]['t'] == 'txt' and re.fullmatch(r'\s*\d{1,2} \w+ \d{4}\s*', re.sub('<[^>]+>', '', blocks[0]['html'])):
                datetxt = re.sub('<[^>]+>', '', blocks.pop(0)['html']).strip()
            # titolo ripetuto subito dopo (es. STORIA / STORIA DELLA SOCIETÀ) resta come h2 di sezione
            sections = group_blocks(blocks)
            ctx.update({'hero': hero, 'title': title, 'page_title': title + ' – Gruppo AET', 'sections': sections, 'datetxt': datetxt, 'date': c['date'][:10],
                        'desc': c['excerpt'] or next((re.sub('<[^>]+>', '', b['html'])[:160] for b in blocks if b['t'] == 'txt'), S[lang]['about'])})
            if kind == 'news': ctx['posts'] = posts_for(lang)
            if kind == 'contact':
                ctx['offices'] = SITE['offices']
                ctx['maps'] = [b['src'] for b in blocks if b['t'] == 'map']
                ctx['company_line'] = next((b['html'] for b in blocks if b['t'] == 'txt' and 'IVA' in b['html'].upper() and 'REA' in b['html'].upper()), None)
            tpl = {'page': 'page.html', 'post': 'post.html', 'news': 'news.html', 'contact': 'contact.html'}[kind]
            write(e['path_' + lang], env.get_template(tpl).render(**ctx))
    # 404
    for lang in ('it',):
        ctx = base_ctx(SITE['pages'][0], lang); ctx.update({'title': 'Pagina non trovata – Gruppo AET', 'desc': ''})
        (OUT / '404.html').write_text(env.get_template('404.html').render(**ctx), encoding='utf-8')
    # sitemap + robots
    urls = [SITE['domain'] + e['path_' + l] for e in SITE['pages'] for l in ('it', 'en')]
    (OUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(f'  <url><loc>{u}</loc></url>' for u in urls) + '\n</urlset>\n', encoding='utf-8')
    (OUT / 'robots.txt').write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE['domain']}/sitemap.xml\n", encoding='utf-8')
    print('pagine generate:', len(urls), '| immagini:', len(ASSET_IMG))

if __name__ == '__main__':
    build()
