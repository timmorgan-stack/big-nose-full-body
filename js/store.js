/* Big Nose Full Body — demo store engine (cart in localStorage).
   Catalogue comes from data/catalog.json via the generated data/catalog.js (window.BNFB_CATALOG).
   Demo only: no server, no real payments. */
window.BNFB = (function () {
  'use strict';

  var CATS = {
    sparkling: { label: 'Sparkling',           color: '#b8891c' },
    white:     { label: 'White',               color: '#c2a12a' },
    rose:      { label: 'Rosé',                color: '#d4607f' },
    orange:    { label: 'Orange & Funky',      color: '#c96a1f' },
    red:       { label: 'Red',                 color: '#950951' },
    sake:      { label: 'Sake & Cider',        color: '#3f5b8c' },
    large:     { label: 'Large Format',        color: '#17120e' },
    dessert:   { label: 'Dessert & Fortified', color: '#6b3fa0' },
    gift:      { label: 'Gift Cards',          color: '#17120e' }
  };

  var TAGS = {
    reserve: 'Reserve List', organic: 'Organic', biodynamic: 'Biodynamic', vegan: 'Vegan',
    natural: 'Natural', unoaked: 'Unoaked', 'minimal-sulfur': 'Minimal Sulfur',
    'no-added-sulfur': 'No Added Sulfur', kosher: 'Kosher', sustainable: 'Sustainable', sample: 'Sample listing'
  };

  var FEED = (window.BNFB_CATALOG && window.BNFB_CATALOG.works) || [];
  var WINES = FEED.map(function (w) {
    return {
      id: w.id, ref: w.ref || w.id, name: w.title, cat: CATS[w.category] ? w.category : 'red',
      origin: w.place || '', price: +w.price || 0, tags: w.tagKeys || [], score: w.score || '',
      desc: w.description || '', image: (w.image && (w.image.thumb || w.image.large)) || '', featured: !!w.featured
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
  function add(id, qty) {
    if (!byId(id)) return;
    var c = getCart(), found = false;
    c.forEach(function (l) { if (l.id === id) { l.qty += (qty || 1); found = true; } });
    if (!found) c.push({ id: id, qty: qty || 1 });
    saveCart(c);
  }
  function setQty(id, qty) {
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
      if (bump) { el.classList.remove('bump'); void el.offsetWidth; el.classList.add('bump'); }
    });
  }

  function saveOrder(o) { write(KEY_ORDER, o); }
  function lastOrder() { return read(KEY_ORDER, null); }
  function orderNumber() {
    var t = Date.now().toString(36).toUpperCase().slice(-4), r = Math.floor(100 + Math.random() * 900);
    return 'BNFB-' + t + r;
  }

  document.addEventListener('DOMContentLoaded', function () { renderCount(false); });

  return {
    CATS: CATS, TAGS: TAGS, WINES: WINES, PROMOS: PROMOS, ZONES: ZONES, TAX_RATE: TAX_RATE,
    byId: byId, getCart: getCart, add: add, setQty: setQty, remove: remove, clear: clear, bottles: bottles,
    getPromo: getPromo, setPromo: setPromo, totals: totals, money: money, esc: esc, renderCount: renderCount,
    saveOrder: saveOrder, lastOrder: lastOrder, orderNumber: orderNumber
  };
})();
