"""Build data/fill_research_2026-08-24.json — long-horizon research fills.

Sources:
- CIBC Summary of Annual Interest Rates and Fees PDF (11995-2026/08, cibc.com)
- Amex card pages + all-cards listing (cached)
- Air Canada Aeroplan credit-card pages (charge-card footnote)
- Frugal Flyer structured fees blocks (secondary cross-check)

Idempotent to run; the emitted patch file is idempotent via apply_fill.py.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
p = HERE / "data" / "fill_research_2026-08-24.json"
patches = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

patches["_meta"] = {
    "date": "2026-08-24",
    "note": (
        "Long-horizon research fills. Primary: issuer pages/disclosures (CIBC rates "
        "PDF 11995-2026/08; amex.ca pages incl. all-cards listing; TD card pages). "
        "Secondary cross-checks: frugalflyer.ca fees blocks, milesopedia.com. "
        "Charge cards carry no purchase APR by design."
    ),
}


def entry(slug, vp=None, resolves=(), adds=()):
    e = patches.setdefault(slug, {})
    if vp:
        e["version_patch"] = {**e.get("version_patch", {}), **vp}
    e["review_resolve"] = sorted(set(e.get("review_resolve", [])) | set(resolves))
    for a in adds:
        rest = [x for x in e.setdefault("review_add", []) if x != a]
        e["review_add"] = rest + [a]


CHG = "charge card - no purchase APR (pay-in-full product)"
CIBC_SRC = 'CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)'

# ── Amex charge cards ───────────────────────────────────────────────────────
entry('amex-ca-small-business-gold-card',
      {'annual_fee_minor': 19900}, ('purchase_apr',),
      [{'field': 'annual_fee_minor',
        'reason': '$199 VERIFIED on amex.ca page ("Annual Fees $199"); was mis-parsed as $0'},
       {'field': 'purchase_apr', 'reason': CHG}])
entry('amex-ca-small-business-platinum-card',
      {'annual_fee_minor': 79900}, ('purchase_apr',),
      [{'field': 'annual_fee_minor',
        'reason': '$799 VERIFIED on amex.ca page; was mis-parsed as $0'},
       {'field': 'purchase_apr', 'reason': CHG}])
entry('amex-ca-the-platinum-card', None, (),
      [{'field': 'purchase_apr', 'reason': CHG + ' ($799 fee confirmed on page)'}])
entry('amex-ca-aeroplan-card', None, ('purchase_apr',),
      [{'field': 'purchase_apr',
        'reason': 'charge card: balance must be paid in full each month; 30% annual '
                  'interest applies only to balances not paid in full (amex.ca / Air '
                  'Canada Aeroplan page footnote)'}])

# ── Amex credit cards with real APRs ────────────────────────────────────────
entry('amex-ca-marriott-bonvoy-business-card',
      {'purchase_apr': 21.99, 'cash_apr': 21.99}, ('purchase_apr',),
      [{'field': 'purchase_apr',
        'reason': '21.99% purchases & cash advances - frugalflyer.ca american-express-marriott-bonvoy-business [cross-check]'}])
entry('amex-ca-essential-credit-card',
      {'purchase_apr': 12.99, 'cash_apr': 12.99},
      ('earn_rates', 'offers', 'purchase_apr'),
      [{'field': 'earn_rates',
        'reason': 'no rewards earning - low-rate card (amex.ca all-cards listing: "$25, '
                  '12.99% on purchases and funds advances"; no earn structure on card page)'}])
# Essential program: no rewards
e = patches.setdefault('amex-ca-essential-credit-card', {})
e['program_slug'] = 'none'

# ── Aeroplan Reserve is a CREDIT card at 21.99% ────────────────────────────
entry('amex-ca-aeroplan-reserve',
      {'purchase_apr': 21.99, 'cash_apr': 21.99}, ('purchase_apr',),
      [{'field': 'purchase_apr',
        'reason': '21.99% purchases & funds advances - VERIFIED on amex.ca page ("Card Type Credit Card ... Annual Interest Rate 21.99%")'}])

# ── CIBC business fee + program calls ──────────────────────────────────────
entry('cibc-aventura-plus-visa', {'annual_fee_minor': 12000}, ('annual_fee',),
      [{'field': 'annual_fee_minor',
        'reason': '$120 - frugalflyer.ca cibc-aventura-visa-business-plus [cross-check]'}])
entry('cibc-select-visa-card', None,
      ('program_slug', 'earn_rates'),
      [{'field': 'program_slug',
        'reason': 'no rewards: Select is a low-rate card (13.99%) - milesopedia page shows '
                  'rates only with no earn section; CIBC taxonomy files it under low-interest'}])
entry('cibc-corporate-classic-plus-visa', {'annual_fee_minor': None}, (), [])

# ── TD USD Visa: no rewards program ────────────────────────────────────────
entry('td-us-dollar-visa-card', None,
      ('program_slug', 'earn_rates', 'offers'),
      [{'field': 'program_slug',
        'reason': 'no rewards program: TD page shows no earn structure anywhere; value prop '
                  'is FX-free USD spending (0% FX fee verified on page)'}])

# ── TD Aeroplan VI: complete earn structure + full offer ───────────────────
tavi = patches.setdefault('td-aeroplan-visa-infinite-card', {})
tavi['rates_add'] = [
    {'category_slug': 'gas', 'rate': 1.5, 'kind': 'points',
     'notes': 'eligible gas + electric vehicle charging'},
    {'category_slug': 'travel_air', 'rate': 1.5, 'kind': 'points',
     'notes': 'direct through Air Canada purchases incl Air Canada Vacations'},
]
tavi['offer_patch'] = {
    'headline': 'Earn up to 40,000 Aeroplan points',
    'reward_points': 40000,
    'min_spend_minor': 300000,
    'deadline_days': 90,
    'eligibility_notes_append': (
        'Components: 10,000 pts first Purchase; 15,000 pts when $3,000 spent within 90 days '
        'of Account opening; one-time anniversary bonus of 15,000 pts when $12,000 spent '
        'within 12 months of Account opening'),
}
tavi['review_resolve'] = sorted(set(tavi.get('review_resolve', [])) | {'base_rate'})

# ── TD FCT VI: full earn structure + canonical offer ────────────────────────
patches['td-first-class-travel-visa-infinite-card'] = {
    'rates_replace': [
        {'category_slug': None, 'rate': 2.0, 'kind': 'points',
         'notes': 'Base Earn Rate: 2 pts/$1 on all other purchases'},
        {'category_slug': 'grocery', 'rate': 6.0, 'kind': 'points',
         'notes': 'first $25,000 annual net purchases'},
        {'category_slug': 'dining', 'rate': 6.0, 'kind': 'points',
         'notes': 'first $25,000 annual net purchases'},
        {'category_slug': 'transit_rideshare', 'rate': 6.0, 'kind': 'points',
         'notes': 'public transit incl ferries (MCC 4111); first $25k annual net purchases'},
        {'category_slug': 'recurring_bills', 'rate': 4.0, 'kind': 'points',
         'notes': 'recurring bill payments; first $25k annual net purchases'},
        {'category_slug': 'streaming_subs', 'rate': 4.0, 'kind': 'points',
         'notes': 'streaming, digital gaming & media; first $25k annual net purchases'},
        {'category_slug': 'travel_other', 'rate': 8.0, 'kind': 'points',
         'notes': 'bookings through Expedia For TD'},
    ],
    'offer_patch': {
        'headline': 'Earn up to $1,300 in value including up to 146,000 TD Rewards Points',
        'reward_points': 146000,
        'min_spend_minor': 750000,
        'deadline_days': 180,
        'eligibility_notes_append': (
            'Components: 20,000 pts first Purchase; additional 126,000 pts when $7,500 spent '
            'within 180 days of Account opening'),
    },
    'review_resolve': ['earn_rates'],
}

# ── Simplii: full structure from issuer page ────────────────────────────────
patches['simplii-cash-back-visa']['rates_replace'] = [
    {'category_slug': 'dining', 'rate': 0.04, 'kind': 'cashback',
     'notes': 'eligible restaurants and bars'},
    {'category_slug': 'gas', 'rate': 0.015, 'kind': 'cashback',
     'notes': 'up to $15,000/year combined across gas/groceries/drugstore/pre-authorized'},
    {'category_slug': 'grocery', 'rate': 0.015, 'kind': 'cashback'},
    {'category_slug': 'drugstore', 'rate': 0.015, 'kind': 'cashback'},
    {'category_slug': 'recurring_bills', 'rate': 0.015, 'kind': 'cashback',
     'notes': 'pre-authorized payments'},
    {'category_slug': None, 'rate': 0.005, 'kind': 'cashback', 'notes': 'all other purchases'},
]
sv = patches['simplii-cash-back-visa']
sv['review_resolve'] = sorted({'base_rate'} | set(sv.get('review_resolve', [])))

# ── Business Gold base rate; Tangerine WE base ─────────────────────────────
patches['amex-ca-small-business-gold-card']['rates_replace'] = [
    {'category_slug': None, 'rate': 1.0, 'kind': 'points',
     'notes': '1X the points on everything; +10,000 bonus points each calendar quarter with $20,000 spend'},
]
twe = patches.setdefault('tangerine-world-elite-mastercard', {})
twe['rates_replace'] = [
    {'category_slug': None, 'rate': 1.0, 'kind': 'points',
     'notes': '1 Scene+ pt/$1 everywhere; 1.5x Scene+ points on 3 accelerator categories of choice (from 13 incl grocery, entertainment, dining, travel)'},
]
twe['review_resolve'] = sorted(set(twe.get('review_resolve', [])) | {'earn_rates'})

# ── CIBC FX upgrade: official doc wording ───────────────────────────────────
for slug, e in patches.items():
    if not slug.startswith('cibc-'):
        continue
    e['review_add'] = [
        {**a, 'reason': a['reason'].replace(
            'set 2.5% per CIBC standard [VERIFY]',
            '2.5% - VERIFIED: official CIBC disclosure ("fee of 2.5% of the converted amount")')}
        if 'CIBC standard' in a.get('reason', '') else a
        for a in e.get('review_add', [])
    ]

p.write_text(json.dumps(patches, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"staged {sum(1 for k in patches if not k.startswith('_'))} slugs -> {p.name}")
