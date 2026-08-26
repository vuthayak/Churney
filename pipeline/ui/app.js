/* Churney card explorer — vanilla JS, no dependencies. */
(function () {
  "use strict";

  const DATA = window.CHURNEY_DATA || { cards: [], generated_at: null, count: 0 };
  const $ = (sel) => document.querySelector(sel);

  const state = {
    search: "",
    issuer: "",
    program: "",
    type: "",
    sort: "fee-asc",
    selected: null,
  };

  const money = (minor) =>
    minor == null ? "—" : "$" + (minor / 100).toLocaleString("en-CA", { maximumFractionDigits: 2 });

  const esc = (s) =>
    String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));

  function unique(field) {
    return [...new Set(DATA.cards.map((c) => c.card[field]).filter(Boolean))].sort();
  }

  function fillSelect(sel, values) {
    const el = $(sel);
    for (const v of values) {
      const opt = document.createElement("option");
      opt.value = v;
      opt.textContent = v;
      el.appendChild(opt);
    }
  }

  function filtered() {
    let out = DATA.cards.filter((c) => {
      const card = c.card;
      if (state.issuer && card.issuer_slug !== state.issuer) return false;
      if (state.program && card.program_slug !== state.program) return false;
      if (state.type && card.card_type !== state.type) return false;
      if (state.search) {
        const hay = (
          card.name + " " + card.slug + " " + (card.program_slug || "")
        ).toLowerCase();
        if (!hay.includes(state.search.toLowerCase())) return false;
      }
      return true;
    });
    const fee = (c) => c.card_version.annual_fee_minor ?? -1; // unknown fees last
    out.sort((a, b) => {
      switch (state.sort) {
        case "fee-desc":
          return (fee(b) === -1 ? Infinity : fee(b)) - (fee(a) === -1 ? Infinity : fee(a));
        case "name":
          return a.card.name.localeCompare(b.card.name);
        default:
          return (fee(a) === -1 ? Infinity : fee(a)) - (fee(b) === -1 ? Infinity : fee(b));
      }
    });
    return out;
  }

  function renderList() {
    const cards = filtered();
    $("#list").innerHTML = cards.length
      ? cards
          .map((c) => {
            const v = c.card_version;
            const reviews = c.needs_manual_review.length;
            return `
        <div class="card-item ${state.selected === c.file ? "active" : ""}" data-file="${esc(c.file)}">
          <div class="n">${esc(c.card.name)}</div>
          <div class="r">
            <span class="badge">${esc(c.card.issuer_slug)}</span>
            <span class="badge">${esc(c.card.program_slug)}</span>
            <span class="badge fee">AF ${money(v.annual_fee_minor)}</span>
            ${reviews ? `<span class="badge warn">${reviews} review</span>` : ""}
          </div>
        </div>`;
          })
          .join("")
      : `<div class="empty">No cards match.</div>`;

    for (const el of document.querySelectorAll(".card-item")) {
      el.addEventListener("click", () => {
        state.selected = el.dataset.file;
        renderList();
        renderDetail();
      });
    }
  }

  function kv(k, v, cls) {
    return `<div class="kv"><span class="k">${esc(k)}</span><span class="v ${cls || ""}">${v}</span></div>`;
  }

  function earnRateLabel(r) {
    const cat = r.category_slug
      ? r.category_slug.replace(/_/g, " ")
      : "base / everything else";
    const unit = r.kind === "cashback" ? "% back" : "x points";
    const rate = r.kind === "cashback" ? (r.rate * 100).toFixed(2).replace(/\.00$/, "") : r.rate;
    const cap = r.cap_amount_minor ? ` · cap ${money(r.cap_amount_minor)}` : "";
    return { cat, val: `${rate}${unit}${cap}` };
  }

  function renderDetail() {
    const c = DATA.cards.find((x) => x.file === state.selected);
    const root = $("#detail");
    if (!c) {
      root.innerHTML = `<div class="empty">Select a card to see its breakdown.</div>`;
      return;
    }
    const card = c.card;
    const v = c.card_version;
    const offer = c.offers[0];

    const offerHtml = offer
      ? `
      <div class="box">
        <h3>Welcome offer <span style="text-transform:none">(last verified ${new Date(offer.verified_at).toISOString().slice(0, 10)})</span></h3>
        <div class="offer-headline">${esc(offer.headline)}</div>
        ${kv("Min spend", money(offer.min_spend_minor))}
        ${kv("Deadline", offer.deadline_days != null ? offer.deadline_days + " days" : "—")}
        ${kv("Reward", offer.reward_points != null ? offer.reward_points.toLocaleString() + " pts" : money(offer.reward_cashback_minor))}
        ${offer.first_year_free ? kv("First year free", "yes") : ""}
        ${offer.eligibility_notes ? `<div class="notes" style="margin-top:8px">${esc(offer.eligibility_notes)}</div>` : ""}
        ${(offer.alternate_offers || [])
          .map(
            (a) => `
          <div class="alt">
            <div class="notes"><b>${esc(a.channel)}</b> — ${esc(a.headline)}</div>
            ${kv("Reward", a.reward_points != null ? a.reward_points.toLocaleString() + " pts" : money(a.reward_cashback_minor))}
            ${a.min_spend_minor != null ? kv("Min spend", money(a.min_spend_minor)) : ""}
          </div>`
          )
          .join("")}
      </div>`
      : `<div class="box"><h3>Welcome offer</h3><div class="notes">Not captured — see review notes.</div></div>`;

    const rates = c.earn_rates
      .map(earnRateLabel)
      .map(
        ({ cat, val }) =>
          `<tr><td>${esc(cat)}</td><td class="num">${esc(val)}</td></tr>`
      )
      .join("");

    root.innerHTML = `
      <h1>${esc(card.name)}</h1>
      <div class="subtitle">
        ${esc(card.issuer_slug)} · ${esc(card.card_type)} · program:
        <b>${esc(card.program_slug)}</b> · network: ${esc(card.network)} ·
        status: ${esc(card.status)}
      </div>

      <div class="grid">
        <div class="box">
          <h3>Costs</h3>
          ${kv("Annual fee", money(v.annual_fee_minor), "money")}
          ${kv("Additional card", money(v.extra_card_fee_minor))}
          ${kv("Purchase APR", v.purchase_apr != null ? v.purchase_apr + "%" : "—")}
          ${kv("Cash advance APR", v.cash_apr != null ? v.cash_apr + "%" : "—")}
          ${kv("FX fee", v.fx_fee_pct != null ? v.fx_fee_pct + "%" : "— [review]")}
        </div>

        <div class="box">
          <h3>Earn structure</h3>
          ${
            c.earn_rates.length
              ? `<table><tr><th>Category</th><th style="text-align:right">Rate</th></tr>${rates}</table>`
              : `<div class="notes">Not captured — see review notes.</div>`
          }
        </div>

        ${offerHtml}

        <div class="box">
          <h3>Data quality (${c.needs_manual_review.length} items)</h3>
          ${
            c.needs_manual_review.length
              ? `<ul class="review-list">${c.needs_manual_review
                  .map((i) => `<li><b>${esc(i.field)}</b>: ${esc(i.reason)}</li>`)
                  .join("")}</ul>`
              : `<div class="notes">Fully parsed ✓</div>`
          }
          <div style="margin-top:10px">
            <a class="src" href="${esc(card.page_url)}" target="_blank" rel="noreferrer">source page ↗</a>
            · content hash <code style="font-size:11px">${esc((c.content_hash || "").slice(0, 12))}…</code>
          </div>
        </div>
      </div>`;
  }

  function init() {
    fillSelect("#issuer", unique("issuer_slug"));
    fillSelect("#program", unique("program_slug"));
    $("#meta").textContent = `${DATA.count} cards · generated ${DATA.generated_at?.slice(0, 16).replace("T", " ")}Z · data/docs/04-scraper pipeline`;

    $("#search").addEventListener("input", (e) => {
      state.search = e.target.value;
      renderList();
    });
    for (const id of ["issuer", "program", "type", "sort"]) {
      $("#" + id).addEventListener("change", (e) => {
        state[id] = e.target.value;
        renderList();
      });
    }

    // preselect first card
    const cards = filtered();
    if (cards.length) {
      state.selected = cards[0].file;
    }
    renderList();
    renderDetail();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
