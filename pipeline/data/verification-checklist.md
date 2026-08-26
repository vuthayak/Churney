# Manual Verification Checklist

Generated 2026-08-26 · 56 cards across 6 issuers.

For each card: open the **source page**, confirm every fact below, then
tick the box. Anything wrong → fix in `data/cards/<slug>.json` and note
`verified_at`. Convention: cashback rates are stored as pct/100
(4% -> `0.04`) but shown here as percentages.

## amex_ca

### ☐ Aeroplan Business Reserve Card  `amex-ca-aeroplan-business-reserve-card`

Source: <https://www.americanexpress.com/en-ca/credit-cards/aeroplan-business-reserve-card/>

- Annual fee: **$599.00**
- Additional card fee: $199.00
- Purchase APR: 21.99
- Cash advance APR: 21.99
- FX fee %: 2.5
- Earn rates: **1.25x points (base), 3x points (travel_air), 2.5x points (travel_hotel), 2x points (travel_hotel)**
- Welcome offer: **Earn up to 80,000 Aeroplan points** | min spend $10,500.00 | deadline 90 days | reward: 80,000 points
  - Alternate [later_spend]: Additional 40,000 Bonus Aeroplan points in month 13 | reward: 40,000 pts
- ⚠️ Review items (2):
  - **fx_fee_pct**: per-card FX fee not stated; verify standard 2.5% [VERIFY]
  - **fx_fee_pct**: 2.5% sourced from frugalflyer.ca (secondary) [VERIFY]

### ☐ Aeroplan Card  `amex-ca-aeroplan-card`

Source: <https://www.americanexpress.com/en-ca/charge-cards/aeroplan-card/>

- Annual fee: **$120.00**
- Additional card fee: $50.00
- Purchase APR: — (review)
- Cash advance APR: — (review)
- FX fee %: 2.5
- Earn rates: **1x points (base), 2x points (travel_air), 1.5x points (dining), 1.5x points (travel_hotel)**
- Welcome offer: **Earn 35,000 points** | min spend $7,500.00 | deadline 180 days | reward: 35,000 points
  - Alternate [later_spend]: Additional earn component: 10,000 points | reward: 10,000 pts
- ⚠️ Review items (2):
  - **fx_fee_pct**: set 2.5% from external knowledge [VERIFY]; Amex card pages do not state FX fee
  - **purchase_apr**: charge card: balance must be paid in full each month; 30% annual interest applies only to balances not paid in full (amex.ca / Air Canada Aeroplan page footnote)

### ☐ Aeroplan Reserve Card  `amex-ca-aeroplan-reserve`

Source: <https://www.americanexpress.com/en-ca/credit-cards/aeroplan-reserve/>

- Annual fee: **$599.00**
- Additional card fee: $199.00
- Purchase APR: 21.99
- Cash advance APR: 21.99
- FX fee %: 2.5
- Earn rates: **1.25x points (base), 3x points (travel_air), 2x points (dining), 2x points (travel_hotel)**
- Welcome offer: **Earn 60,000 points** | min spend $7,500.00 | deadline 90 days | reward: 60,000 points
  - Alternate [later_spend]: Additional earn component: 25,000 points | reward: 25,000 pts
- ⚠️ Review items (2):
  - **fx_fee_pct**: set 2.5% Amex CA standard [VERIFY]; not stated on cached card page
  - **purchase_apr**: 21.99% purchases & funds advances - VERIFIED on amex.ca page ("Card Type Credit Card ... Annual Interest Rate 21.99%")

### ☐ Business Gold Rewards Card  `amex-ca-small-business-gold-card`

Source: <https://www.americanexpress.com/en-ca/charge-cards/small-business-gold-card/>

- Annual fee: **$199.00**
- Purchase APR: — (review)
- Cash advance APR: — (review)
- FX fee %: 2.5
- Earn rates: **1x points (base)**
- Welcome offer: **Earn 50,000 points** | min spend $7,500.00 | deadline 90 days | reward: 50,000 points
  - Alternate [later_spend]: Additional earn component: 20,000 points | reward: 20,000 pts
  - Alternate [later_spend]: Additional earn component: 10,000 points | reward: 10,000 pts
- ⚠️ Review items (6):
  - **annual_fee_minor**: fee pattern not found
  - **earn_rates**: unmapped earn-tile title skipped (never-guess): 'everything'
  - **earn_rates**: unmapped earn-tile title skipped (never-guess): 'everything for every $1 in Card purchases 5 Featured Benefits Item 1 of 7 Up to $100 in statement credits annually with Dell. Until December 31,2026, shop with Dell and earn up to $50 in statement cre'
  - **fx_fee_pct**: set 2.5% from external knowledge [VERIFY]
  - **annual_fee_minor**: $199 VERIFIED on amex.ca page ("Annual Fees $199"); was mis-parsed as $0
  - **purchase_apr**: charge card - no purchase APR (pay-in-full product)

### ☐ Business Platinum Card from American Express  `amex-ca-small-business-platinum-card`

