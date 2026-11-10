/* Magic House: site behaviour (no dependencies) */
(function () {
  "use strict";
  var cfg = window.MH || {};
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  function waLink(text) {
    if (cfg.wa) return "https://wa.me/" + cfg.wa + (text ? "?text=" + encodeURIComponent(text) : "");
    return cfg.waFallback || "#";
  }
  window.MH_wa = waLink;
  var ROOT = cfg.root || "/";
  function rel(u) {
    if (!u || /^https?:/.test(u)) return u;
    u = ROOT + u.replace(/^\//, "");
    return u;
  }

  /* Sticky header shadow */
  var header = $(".site-header");
  if (header) {
    var onScroll = function () { header.classList.toggle("is-scrolled", window.scrollY > 8); };
    onScroll(); window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* Focus trap helper */
  function trap(container, e) {
    if (e.key !== "Tab") return;
    var f = $$('a[href], button:not([disabled]), input, textarea, [tabindex]:not([tabindex="-1"])', container).filter(function (el) { return el.offsetParent !== null; });
    if (!f.length) return;
    var first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }

  /* Mobile drawer */
  var drawer = $("#drawer"), toggle = $(".menu-toggle"), lastFocus;
  function openDrawer() {
    lastFocus = document.activeElement;
    drawer.classList.add("is-open"); drawer.removeAttribute("aria-hidden");
    toggle.setAttribute("aria-expanded", "true"); document.body.style.overflow = "hidden";
    setTimeout(function () { var c = $(".drawer-close", drawer); c && c.focus(); }, 50);
  }
  function closeDrawer() {
    drawer.classList.remove("is-open"); drawer.setAttribute("aria-hidden", "true");
    toggle.setAttribute("aria-expanded", "false"); document.body.style.overflow = "";
    lastFocus && lastFocus.focus();
  }
  if (drawer && toggle) {
    toggle.addEventListener("click", openDrawer);
    $$("[data-close-drawer]", drawer).forEach(function (el) { el.addEventListener("click", closeDrawer); });
    drawer.addEventListener("keydown", function (e) { if (e.key === "Escape") closeDrawer(); trap(drawer, e); });
  }

  /* Search */
  var search = $("#search"), index = null;
  function openSearch() {
    lastFocus = document.activeElement;
    search.classList.add("is-open"); search.removeAttribute("aria-hidden"); document.body.style.overflow = "hidden";
    var input = $("input", search); setTimeout(function () { input.focus(); }, 30);
    if (!index) {
      fetch(ROOT + "search.json").then(function (r) { return r.json(); }).then(function (d) { index = d; render(input.value); }).catch(function () { index = []; });
    }
  }
  function closeSearch() {
    search.classList.remove("is-open"); search.setAttribute("aria-hidden", "true"); document.body.style.overflow = "";
    lastFocus && lastFocus.focus();
  }
  function norm(s) { return (s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, ""); }
  function render(q) {
    var list = $(".search-results", search), empty = $(".search-empty", search);
    list.innerHTML = ""; q = norm(q).trim();
    if (!q || !index) { empty.textContent = index && !index.length ? "Products are being added. Check back soon or message us on WhatsApp." : ""; return; }
    var terms = q.split(/\s+/);
    var hits = index.filter(function (p) { var hay = norm(p.n + " " + p.c + " " + p.d); return terms.every(function (t) { return hay.indexOf(t) > -1; }); }).slice(0, 20);
    empty.textContent = hits.length ? "" : "No products match \u201c" + q + "\u201d. Try another word, or ask us on WhatsApp.";
    hits.forEach(function (p) {
      var li = document.createElement("li");
      li.innerHTML = '<a href="' + rel(p.u) + '">' + (p.i ? '<img src="' + rel(p.i) + '" alt="" loading="lazy" width="60" height="60">' : '<span class="thumb"></span>') +
        '<span><strong></strong><small></small></span></a>';
      $("strong", li).textContent = p.n; $("small", li).textContent = p.c + (p.p ? ", " + p.p : "");
      list.appendChild(li);
    });
  }
  if (search) {
    $$("[data-open-search]").forEach(function (b) { b.addEventListener("click", openSearch); });
    $("[data-close-search]", search).addEventListener("click", closeSearch);
    $("input", search).addEventListener("input", function (e) { render(e.target.value); });
    search.addEventListener("keydown", function (e) { if (e.key === "Escape") closeSearch(); trap(search, e); });
  }

  /* Reveal on scroll */
  var reveals = $$(".reveal");
  if ("IntersectionObserver" in window && reveals.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    reveals.forEach(function (el) { io.observe(el); });
  } else { reveals.forEach(function (el) { el.classList.add("is-in"); }); }

  /* Load more on collection pages */
  $$("[data-paginate]").forEach(function (grid) {
    var per = parseInt(grid.getAttribute("data-paginate"), 10) || 12;
    var items = $$(":scope > *", grid);
    if (items.length <= per) return;
    var shown = per;
    items.forEach(function (el, i) { if (i >= shown) el.hidden = true; });
    var wrap = document.createElement("div"); wrap.className = "load-more";
    var btn = document.createElement("button"); btn.className = "btn btn--ghost"; btn.type = "button";
    var update = function () { btn.textContent = "Load more (" + (items.length - shown) + " left)"; };
    update(); wrap.appendChild(btn); grid.after(wrap);
    btn.addEventListener("click", function () {
      var first = items[shown];
      shown += per; items.forEach(function (el, i) { if (i < shown) el.hidden = false; });
      if (shown >= items.length) wrap.remove(); else update();
      var a = first && $("a", first); a && a.focus();
    });
  });

  /* Gallery filter + lightbox */
  var lb = $("#lightbox");
  $$("[data-gallery]").forEach(function (gal) {
    var figs = $$("figure", gal);
    var filters = $(".filters", gal.parentNode);
    if (filters) {
      $$("button", filters).forEach(function (b) {
        b.addEventListener("click", function () {
          var f = b.getAttribute("data-filter");
          $$("button", filters).forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
          figs.forEach(function (fig) { fig.hidden = !(f === "all" || fig.getAttribute("data-cat") === f); });
        });
      });
    }
    if (!lb) return;
    var img = $("img", lb), cap = $(".lb-caption", lb), cur = 0, visible = [];
    function show(i) {
      cur = (i + visible.length) % visible.length;
      var b = $("button", visible[cur]);
      img.src = b.getAttribute("data-full"); img.alt = $("img", b).alt;
      var fc = $("figcaption", visible[cur]); cap.textContent = fc ? fc.textContent : "";
    }
    function open(fig) {
      lastFocus = document.activeElement;
      visible = figs.filter(function (f) { return !f.hidden; });
      lb.classList.add("is-open"); lb.removeAttribute("aria-hidden"); document.body.style.overflow = "hidden";
      show(visible.indexOf(fig)); $(".lb-close", lb).focus();
    }
    function close() { lb.classList.remove("is-open"); lb.setAttribute("aria-hidden", "true"); document.body.style.overflow = ""; lastFocus && lastFocus.focus(); }
    figs.forEach(function (fig) { $("button", fig).addEventListener("click", function () { open(fig); }); });
    $(".lb-close", lb).onclick = close;
    $(".lb-prev", lb).onclick = function () { show(cur - 1); };
    $(".lb-next", lb).onclick = function () { show(cur + 1); };
    lb.onclick = function (e) { if (e.target === lb) close(); };
    lb.onkeydown = function (e) {
      if (e.key === "Escape") close();
      else if (e.key === "ArrowLeft") show(cur - 1);
      else if (e.key === "ArrowRight") show(cur + 1);
      trap(lb, e);
    };
  });

  /* Product image thumbs */
  $$(".pdp-gallery").forEach(function (g) {
    var main = $(".main img", g);
    $$(".thumbs button", g).forEach(function (b) {
      b.addEventListener("click", function () {
        main.src = b.getAttribute("data-src");
        $$(".thumbs button", g).forEach(function (x) { x.setAttribute("aria-current", String(x === b)); });
      });
    });
  });


  /* Basket */
  var KEY = "mh-basket-v1", basketEl = $("#basket"), toastEl = $(".toast"), toastT;
  function load() { try { var d = JSON.parse(localStorage.getItem(KEY) || "[]"); return Array.isArray(d) ? d : []; } catch (e) { return []; } }
  var cart = load();
  function save() { try { localStorage.setItem(KEY, JSON.stringify(cart)); } catch (e) {} }
  function money(v) { return "$" + (Math.round(v * 100) / 100).toFixed(2).replace(/\.00$/, ""); }
  function toast(msg) {
    if (!toastEl) return;
    toastEl.textContent = msg; toastEl.classList.add("is-on");
    clearTimeout(toastT); toastT = setTimeout(function () { toastEl.classList.remove("is-on"); }, 2600);
  }
  function count() { return cart.reduce(function (s, i) { return s + i.qty; }, 0); }
  function renderBasket() {
    var n = count();
    $$(".basket-count").forEach(function (b) { b.textContent = n > 99 ? "99+" : n; b.hidden = n === 0; });
    $$("[data-open-basket]").forEach(function (b) { b.setAttribute("aria-label", "Open basket, " + n + " item" + (n === 1 ? "" : "s")); });
    if (!basketEl) return;
    var list = $(".basket__items", basketEl);
    list.innerHTML = "";
    basketEl.classList.toggle("is-empty", !cart.length);
    var total = 0, unpriced = false;
    cart.forEach(function (it, idx) {
      if (it.price == null) unpriced = true; else total += it.price * it.qty;
      var li = document.createElement("li"); li.className = "bitem";
      li.innerHTML = (it.img ? '<img src="' + rel(it.img) + '" alt="" width="64" height="64">' : '<span class="bthumb"></span>') +
        '<div class="binfo"><a class="bname" href="' + rel(it.url) + '"></a><span class="bprice"></span>' +
        '<div class="bqty"><button type="button" data-dec aria-label="Decrease quantity">' + ICON_MINUS + '</button>' +
        '<span class="q" aria-live="polite"></span><button type="button" data-inc aria-label="Increase quantity">' + ICON_PLUS + '</button>' +
        '<button type="button" class="bremove" data-remove>Remove</button></div></div>';
      $(".bname", li).textContent = it.name;
      $(".bprice", li).textContent = it.price == null ? "Price on request" : money(it.price * it.qty);
      $(".q", li).textContent = it.qty;
      $("[data-dec]", li).setAttribute("aria-label", "Decrease quantity of " + it.name);
      $("[data-inc]", li).setAttribute("aria-label", "Increase quantity of " + it.name);
      $("[data-remove]", li).setAttribute("aria-label", "Remove " + it.name);
      $("[data-dec]", li).onclick = function () { if (it.qty > 1) { it.qty--; save(); renderBasket(); } else { removeAt(idx); } };
      $("[data-inc]", li).onclick = function () { if (it.qty < 99) { it.qty++; save(); renderBasket(); } };
      $("[data-remove]", li).onclick = function () { removeAt(idx); };
      list.appendChild(li);
    });
    $(".basket__total strong", basketEl).textContent = money(total) + (unpriced ? " +" : "");
    $(".basket__note", basketEl).hidden = !unpriced;
  }
  function removeAt(i) {
    var it = cart[i]; cart.splice(i, 1); save(); renderBasket();
    toast(it.name + " removed from basket");
    var next = $(".basket__items [data-remove]", basketEl) || $(".basket__empty a", basketEl);
    next && next.focus();
  }
  var ICON_MINUS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M5 12h14"/></svg>';
  var ICON_PLUS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>';
  function openBasket() {
    lastFocus = document.activeElement;
    basketEl.classList.add("is-open"); basketEl.removeAttribute("aria-hidden"); document.body.style.overflow = "hidden";
    setTimeout(function () { var c = $("[data-close-basket].icon-btn", basketEl); c && c.focus(); }, 50);
  }
  function closeBasket() {
    basketEl.classList.remove("is-open"); basketEl.setAttribute("aria-hidden", "true"); document.body.style.overflow = "";
    lastFocus && lastFocus.focus();
  }
  if (basketEl) {
    $$("[data-open-basket]").forEach(function (b) { b.addEventListener("click", openBasket); });
    $$("[data-close-basket]", basketEl).forEach(function (b) { b.addEventListener("click", closeBasket); });
    basketEl.addEventListener("keydown", function (e) { if (e.key === "Escape") closeBasket(); trap(basketEl, e); });
    $("[data-clear-basket]", basketEl).addEventListener("click", function () { cart = []; save(); renderBasket(); toast("Basket emptied"); $(".basket__empty a", basketEl).focus(); });
    var bform = $(".basket__form", basketEl);
    bform.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!cart.length) return;
      var ok = true;
      ["name", "address"].forEach(function (n) {
        var inp = bform[n], f = inp.closest(".field"), bad = inp.value.trim().length < 2;
        f.classList.toggle("has-error", bad); inp.setAttribute("aria-invalid", String(bad));
        $(".err", f).textContent = bad ? (n === "name" ? "Enter your full name." : "Enter your delivery area or address.") : "";
        if (bad && ok) { inp.focus(); ok = false; }
      });
      if (!ok) return;
      var total = 0, unpriced = false;
      var lines = cart.map(function (it, i) {
        var line = (i + 1) + ". " + it.name + " x " + it.qty;
        if (it.price == null) { unpriced = true; line += ": price on request"; }
        else { total += it.price * it.qty; line += ": " + money(it.price * it.qty); }
        return line;
      });
      var base = (location.origin && location.origin !== "null") ? location.href.replace(/[#?].*$/, "") : "";
      var msg = "Hello Magic House! I would like to place an order:\n\n" + lines.join("\n") +
        "\n\nTotal: " + money(total) + (unpriced ? " (plus items with price on request)" : "") +
        "\n\nName: " + bform.name.value.trim() + "\nDelivery: " + bform.address.value.trim() +
        (bform.note.value.trim() ? "\nNotes: " + bform.note.value.trim() : "") +
        "\n\nPlease confirm availability and delivery.";
      window.open(waLink(msg), "_blank", "noopener");
      toast("WhatsApp opened with your order. Tap send there to confirm.");
    });
  }
  $$("[data-add]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var d; try { d = JSON.parse(btn.getAttribute("data-add")); } catch (e) { return; }
      var found = cart.filter(function (i) { return i.id === d.id; })[0];
      if (found) found.qty = Math.min(99, found.qty + 1); else cart.push({ id: d.id, name: d.name, price: d.price, img: d.img, url: d.url, qty: 1 });
      save(); renderBasket();
      toast(d.name + " added to basket");
      btn.classList.add("is-added"); setTimeout(function () { btn.classList.remove("is-added"); }, 900);
    });
  });
  window.addEventListener("storage", function (e) { if (e.key === KEY) { cart = load(); renderBasket(); } });
  renderBasket();

  /* Shop filters */
  var sf = $("[data-shop-filters]"), sg = $("[data-shop-grid]");
  if (sf && sg) {
    var cards = $$(".product-card", sg), cnt = $(".shop-count");
    var applyF = function (f) {
      var n = 0;
      cards.forEach(function (c) { var show = f === "all" || c.getAttribute("data-col") === f; c.hidden = !show; if (show) n++; });
      $$("button", sf).forEach(function (x) { x.setAttribute("aria-pressed", String(x.getAttribute("data-filter") === f)); });
      if (cnt) cnt.textContent = n + (n === 1 ? " piece" : " pieces");
    };
    $$("button", sf).forEach(function (b) { b.addEventListener("click", function () { var f = b.getAttribute("data-filter"); applyF(f); try { history.replaceState(null, "", f === "all" ? location.pathname : "#" + f); } catch (e) {} }); });
    var h = location.hash.replace("#", ""); if (h && $('[data-filter="' + h + '"]', sf)) applyF(h);
  }

  /* Contact form */
  var form = $("#contact-form");
  if (form) {
    var status = $(".form-status", form);
    var rules = {
      name: function (v) { return v.trim().length >= 2 || "Enter your full name."; },
      phone: function (v) { return /^[+()\d\s-]{7,20}$/.test(v.trim()) || "Enter a phone number, for example +961 70 123 456."; },
      email: function (v) { return !v.trim() || /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim()) || "Enter a valid email address, or leave it empty."; },
      message: function (v) { return v.trim().length >= 5 || "Tell us a little about what you need."; }
    };
    function check(input) {
      var r = rules[input.name]; if (!r) return true;
      var res = r(input.value), field = input.closest(".field"), err = $(".err", field);
      var ok = res === true;
      field.classList.toggle("has-error", !ok);
      input.setAttribute("aria-invalid", String(!ok));
      if (err) err.textContent = ok ? "" : res;
      return ok;
    }
    $$("input, textarea", form).forEach(function (i) { i.addEventListener("blur", function () { if (i.value) check(i); }); });
    form.addEventListener("submit", function (e) {
      e.preventDefault(); status.className = "form-status"; status.textContent = "";
      if (form.company && form.company.value) return; // honeypot
      if (Date.now() - (window.__mhLoaded || 0) < 2500) { status.className = "form-status bad"; status.textContent = "Please take a moment to review your message, then send it again."; return; }
      var inputs = $$("input[name], textarea[name]", form).filter(function (i) { return rules[i.name]; });
      var bad = inputs.filter(function (i) { return !check(i); });
      if (bad.length) { bad[0].focus(); status.className = "form-status bad"; status.textContent = "Check the highlighted fields."; return; }
      var data = { name: form.name.value.trim(), phone: form.phone.value.trim(), email: form.email.value.trim(), message: form.message.value.trim() };
      if (cfg.formEndpoint) {
        var btn = $("button[type=submit]", form); btn.disabled = true; btn.textContent = "Sending\u2026";
        fetch(cfg.formEndpoint, { method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" }, body: JSON.stringify(data) })
          .then(function (r) { if (!r.ok) throw new Error(); form.reset(); status.className = "form-status ok"; status.textContent = "Message sent. We will reply soon."; })
          .catch(function () { status.className = "form-status bad"; status.textContent = "The message did not send. Try again, or message us on WhatsApp."; })
          .then(function () { btn.disabled = false; btn.textContent = "Send message"; });
      } else {
        var text = "Hello Magic House!\n\nName: " + data.name + "\nPhone: " + data.phone + (data.email ? "\nEmail: " + data.email : "") + "\n\n" + data.message;
        window.open(waLink(text), "_blank", "noopener");
        status.className = "form-status ok"; status.textContent = "WhatsApp opened with your message. Tap send there to reach us.";
      }
    });
  }
  window.__mhLoaded = Date.now();
})();
