/* Gruppo AET — menu, slider, carosello news, form. Nessuna dipendenza. */
(function () {
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* menu mobile e sottomenu */
  var toggle = document.querySelector('.nav-toggle'), nav = document.getElementById('nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.hasAttribute('data-open');
      if (open) nav.removeAttribute('data-open'); else nav.setAttribute('data-open', '');
      toggle.setAttribute('aria-expanded', String(!open));
      toggle.querySelector('.nav-toggle__label').textContent = open ? toggle.dataset.open : toggle.dataset.close;
    });
  }
  function closeSubs(except) { document.querySelectorAll('.nav .has-sub[data-open]').forEach(function (o) { if (o !== except) { o.removeAttribute('data-open'); o.querySelector('button').setAttribute('aria-expanded', 'false'); } }); }
  document.querySelectorAll('.nav .has-sub > button').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var li = btn.parentNode, open = li.hasAttribute('data-open'); closeSubs(li);
      if (open) li.removeAttribute('data-open'); else li.setAttribute('data-open', '');
      btn.setAttribute('aria-expanded', String(!open));
    });
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeSubs(); });
  document.addEventListener('click', function (e) { if (!e.target.closest('.nav')) closeSubs(); });

  /* slider a dissolvenza (hero e progetti) */
  document.querySelectorAll('[data-slider]').forEach(function (root) {
    var slides = Array.prototype.slice.call(root.querySelectorAll('.slide')), i = 0, timer = null;
    var delay = parseInt(root.dataset.autoplay || '0', 10), dots = root.querySelector('.slider__dots');
    if (slides.length < 2) return;
    if (dots) slides.forEach(function (_, k) { var li = document.createElement('li'), b = document.createElement('button'); b.type = 'button'; b.addEventListener('click', function () { show(k); restart(); }); li.appendChild(b); dots.appendChild(li); });
    function show(n) {
      i = (n + slides.length) % slides.length;
      slides.forEach(function (s, k) { if (k === i) s.setAttribute('data-active', ''); else s.removeAttribute('data-active'); });
      if (dots) dots.querySelectorAll('button').forEach(function (b, k) { if (k === i) b.setAttribute('aria-current', 'true'); else b.removeAttribute('aria-current'); });
    }
    function restart() { if (timer) clearInterval(timer); if (delay && !reduce) timer = setInterval(function () { show(i + 1); }, delay); }
    root.querySelector('.slider__btn--prev').addEventListener('click', function () { show(i - 1); restart(); });
    root.querySelector('.slider__btn--next').addEventListener('click', function () { show(i + 1); restart(); });
    root.addEventListener('mouseenter', function () { if (timer) clearInterval(timer); });
    root.addEventListener('mouseleave', restart);
    root.addEventListener('focusin', function () { if (timer) clearInterval(timer); });
    root.addEventListener('focusout', restart);
    show(0); restart();
  });

  /* carosello news a scorrimento */
  document.querySelectorAll('[data-carousel]').forEach(function (root) {
    var track = root.querySelector('.carousel__track');
    function step() { var first = track.firstElementChild; return first ? first.getBoundingClientRect().width + 30 : 300; }
    root.querySelector('.carousel__btn--prev').addEventListener('click', function () { track.scrollBy({ left: -step(), behavior: reduce ? 'auto' : 'smooth' }); });
    root.querySelector('.carousel__btn--next').addEventListener('click', function () { track.scrollBy({ left: step(), behavior: reduce ? 'auto' : 'smooth' }); });
  });

  /* form contatti */
  var form = document.getElementById('contact-form');
  if (form) {
    var status = form.querySelector('.form-status');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); return; }
      var btn = form.querySelector('button[type=submit]'); btn.disabled = true; status.textContent = '…'; status.removeAttribute('data-state');
      var data = {}; new FormData(form).forEach(function (v, k) { data[k] = v; });
      fetch(form.action, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(function () { status.textContent = form.dataset.ok; status.dataset.state = 'ok'; form.reset(); })
        .catch(function () { status.textContent = form.dataset.err; status.dataset.state = 'err'; })
        .then(function () { btn.disabled = false; });
    });
  }
})();