Source: <https://www.americanexpress.com/en-ca/charge-cards/small-business-platinum-card/>

- Annual fee: **$799.00**
- Purchase APR: — (review)
- Cash advance APR: — (review)
- FX fee %: 2.5
- Earn rates: **1.25x points (travel_other), 1.25x points (base)**
- Welcome offer: **Earn 80,000 points** | min spend $15,000.00 | deadline 90 days | reward: 80,000 points
  - Alternate [later_spend]: Additional earn component: 40,000 points | reward: 40,000 pts
- ⚠️ Review items (6):
  - **annual_fee_minor**: fee pattern not found
  - **earn_rates**: unmapped earn-tile title skipped (never-guess): 'everything'
  - **earn_rates**: unmapped earn-tile title skipped (never-guess): 'everything for every $1 in Card purchases 3 Featured Benefits Item 1 of 4 Enjoy financial flexibility that offers you more control Your Card comes equipped with business sized purchasing power that ad'
  - **fx_fee_pct**: set 2.5% from external knowledge [VERIFY]
  - **annual_fee_minor**: $799 VERIFIED on amex.ca page; was mis-parsed as $0
  - **purchase_apr**: charge card - no purchase APR (pay-in-full product)

### ☐ Cobalt Card  `amex-ca-cobalt-card`

Source: <https://www.americanexpress.com/en-ca/credit-cards/cobalt-card/>

- Annual fee: **$191.88**
- Purchase APR: 21.99
- Cash advance APR: 21.99
- FX fee %: 2.5
- Earn rates: **1x points (base), 5x points (dining), 3x points (streaming_subs), 2x points (transit_rideshare)**
- Welcome offer: **Earn up to 15,000 points** | reward: 15,000 points
- ⚠️ Review items (2):
  - **annual_fee_minor**: monthly-billed card ($15.99/month); stored annualized as 19188 minor units
  - **fx_fee_pct**: set 2.5% from external knowledge [VERIFY]; Amex card pages do not state FX fee

### ☐ EssentialTMCredit Card  `amex-ca-essential-credit-card`

Source: <https://www.americanexpress.com/en-ca/credit-cards/essential-credit-card/>

- Annual fee: **$25.00**
- Purchase APR: 12.99
- Cash advance APR: 12.99
- FX fee %: 2.5
- Earn rates: ⚠️ none captured
- ⚠️ Review items (1):
  - **fx_fee_pct**: set 2.5% from external knowledge [VERIFY]; Amex card pages do not state FX fee

### ☐ Gold Rewards Card  `amex-ca-gold-rewards-card`

Source: <https://www.americanexpress.com/en-ca/credit-cards/gold-rewards-card/>

- Annual fee: **$250.00**
- Additional card fee: $1.00
- Purchase APR: 21.99
- Cash advance APR: 21.99
- FX fee %: 2.5
- Earn rates: **1x points (base), 2x points (gas), 2x points (drugstore), 2x points (grocery), 2x points (travel_air), 2x points (travel_hotel), 2x points (travel_other)**
- Welcome offer: **Earn 60,000 points** | min spend $1,000.00 | deadline 365 days | reward: 60,000 points
- ⚠️ Review items (1):
  - **fx_fee_pct**: set 2.5% from external knowledge [VERIFY]; Amex card pages do not state FX fee

### ☐ Green Card  `amex-ca-green-card`

Source: <https://www.americanexpress.com/en-ca/credit-cards/green-card/>

- Annual fee: **$0**
- Purchase APR: 21.99
- Cash advance APR: 21.99
- FX fee %: 2.5
- Earn rates: **1x points (base)**
- Welcome offer: **Earn 10,000 points** | min spend $1,000.00 | deadline 90 days | reward: 10,000 points
- ⚠️ Review items (1):
  - **fx_fee_pct**: set 2.5% from external knowledge [VERIFY]; Amex card pages do not state FX fee

### ☐ Marriott Bonvoy American Express Card  `amex-ca-marriott-bonvoy-card`

Source: <https://www.americanexpress.com/en-ca/credit-cards/marriott-bonvoy-card/>

- Annual fee: **$120.00**
- Purchase APR: 21.99
- Cash advance APR: 21.99
- FX fee %: 2.5
- Earn rates: **2x points (base), 5x points (travel_hotel)**
- Welcome offer: **Earn 80,000 points** | min spend $6,000.00 | deadline 180 days | reward: 80,000 points
  - Alternate [later_spend]: Additional earn component: 30,000 points | reward: 30,000 pts
- ⚠️ Review items (1):
  - **fx_fee_pct**: set 2.5% from external knowledge [VERIFY]

### ☐ Marriott Bonvoy Business American Express Card  `amex-ca-marriott-bonvoy-business-card`

Source: <https://www.americanexpress.com/en-ca/credit-cards/marriott-bonvoy-business-card/>

