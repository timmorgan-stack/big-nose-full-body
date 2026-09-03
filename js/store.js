/* Big Nose Full Body — demo store engine (cart in localStorage).
   Catalogue comes from data/catalog.json via the generated data/catalog.js (window.BNFB_CATALOG).
   Demo only: no server, no real payments. */
window.BNFB = (function () {
  'use strict';

  var CATS = {
    sparkling: { label: 'Sparkling',          color: '#b8891c' },
    white:     { label: 'White',              color: '#c2a12a' },
    rose:      { label: 'Rosé',               color: '#d4607f' },
    orange:    { label: 'Orange & Beyond',    color: '#c96a1f' },
    red:       { label: 'Red',                color: '#950951' },
    sake:      { label: 'Sake & Cider',       color: '#3f5b8c' },
    fortified: { label: 'Fortified & Dessert',color: '#6b3fa0' },
    half:      { label: 'Half Bottles',       color: '#7a6a55' },
    alt:       { label: 'Boxes, Cans & Cartons', color: '#2f7d6b' },
    kosher:    { label: 'Kosher',             color: '#1f5f8b' },
    dealc:     { label: 'De-Alcoholized',     color: '#4a7c3f' },
    gift:      { label: 'Gift Cards',         color: '#17120e' },
    reserve:   { label: 'Reserve List',       color: '#6d0339' }
  };

  var TAGS = {
    reserve: 'Reserve List', organic: 'Organic', biodynamic: 'Biodynamic', sustainable: 'Sustainable',
    vegan: 'Vegan', natural: 'Natural', 'minimal-sulfur': 'Minimal Sulfur',
    'no-added-sulfur': 'No Added Sulfur', unoaked: 'Unoaked', kosher: 'Kosher',
    orange: 'Orange / Skin Contact', 'skin-contact': 'Skin Contact', 'pet-nat': 'Pét-Nat',
    'off-dry': 'Off Dry', new: 'New Arrival'
  };

  var FEED = (window.BNFB_CATALOG && window.BNFB_CATALOG.works) || [];
  var WINES = FEED.map(function (w) {
    return {
      id: w.id, ref: w.ref || w.id, name: w.title, cat: CATS[w.category] ? w.category : 'red',
      origin: w.place || '', price: +w.price || 0, tags: w.tagKeys || [], score: w.score || '',
      desc: w.description || '', pairings: w.pairings || '', size: w.size || '',
      image: (w.image && (w.image.thumb || w.image.large)) || '', featured: !!w.featured,
      /* a Reserve-List bottle the shop keeps in the cellar: ask at the counter, not orderable online */
      cellarOnly: !!w.cellarOnly,
      /* -1 = open (never runs out); 0 = sold out; n = bottles on the shelf */
      stock: w.cellarOnly ? 0
           : (w.stock === null || w.stock === undefined || w.stock === '' || +w.stock < 0) ? -1 : Math.floor(+w.stock)
    };
  });

  var PROMOS = { HALF5: { rate: 0.05, min: 6, label: '5% off 6+ bottles' }, CASE15: { rate: 0.15, min: 12, label: '15% off 12+ bottles' } };
  var TAX_RATE = 0.08875; /* NYC combined sales tax */
  var ZONES = {
    pickup: { label: 'Pick up in store', min: 0 },
    orange: { label: 'Orange zone delivery', min: 50 },
    purple: { label: 'Purple zone delivery', min: 100 }
  };

  var KEY_CART = 'bnfb_cart', KEY_PROMO = 'bnfb_promo', KEY_ORDER = 'bnfb_last_order';

  function read(key, fallback) {
    try { var v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; } catch (e) { return fallback; }
  }
  function write(key, val) {
    try { if (val === null) localStorage.removeItem(key); else localStorage.setItem(key, JSON.stringify(val)); } catch (e) { /* private mode */ }
  }

  function byId(id) { for (var i = 0; i < WINES.length; i++) if (WINES[i].id === id) return WINES[i]; return null; }

  function getCart() {
    var c = read(KEY_CART, []);
    return c.filter(function (l) { return byId(l.id) && l.qty > 0; });
  }
  function saveCart(c) { write(KEY_CART, c); renderCount(true); }
  /* how many more of a wine the shelf allows on top of what's in the cart; Infinity for an open line */
  function room(id) {
    var w = byId(id); if (!w) return 0;
    if (w.stock < 0) return Infinity;
    var have = 0; getCart().forEach(function (l) { if (l.id === id) have = l.qty; });
    return Math.max(0, w.stock - have);
  }
  /* returns true when the bottles went in; false when the shelf is empty or already all in the cart */
  function add(id, qty) {
    if (!byId(id)) return false;
    qty = qty || 1;
    if (room(id) < qty) return false;
    var c = getCart(), found = false;
    c.forEach(function (l) { if (l.id === id) { l.qty += qty; found = true; } });
    if (!found) c.push({ id: id, qty: qty });
    saveCart(c);
    return true;
  }
  function setQty(id, qty) {
    var w = byId(id);
    if (w && w.stock >= 0) qty = Math.min(qty, w.stock);
    var c = getCart().map(function (l) { if (l.id === id) l.qty = qty; return l; }).filter(function (l) { return l.qty > 0; });
    saveCart(c);
  }
  function remove(id) { saveCart(getCart().filter(function (l) { return l.id !== id; })); }
  function clear() { saveCart([]); write(KEY_PROMO, null); }

  function bottles() { return getCart().reduce(function (n, l) { return n + l.qty; }, 0); }

  function getPromo() { return (read(KEY_PROMO, '') || '').toUpperCase(); }
  function setPromo(code) { write(KEY_PROMO, code ? code.toUpperCase() : null); }

  function totals() {
    var cart = getCart(), n = 0, sub = 0;
    cart.forEach(function (l) { var w = byId(l.id); n += l.qty; sub += w.price * l.qty; });
    var code = getPromo(), promo = PROMOS[code], rate = 0, promoState = 'none';
    if (code) {
      if (!promo) promoState = 'unknown';
      else if (n < promo.min) promoState = 'short';
      else { promoState = 'ok'; rate = promo.rate; }
    }
    var discount = Math.round(sub * rate * 100) / 100;
    var net = sub - discount;
    var tax = Math.round(net * TAX_RATE * 100) / 100;
    return { lines: cart, bottles: n, subtotal: sub, promo: code, promoState: promoState, promoRate: rate, discount: discount, net: net, tax: tax, total: net + tax };
  }

  function money(n) { return '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }

  function renderCount(bump) {
    var n = bottles();
    [].forEach.call(document.querySelectorAll('[data-cart-count]'), function (el) {
      el.textContent = n;
      var pill = el.closest('.nav__cart');
      if (pill) pill.classList.toggle('nav__cart--full', n > 0);
      if (bump) { el.classList.remove('bump'); void el.offsetWidth; el.classList.add('bump'); }
    });
    refreshCartBar();
  }

  /* Cards are a fixed height so the grid stays even; "Read more" opens the one you want.
     Delegated once, so it covers both the shop's rendered cards and the static pages'. */
  var readMoreWired = false;
  function wireReadMore() {
    if (readMoreWired) return;
    readMoreWired = true;
    document.addEventListener('click', function (ev) {
      var b = ev.target.closest && ev.target.closest('.readmore');
      if (!b) return;
      var card = b.closest('.wcard');
      if (!card) return;
      b.textContent = card.classList.toggle('open') ? 'Read less' : 'Read more';
    });
  }
  /* hide the toggle on cards whose text already fits */
  function trimReadMore(root) {
    var cards = (root || document).querySelectorAll('.wcard');
    [].forEach.call(cards, function (card) {
      var b = card.querySelector('.readmore');
      if (!b || card.classList.contains('open')) return;
      var pair = card.querySelector('.wcard__pair');
      var desc = card.querySelector('.wcard__desc');
      var clipped = (desc && desc.scrollHeight > desc.clientHeight + 2) ||
                    (pair && pair.textContent.trim() !== '');
      b.hidden = !clipped;
    });
  }

  /* One delegated handler for every "Add to cart" on the site, whether the card was
     rendered by the shop page or baked into a static page. Each card carries its own
     quantity stepper, the same control the cart uses. */
  var addWired = false;
  function wireAdd() {
    if (addWired) return;
    addWired = true;
    document.addEventListener('click', function (ev) {
      var t = ev.target;
      var step = t.closest && t.closest('[data-qinc],[data-qdec]');
      if (step) {
        var out = step.parentNode.querySelector('output');
        var n = Math.max(1, (parseInt(out.textContent, 10) || 1) + (step.hasAttribute('data-qinc') ? 1 : -1));
        var w = byId(step.getAttribute('data-qinc') || step.getAttribute('data-qdec'));
        if (w && w.stock >= 0) n = Math.min(n, Math.max(1, w.stock));
        out.textContent = n;
        return;
      }
      var b = t.closest && t.closest('[data-add]');
      if (!b) return;
      var id = b.getAttribute('data-add');
      var box = b.closest('.wcard__buy') || b.parentNode;
      var qtyOut = box && box.querySelector('output');
      var qty = qtyOut ? Math.max(1, parseInt(qtyOut.textContent, 10) || 1) : 1;
      if (add(id, qty)) {
        b.textContent = qty > 1 ? ('Added ' + qty + ' \u2713') : 'Added \u2713';
        b.classList.add('added');
        if (qtyOut) qtyOut.textContent = 1;
      } else {
        var w = byId(id);
        b.textContent = w && w.stock === 0 ? 'Sold out' : ('Only ' + (w ? w.stock : 0) + ' available');
      }
      setTimeout(function () { b.textContent = 'Add to cart'; b.classList.remove('added'); }, 1500);
    });
  }

  /* A standing bar with the running total and both ways on to checkout.
     It only appears once there is something in the cart, and never on the
     cart or checkout pages themselves. */
  function wireCartBar() {
    var here = location.pathname.split('/').pop();
    if (here === 'cart.html' || here === 'checkout.html' || here === 'confirmation.html') return;
    var bar = document.createElement('div');
    bar.className = 'cartbar';
    bar.hidden = true;
    bar.innerHTML =
      '<div class="cartbar__inner">' +
        '<span class="cartbar__sum"><b data-bar-count>0</b> <span data-bar-total></span></span>' +
        '<a class="cartbar__view" href="cart.html">View cart</a>' +
        '<a class="cartbar__cta" href="checkout.html">Check out</a>' +
      '</div>';
    document.body.appendChild(bar);
    refreshCartBar();
  }
  function refreshCartBar() {
    var bar = document.querySelector('.cartbar');
    if (!bar) return;
    var t = totals();
    bar.hidden = t.bottles === 0;
    document.body.classList.toggle('has-cartbar', t.bottles > 0);
    var c = bar.querySelector('[data-bar-count]'), s = bar.querySelector('[data-bar-total]');
    if (c) c.textContent = t.bottles + (t.bottles === 1 ? ' bottle' : ' bottles');
    if (s) s.textContent = '\u00b7 ' + money(t.subtotal);
  }

  /* Native <select> popups are drawn by the OS and ignore the house style, so any
     select marked data-house-select gets a listbox we control. The real <select>
     stays in the DOM and still fires "change", so page code and forms are unchanged. */
  function wireSelects(root) {
    var sels = (root || document).querySelectorAll('select[data-house-select]');
    [].forEach.call(sels, function (sel) {
      if (sel.dataset.houseWired) return;
      sel.dataset.houseWired = '1';

      var wrap = document.createElement('div');
      wrap.className = 'selectmenu';
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'selectmenu__btn';
      btn.setAttribute('aria-haspopup', 'listbox');
      btn.setAttribute('aria-expanded', 'false');
      if (sel.getAttribute('aria-label')) btn.setAttribute('aria-label', sel.getAttribute('aria-label'));
      var list = document.createElement('ul');
      list.className = 'selectmenu__list';
      list.setAttribute('role', 'listbox');
      list.hidden = true;

      sel.parentNode.insertBefore(wrap, sel);
      wrap.appendChild(btn); wrap.appendChild(list); wrap.appendChild(sel);
      sel.classList.add('selectmenu__native');

      function paint() {
        btn.textContent = sel.options[sel.selectedIndex] ? sel.options[sel.selectedIndex].text : '';
        list.innerHTML = '';
        [].forEach.call(sel.options, function (o, i) {
          var li = document.createElement('li');
          li.setAttribute('role', 'option');
          li.setAttribute('aria-selected', i === sel.selectedIndex ? 'true' : 'false');
          li.dataset.i = i;
          li.textContent = o.text;
          list.appendChild(li);
        });
      }
      function open(state) {
        list.hidden = !state;
        btn.setAttribute('aria-expanded', state ? 'true' : 'false');
        wrap.classList.toggle('open', !!state);
      }
      function choose(i) {
        if (i < 0 || i >= sel.options.length) return;
        sel.selectedIndex = i;
        sel.dispatchEvent(new Event('change', { bubbles: true }));
        paint(); open(false); btn.focus();
      }

      paint();
      btn.addEventListener('click', function () { open(list.hidden); });
      list.addEventListener('click', function (ev) {
        var li = ev.target.closest('[data-i]');
        if (li) choose(+li.dataset.i);
      });
      wrap.addEventListener('keydown', function (ev) {
        if (ev.key === 'Escape') { open(false); btn.focus(); return; }
        if (ev.key === 'ArrowDown' || ev.key === 'ArrowUp') {
          ev.preventDefault();
          if (list.hidden) { open(true); return; }
          choose(sel.selectedIndex + (ev.key === 'ArrowDown' ? 1 : -1));
        }
        if ((ev.key === 'Enter' || ev.key === ' ') && !list.hidden) {
          var li = ev.target.closest('[data-i]');
          if (li) { ev.preventDefault(); choose(+li.dataset.i); }
        }
      });
      document.addEventListener('click', function (ev) {
        if (!wrap.contains(ev.target)) open(false);
      });
    });
  }

  function saveOrder(o) { write(KEY_ORDER, o); }
  function lastOrder() { return read(KEY_ORDER, null); }
  function orderNumber() {
    var t = Date.now().toString(36).toUpperCase().slice(-4), r = Math.floor(100 + Math.random() * 900);
    return 'BNFB-' + t + r;
  }

  document.addEventListener('DOMContentLoaded', function () {
    renderCount(false); wireReadMore(); trimReadMore(document); wireAdd(); wireCartBar(); wireSelects(document);
  });

  return {
    CATS: CATS, TAGS: TAGS, WINES: WINES, PROMOS: PROMOS, ZONES: ZONES, TAX_RATE: TAX_RATE,
    byId: byId, getCart: getCart, add: add, setQty: setQty, remove: remove, clear: clear, bottles: bottles, room: room,
    getPromo: getPromo, setPromo: setPromo, totals: totals, money: money, esc: esc, renderCount: renderCount,
    saveOrder: saveOrder, lastOrder: lastOrder, orderNumber: orderNumber,
    wireReadMore: wireReadMore, trimReadMore: trimReadMore, refreshCartBar: refreshCartBar, wireSelects: wireSelects
  };
})();
