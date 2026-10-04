/* Gruppo AET — menu mobile, sottomenu accessibili, invio form. Nessuna dipendenza. */
(function () {
  var toggle = document.querySelector('.nav-toggle'), nav = document.getElementById('nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.hasAttribute('data-open');
      if (open) { nav.removeAttribute('data-open'); } else { nav.setAttribute('data-open', ''); }
      toggle.setAttribute('aria-expanded', String(!open));
      toggle.querySelector('.nav-toggle__label').textContent = open ? toggle.dataset.open : toggle.dataset.close;
    });
  }
  document.querySelectorAll('.nav .has-sub > button').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var li = btn.parentNode, open = li.hasAttribute('data-open');
      document.querySelectorAll('.nav .has-sub[data-open]').forEach(function (o) { if (o !== li) { o.removeAttribute('data-open'); o.querySelector('button').setAttribute('aria-expanded', 'false'); } });
      if (open) { li.removeAttribute('data-open'); } else { li.setAttribute('data-open', ''); }
      btn.setAttribute('aria-expanded', String(!open));
    });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') document.querySelectorAll('.nav .has-sub[data-open]').forEach(function (o) { o.removeAttribute('data-open'); o.querySelector('button').setAttribute('aria-expanded', 'false'); });
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.nav')) document.querySelectorAll('.nav .has-sub[data-open]').forEach(function (o) { o.removeAttribute('data-open'); o.querySelector('button').setAttribute('aria-expanded', 'false'); });
  });

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