- Annual fee: **$150.00**
- Additional card fee: $50.00
- Purchase APR: 21.99
- Cash advance APR: 21.99
- FX fee %: 2.5
- Earn rates: **5x points (travel_hotel), 2x points (base), 3x points (gas), 3x points (dining), 3x points (travel_air)**
- Welcome offer: **Earn 80,000 points** | min spend $10,000.00 | deadline 180 days | reward: 80,000 points
  - Alternate [later_spend]: Additional earn component: 30,000 points | reward: 30,000 pts
- ⚠️ Review items (2):
  - **fx_fee_pct**: set 2.5% from external knowledge [VERIFY]
  - **purchase_apr**: 21.99% purchases & cash advances - frugalflyer.ca american-express-marriott-bonvoy-business [cross-check]

### ☐ SimplyCash Card from American Express  `amex-ca-simply-cash`

Source: <https://www.americanexpress.com/en-ca/credit-cards/simply-cash/>

- Annual fee: **$0**
- Purchase APR: 21.99
- Cash advance APR: 21.99
- FX fee %: 2.5
- Earn rates: **1.25% cash back (base), 2% cash back (grocery), 2% cash back (gas)**
- Welcome offer: **Earn up to $100 in bonus cash back** | min spend $2,000.00 | deadline 90 days | reward: $100.00 cash back
- ⚠️ Review items (1):
  - **fx_fee_pct**: set 2.5% from external knowledge [VERIFY]

### ☐ SimplyCash Preferred Card from American Express  `amex-ca-simply-cash-preferred`

Source: <https://www.americanexpress.com/en-ca/credit-cards/simply-cash-preferred/>

- Annual fee: **$119.88**
- Purchase APR: 21.99
- Cash advance APR: 21.99
- FX fee %: 2.5
- Earn rates: **2% cash back (base), 4% cash back (grocery), 4% cash back (gas)**
- Welcome offer: **Earn up to $200 in bonus cash back** | min spend $2,000.00 | deadline 90 days | reward: $200.00 cash back
- ⚠️ Review items (2):
  - **fx_fee_pct**: set 2.5% from external knowledge [VERIFY]
  - **annual_fee_minor**: USER-VERIFIED vs amex.ca: Card Fee $9.99/month (= $119.88 annually, non-Quebec); $119/year Quebec residents

### ☐ The Platinum Card  `amex-ca-the-platinum-card`

Source: <https://www.americanexpress.com/en-ca/charge-cards/the-platinum-card/>

- Annual fee: **$799.00**
- Additional card fee: $250.00
- Purchase APR: — (review)
- Cash advance APR: — (review)
- FX fee %: 2.5
- Earn rates: **1x points (base), 2x points (dining), 2x points (travel_other)**
- Welcome offer: **Earn 70,000 points** | min spend $10,000.00 | deadline 90 days | reward: 70,000 points
  - Alternate [later_spend]: Additional earn component: 30,000 points | reward: 30,000 pts
- ⚠️ Review items (3):
  - **fx_fee_pct**: set 2.5% from external knowledge [VERIFY]
  - **purchase_apr**: charge card - no purchase APR applicable
  - **purchase_apr**: charge card - no purchase APR (pay-in-full product) ($799 fee confirmed on page)

## cibc

### ☐ CIBC Adapta Mastercard  `cibc-adapta-mastercard`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/adapta-mastercard.html>

- Annual fee: **$0**
- Additional card fee: $0
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **1x points (base), 2x points (travel_other)**
- Welcome offer: **Earn 15,000 points** | min spend $1,000.00 | deadline 120 days | reward: 15,000 points
  - Alternate [later_spend]: Additional earn component: 9,000 points | reward: 9,000 pts
- ⚠️ Review items (2):
  - **fx_fee_pct**: set 2.5% per CIBC standard [VERIFY]
  - **purchase_apr**: 21.99%/22.99% purchases/cash - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)

### ☐ CIBC Adapta Mastercard for Students  `cibc-adapta-mastercard-for-students`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/adapta-mastercard-for-students.html>

- Annual fee: **$0**
- Additional card fee: $0
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **1x points (base), 2x points (travel_other)**
- Welcome offer: **Earn 9,000 points** | min spend $1,000.00 | deadline 120 days | reward: 9,000 points
- ⚠️ Review items (2):
  - **fx_fee_pct**: set 2.5% per CIBC standard [VERIFY]
  - **purchase_apr**: 21.99%/22.99% purchases/cash - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)

### ☐ CIBC Aeroplan Visa Business Card  `cibc-aerogold-visa-card-business`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/aerogold-visa-card-business.html>

- Annual fee: **$180.00**
- Additional card fee: $50.00
- Purchase APR: 12.99
- Cash advance APR: — (review)
- FX fee %: 2.5
- Earn rates: **1x points (base), 2x points (travel_air), 2x points (travel_hotel), 1.5x points (travel_other), 1.5x points (transit_rideshare), 1.5x points (dining)**
- Welcome offer: **Earn 75,000 points** | min spend $7,500.00 | deadline 90 days | reward: 75,000 points

### ☐ CIBC Aeroplan Visa BusinessPlusCard  `cibc-aerogold-plus-visa`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/aerogold-plus-visa.html>

- Annual fee: **$139.00**
- Additional card fee: $300.00
- Purchase APR: 20.99
- Cash advance APR: — (review)
- FX fee %: 2.5
- Earn rates: **1x points (base), 2x points (travel_air), 2x points (travel_hotel), 1.5x points (travel_other), 1.5x points (transit_rideshare), 1.5x points (dining)**
- Welcome offer: **Earn 75,000 points** | min spend $7,500.00 | deadline 90 days | reward: 75,000 points

### ☐ CIBC Aeroplan Visa Card  `cibc-aeroplan-visa-card`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/aeroplan-visa-card.html>

- Annual fee: **$0**
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **1x points (base), 1x points (grocery), 1x points (gas), 1x points (travel_air), 1x points (travel_other)**
- Welcome offer: **Earn 10,000 points** | min spend $1,500.00 | deadline 120 days | reward: 10,000 points
- ⚠️ Review items (1):
  - **purchase_apr**: 21.99%/22.99% purchases/cash - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)

### ☐ CIBC Aeroplan Visa Card for Students  `cibc-aeroplan-visa-for-students`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/aeroplan-visa-for-students.html>

- Annual fee: **$0**
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **1x points (base), 1x points (grocery), 1x points (gas), 1x points (travel_air), 1x points (travel_other)**
- Welcome offer: **Earn 10,000 points** | min spend $1,500.00 | deadline 120 days | reward: 10,000 points
- ⚠️ Review items (1):
  - **purchase_apr**: 21.99%/22.99% purchases/cash - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)

### ☐ CIBC Aeroplan Visa Infinite Card  `cibc-aeroplan-visa-infinite-card`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/aeroplan-visa-infinite-card.html>

- Annual fee: **$139.00**
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **1x points (base), 1.5x points (grocery), 1.5x points (gas), 1.5x points (travel_air), 1.5x points (travel_other), 1.5x points (travel_hotel)**
- Welcome offer: **Earn 50,000 points** | min spend $6,000.00 | deadline 180 days | reward: 50,000 points
- ⚠️ Review items (1):
  - **purchase_apr**: 21.99%/22.99% purchases/cash - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)

### ☐ CIBC Aeroplan Visa Infinite Privilege Card  `cibc-aeroplan-visa-infinite-privilege-card`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/aeroplan-visa-infinite-privilege-card.html>

- Annual fee: **$599.00**
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **1.25x points (base), 1.5x points (grocery), 1.5x points (gas), 1.5x points (dining), 1.5x points (travel_other), 2x points (travel_air), 2x points (travel_hotel)**
- Welcome offer: **Earn 100,000 points** | min spend $1,000.00 | deadline 60 days | reward: 100,000 points
- ⚠️ Review items (2):
  - **fx_fee_pct**: set 2.5% CIBC standard [VERIFY]; not stated on cached card page
  - **purchase_apr**: 21.99%/22.99% purchases/cash - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)

### ☐ CIBC Aventura Gold Visa Card  `cibc-aventura-gold-visa-card`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/aventura-gold-visa-card.html>

- Annual fee: **$139.00**
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **1x points (base), 2x points (travel_other), 1.5x points (grocery), 1.5x points (gas), 1.5x points (drugstore)**
- Welcome offer: **Earn 35,000 points** | min spend $3,000.00 | deadline 120 days | reward: 35,000 points
- ⚠️ Review items (2):
  - **fx_fee_pct**: set 2.5% CIBC standard [VERIFY]; not stated on cached card page
  - **purchase_apr**: 21.99%/22.99% purchases/cash - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)

### ☐ CIBC Aventura Visa Card  `cibc-aventura-visa-card`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/aventura-visa-card.html>

- Annual fee: **$0**
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **1x points (base), 1x points (grocery), 1x points (gas), 1x points (drugstore)**
- Welcome offer: **Earn 12,500 points** | reward: 12,500 points
- ⚠️ Review items (1):
  - **purchase_apr**: 21.99%/22.99% purchases/cash - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)

### ☐ CIBC Aventura Visa Card for Business  `cibc-aventura-visa-card-business`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/aventura-visa-card-business.html>

- Annual fee: **$139.00**
- Purchase APR: 20.99
- Cash advance APR: — (review)
- FX fee %: 2.5
- Earn rates: **1x points (base), 1.5x points (gas), 1.5x points (transit_rideshare), 1.5x points (travel_air), 1.5x points (travel_hotel), 1.5x points (travel_other)**
- Welcome offer: **Earn 70,000 points** | min spend $40,000.00 | deadline 360 days | reward: 70,000 points

### ☐ CIBC Aventura Visa Card for BusinessPlus  `cibc-aventura-plus-visa`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/aventura-plus-visa.html>

- Annual fee: **$120.00**
- Additional card fee: $300.00
- Purchase APR: 20.99
- Cash advance APR: — (review)
- FX fee %: 2.5
- Earn rates: **1x points (base), 1.5x points (gas), 1.5x points (transit_rideshare), 1.5x points (travel_air), 1.5x points (travel_hotel), 1.5x points (travel_other)**
- Welcome offer: **Earn 70,000 points** | min spend $40,000.00 | deadline 360 days | reward: 70,000 points
- ⚠️ Review items (1):
  - **annual_fee_minor**: $120 - frugalflyer.ca cibc-aventura-visa-business-plus [cross-check]

### ☐ CIBC Aventura Visa Card for Students  `cibc-aventura-visa-for-students`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/aventura-visa-for-students.html>

- Annual fee: **$0**
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **1x points (grocery), 1x points (gas), 1x points (drugstore), 1x points (travel_other), 0.5x points (base)**
- Welcome offer: **Earn 12,500 points** | reward: 12,500 points
- ⚠️ Review items (1):
  - **purchase_apr**: 21.99%/22.99% purchases/cash - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)

### ☐ CIBC Aventura Visa Infinite Card  `cibc-aventura-visa-infinite-card`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/aventura-visa-infinite-card.html>

- Annual fee: **$139.00**
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **1x points (base), 2x points (travel_other), 1.5x points (grocery), 1.5x points (gas), 1.5x points (drugstore)**
- Welcome offer: **Earn 35,000 points** | min spend $3,000.00 | deadline 120 days | reward: 35,000 points
- ⚠️ Review items (2):
  - **fx_fee_pct**: set 2.5% CIBC standard [VERIFY]; not stated on cached card page
  - **purchase_apr**: 21.99%/22.99% purchases/cash - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)

### ☐ CIBC Aventura Visa Infinite Privilege Card  `cibc-aventura-visa-infinite-privilege-card`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/aventura-visa-infinite-privilege-card.html>

- Annual fee: **$499.00**
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **1.25x points (base), 3x points (travel_other), 2x points (grocery), 2x points (gas), 2x points (dining), 2x points (transit_rideshare), 2x points (entertainment)**
- Welcome offer: **Earn 80,000 points** | min spend $3,000.00 | deadline 120 days | reward: 80,000 points
- ⚠️ Review items (2):
  - **fx_fee_pct**: set 2.5% CIBC standard [VERIFY]; not stated on cached card page
  - **purchase_apr**: 21.99%/22.99% purchases/cash - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)

### ☐ CIBC Classic Visa Card  `cibc-classic-visa-card`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/classic-visa-card.html>

- Annual fee: **$0**
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: ⚠️ none captured
- ⚠️ Review items (2):
  - **fx_fee_pct**: set 2.5% per CIBC standard [VERIFY]
  - **purchase_apr**: 21.99%/22.99% purchases/cash - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)

### ☐ CIBC Classic Visa Card for Students  `cibc-classic-visa-for-students`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/classic-visa-for-students.html>

- Annual fee: **$0**
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: ⚠️ none captured
- ⚠️ Review items (2):
  - **fx_fee_pct**: set 2.5% per CIBC standard [VERIFY]
  - **purchase_apr**: 21.99%/22.99% purchases/cash - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)

### ☐ CIBC Corporate ClassicPlusVisa Card  `cibc-corporate-classic-plus-visa`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/corporate-classic-plus-visa.html>

- Annual fee: **$20.00**
- Purchase APR: 20.99
- Cash advance APR: — (review)
- FX fee %: 2.5
- Earn rates: ⚠️ none captured
- ⚠️ Review items (3):
  - **program_slug**: corporate expense card; no consumer rewards program applies
  - **fx_fee_pct**: set 2.5% per CIBC standard [VERIFY]
  - **annual_fee_minor**: $20 VERIFIED on cibc.com corporate card page ("Annual fee $20")

### ☐ CIBC Costco Business Mastercard  `cibc-costco-mastercard-business`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/costco-mastercard-business.html>

- Annual fee: **$0**
- Purchase APR: 21.75
- Cash advance APR: 22.49
- FX fee %: 2.5
- Earn rates: **1% cash back (base), 3% cash back (dining)**
- Welcome offer: **Exclusive $100 welcome bonus** | reward: $100.00 cash back
- ⚠️ Review items (1):
  - **purchase_apr**: 21.75%/22.49% - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)

### ☐ CIBC Costco Mastercard  `cibc-costco-mastercard`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/costco-mastercard.html>

- Annual fee: **$0**
- Additional card fee: $0
- Purchase APR: 21.75
- Cash advance APR: 22.49
- FX fee %: 2.5
- Earn rates: **1% cash back (base), 3% cash back (dining), 2% cash back (gas)**
- ⚠️ Review items (3):
  - **fx_fee_pct**: set 2.5% CIBC standard [VERIFY]; not stated on cached card page
  - **purchase_apr**: 21.75%/22.49% - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)
  - **offers**: confirmed: no standing public welcome bonus as of 2026-08-24 (issuer page + frugalflyer cross-check); occasional limited-time promos only - not a churn target

### ☐ CIBC Dividend Platinum Visa Card  `cibc-dividend-visa-platinum-card`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/dividend-visa-platinum-card.html>

- Annual fee: **$99.00**
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **1% cash back (base), 3% cash back (grocery), 3% cash back (gas), 2% cash back (dining), 2% cash back (travel_other), 2% cash back (transit_rideshare), 2% cash back (recurring_bills)**
- Welcome offer: **Join and earn up to $300 in value including annual fee rebate** | min spend $2,000.00 | deadline 120 days | reward: $200.00 cash back
- ⚠️ Review items (1):
  - **purchase_apr**: 21.99%/22.99% purchases/cash - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)

### ☐ CIBC Dividend Visa Card  `cibc-dividend-visa-card`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/dividend-visa-card.html>

- Annual fee: **$0**
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **0.5% cash back (base), 2% cash back (grocery), 1% cash back (gas), 1% cash back (dining), 1% cash back (transit_rideshare), 1% cash back (travel_other)**
- ⚠️ Review items (3):
  - **fx_fee_pct**: set 2.5% CIBC standard [VERIFY]; not stated on cached card page
  - **purchase_apr**: 21.99%/22.99% purchases/cash - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)
  - **offers**: confirmed: no standing public welcome bonus as of 2026-08-24 (issuer page + frugalflyer cross-check); occasional limited-time promos only - not a churn target

### ☐ CIBC Dividend Visa Card for Students  `cibc-dividend-visa-for-students`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/dividend-visa-for-students.html>

- Annual fee: **$0**
- Purchase APR: 2.0
- Cash advance APR: — (review)
- FX fee %: 2.5
- Earn rates: **0.5% cash back (base), 2% cash back (grocery), 1% cash back (gas), 1% cash back (dining), 1% cash back (transit_rideshare), 1% cash back (travel_other)**
- Welcome offer: **Get $25 cash back after your first purchase** | reward: $25.00 cash back

### ☐ CIBC Dividend Visa Infinite Card  `cibc-dividend-visa-infinite-card`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/dividend-visa-infinite-card.html>

- Annual fee: **$120.00**
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **1% cash back (base), 4% cash back (grocery), 4% cash back (gas), 2% cash back (dining), 2% cash back (travel_other), 2% cash back (transit_rideshare), 2% cash back (recurring_bills)**
- Welcome offer: **Join and earn up to $350 in value including annual fee rebate** | min spend $2,000.00 | deadline 120 days | reward: $250.00 cash back
- ⚠️ Review items (1):
  - **purchase_apr**: 21.99%/22.99% purchases/cash - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)

### ☐ CIBC Select Visa Card  `cibc-select-visa-card`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/select-visa-card.html>

- Annual fee: **$29.00**
- Purchase APR: 13.99
- Cash advance APR: 13.99
- FX fee %: 2.5
- Earn rates: ⚠️ none captured
- Welcome offer: **Balance transfer offer: 0% interest for up to 10 months + annual fee rebate**
- ⚠️ Review items (3):
  - **fx_fee_pct**: set 2.5% CIBC standard [VERIFY]; not stated on cached card page
  - **purchase_apr**: 13.99% low-rate card - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)
  - **program_slug**: no rewards: Select is a low-rate card (13.99%) - milesopedia page shows rates only with no earn section; CIBC taxonomy files it under low-interest

### ☐ CIBC U.S. Dollar Aventura Gold Visa Card  `cibc-us-dollar-aventura-gold-visa-card`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/us-dollar-aventura-gold-visa-card.html>

- Annual fee: **$35.00**
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 0.0
- Earn rates: **1x points (base)**
- Welcome offer: **Earn 2,500 points** | reward: 2,500 points
  - Alternate [later_spend]: Additional earn component: 500 points | reward: 500 pts
- ⚠️ Review items (1):
  - **purchase_apr**: 21.99%/22.99% purchases/cash - VERIFIED: CIBC Summary of Annual Interest Rates and Fees (doc 11995-2026/08, cibc.com)

### ☐ CIBC bizline Visa Card  `cibc-bizline-visa-card`

Source: <https://www.cibc.com/en/personal-banking/credit-cards/all-credit-cards/bizline-visa-card.html>

- Annual fee: **$0**
- Purchase APR: — (review)
- Cash advance APR: — (review)
- FX fee %: 2.5
- Earn rates: ⚠️ none captured
- ⚠️ Review items (1):
  - **fx_fee_pct**: set 2.5% per CIBC standard [VERIFY]

## scotiabank

### ☐ ScotiaGold Passport Visa Card  `scotiabank-scotiagold-passport-card`

Source: <https://www.scotiabank.com/ca/en/personal/credit-cards/visa/scotiagold-passport-card.html>

- Annual fee: **$110.00**
- Additional card fee: $30.00
- Purchase APR: 19.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **1x points (base)**
- Welcome offer: **Earn 10,000 points** | min spend $2,000.00 | deadline 90 days | reward: 10,000 points
- ⚠️ Review items (1):
  - **fx_fee_pct**: FX fee not stated on page; 2.5% Scotia standard assumed [VERIFY]

### ☐ Scotiabank American Express Card  `scotiabank-no-fee-amex-card`

Source: <https://www.scotiabank.com/ca/en/personal/credit-cards/american-express/no-fee-amex-card.html>

- Annual fee: **$0**
- Additional card fee: $0
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **3x points (grocery), 2x points (dining), 2x points (entertainment), 1x points (travel_air), 1x points (travel_hotel), 1x points (travel_other), 1x points (base)**
- Welcome offer: **Earn 10,000 points** | min spend $1,000.00 | deadline 90 days | reward: 10,000 points
  - Alternate [later_spend]: Additional earn component: 2,500 points | reward: 2,500 pts
- ⚠️ Review items (1):
  - **fx_fee_pct**: no FX waiver stated on this card's page; 2.5% Scotia standard assumed [VERIFY]

### ☐ Scotiabank Gold American Express Card  `scotiabank-gold-card`

Source: <https://www.scotiabank.com/ca/en/personal/credit-cards/american-express/gold-card.html>

- Annual fee: **$120.00**
- Additional card fee: $29.00
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 0.0
- Earn rates: **6x points (grocery), 5x points (dining), 5x points (entertainment), 3x points (gas), 3x points (transit_rideshare), 3x points (streaming_subs), 1x points (travel_air), 1x points (travel_hotel), 1x points (travel_other), 1x points (base)**
- Welcome offer: **Earn 30,000 points** | min spend $2,000.00 | deadline 90 days | reward: 30,000 points

### ☐ Scotiabank Passport Visa Infinite + Card  `scotiabank-passport-infinite-card`

Source: <https://www.scotiabank.com/ca/en/personal/credit-cards/visa/passport-infinite-card.html>

- Annual fee: **$150.00**
- Additional card fee: $0
- Purchase APR: 20.99
- Cash advance APR: 22.99
- FX fee %: 0.0
- Earn rates: **1x points (base)**
- Welcome offer: **Earn 25,000 points** | min spend $2,000.00 | deadline 90 days | reward: 25,000 points
  - Alternate [later_spend]: Additional earn component: 10,000 points | reward: 10,000 pts
  - Alternate [later_spend]: Additional earn component: 2,000 points | reward: 2,000 pts

### ☐ Scotiabank Platinum American Express Card  `scotiabank-platinum-card`

Source: <https://www.scotiabank.com/ca/en/personal/credit-cards/american-express/platinum-card.html>

- Annual fee: **$399.00**
- Additional card fee: $99.00
- Purchase APR: 9.99
- Cash advance APR: 9.99
- FX fee %: 0.0
- Earn rates: **2x points (base)**
- Welcome offer: **Earn 60,000 points** | min spend $10,000.00 | deadline 180 days | reward: 60,000 points

### ☐ Scotiabank Scene+ Visa Card  `scotiabank-scene-card`

Source: <https://www.scotiabank.com/ca/en/personal/credit-cards/visa/scene-card.html>

- Annual fee: **$0**
- Additional card fee: $0
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **2x points (entertainment), 2x points (retail_other), 1x points (base)**
- Welcome offer: **Earn 5,000 points** | min spend $1,000.00 | deadline 90 days | reward: 5,000 points
  - Alternate [later_spend]: Additional earn component: 2,500 points | reward: 2,500 pts
- ⚠️ Review items (1):
  - **fx_fee_pct**: FX fee not stated on page; 2.5% Scotia standard assumed [VERIFY]

### ☐ Scotiabank Scene+ Visa Card (for students)  `scotiabank-scene-student-card`

Source: <https://www.scotiabank.com/ca/en/personal/credit-cards/visa/scene-student-card.html>

- Annual fee: **$0**
- Additional card fee: $0
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **2x points (entertainment), 1x points (base)**
- Welcome offer: **Earn 5,000 points** | min spend $1,000.00 | deadline 90 days | reward: 5,000 points
  - Alternate [later_spend]: Additional earn component: 2,500 points | reward: 2,500 pts
- ⚠️ Review items (1):
  - **fx_fee_pct**: FX fee not stated on page; 2.5% Scotia standard assumed [VERIFY]

## simplii

### ☐ Simplii Financial Cash Back Visa Card  `simplii-cash-back-visa`

Source: <https://www.simplii.com/en/credit-cards/cash-back-visa.html>

- Annual fee: **$0**
- Additional card fee: $0
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **4% cash back (dining), 1.5% cash back (gas), 1.5% cash back (grocery), 1.5% cash back (drugstore), 1.5% cash back (recurring_bills), 0.5% cash back (base)**
- Welcome offer: **Earn $100 cash back** | min spend $500.00 | deadline 90 days | reward: $100.00 cash back
- ⚠️ Review items (1):
  - **cash_apr**: 22.99% sourced from frugalflyer.ca (secondary) [VERIFY]

## tangerine

### ☐ Money-Back Credit Card  `tangerine-money-back-credit-card`

Source: <https://www.tangerine.ca/en/personal/spend/credit-cards/money-back-credit-card>

- Annual fee: **$0**
- Purchase APR: 20.95
- Cash advance APR: 22.95
- FX fee %: 2.5
- Earn rates: **2% cash back (base), 2% cash back (gas)**
- Welcome offer: **Earn 10% cash back for your first 2 months (up to $100)** | deadline 60 days | reward: $100.00 cash back
- ⚠️ Review items (1):
  - **purchase_apr**: corrected from issuer page: purchases 20.95%, cash advances 22.95%

### ☐ Tangerine Money-Back World Mastercard  `tangerine-world-credit-card`

Source: <https://www.tangerine.ca/en/personal/spend/credit-cards/world-credit-card>

- Annual fee: **$0**
- Purchase APR: 20.95
- Cash advance APR: 22.95
- FX fee %: 2.5
- Earn rates: **2% cash back (gas), 0.5% cash back (base)**
- Welcome offer: **Earn 10% cash back for your first 2 months (up to $100)** | deadline 60 days | reward: $100.00 cash back
- ⚠️ Review items (2):
  - **fx_fee_pct**: page states foreign currency conversion fee of ~2.5%; exact figure truncated in capture [VERIFY]
  - **purchase_apr**: corrected from issuer page: purchases 20.95%, cash advances 22.95%

### ☐ Tangerine Rewards World Elite Mastercard  `tangerine-world-elite-mastercard`

Source: <https://www.tangerine.ca/en/personal/spend/credit-cards/world-elite-mastercard>

- Annual fee: **$0**
- Purchase APR: 20.95
- Cash advance APR: 22.95
- FX fee %: 2.5
- Earn rates: **1x points (base)**
- Welcome offer: **30,000 bonus Scene+ points** | min spend $3,000.00 | deadline 90 days | reward: 30,000 points
- ⚠️ Review items (2):
  - **fx_fee_pct**: page states foreign currency conversion fee of ~2.5%; exact figure truncated in capture [VERIFY]
  - **purchase_apr**: corrected from issuer page: purchases 20.95%, cash advances 22.95%

## td

### ☐ TD Aeroplan Visa Infinite Card  `td-aeroplan-visa-infinite-card`

Source: <https://www.td.com/ca/en/personal-banking/products/credit-cards/aeroplan/aeroplan-visa-infinite-card>

- Annual fee: **$139.00**
- Additional card fee: $75.00
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **1.5x points (grocery), 1.5x points (travel_hotel), 1.5x points (gas), 1.5x points (travel_air), 1x points (base)**
- Welcome offer: **Earn up to 40,000 Aeroplan points** | min spend $3,000.00 | deadline 90 days | reward: 40,000 points
  - Alternate [later_spend]: Additional earn component: 15,000 points | reward: 15,000 pts
- ⚠️ Review items (1):
  - **fx_fee_pct**: set 2.5% TD standard [VERIFY]; not stated on cached card page

### ☐ TD Cash Back Visa Infinite Card  `td-cash-back-visa-infinite-card`

Source: <https://www.td.com/ca/en/personal-banking/products/credit-cards/cash-back/cash-back-visa-infinite-card>

- Annual fee: **$139.00**
- Additional card fee: $50.00
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **1% cash back (base), 3% cash back (grocery), 3% cash back (streaming_subs), 3% cash back (gas), 3% cash back (transit_rideshare)**
- Welcome offer: **10% Cash Back Dollars in the first 3 months** | min spend $3,500.00 | deadline 90 days | reward: $350.00 cash back
- ⚠️ Review items (1):
  - **fx_fee_pct**: FX fee not stated on cached TD pages; 2.5% TD standard assumed [VERIFY]

### ☐ TD First Class Travel Visa Infinite Card  `td-first-class-travel-visa-infinite-card`

Source: <https://www.td.com/ca/en/personal-banking/products/credit-cards/travel-rewards/first-class-travel-visa-infinite-card>

- Annual fee: **$139.00**
- Additional card fee: $50.00
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 2.5
- Earn rates: **2x points (base), 6x points (grocery), 6x points (dining), 6x points (transit_rideshare), 4x points (recurring_bills), 4x points (streaming_subs), 8x points (travel_other)**
- Welcome offer: **Earn up to $1,300 in value including up to 146,000 TD Rewards Points** | min spend $7,500.00 | deadline 180 days | reward: 146,000 points
- ⚠️ Review items (1):
  - **fx_fee_pct**: set 2.5% TD standard [VERIFY]; not stated on cached card page

### ☐ TD U.S. Dollar Visa Card  `td-us-dollar-visa-card`

Source: <https://www.td.com/ca/en/personal-banking/products/credit-cards/us-dollar/us-dollar-visa-card>

- Annual fee: **$39.00**
- Additional card fee: $0
- Purchase APR: 21.99
- Cash advance APR: 22.99
- FX fee %: 0.0
- Earn rates: ⚠️ none captured
- ⚠️ Review items (1):
  - **program_slug**: no rewards program: TD page shows no earn structure anywhere; value prop is FX-free USD spending (0% FX fee verified on page)

---

~518 facts to verify. Priority order: fees → earn rates →
welcome offers → APRs/FX. Fill FX fee once per issuer (most are 2.5%)
and propagate to every card of that issuer.
