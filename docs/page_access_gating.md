# Page Access Gating

This document summarizes the progression restrictions enforced across key pages and APIs of **Kingmaker's Rise**. Use it as a quick reference when testing progression-related features.

**Public Pages**: `index.html`, `signup.html`, `login.html`/`signin.html`, `legal.html` and its policy subpages. These do **not** require authentication. All other pages are protected by `authGuard.js`.

| System / Page / API | Castle Level Required? | Nobles Required? | Knights Required? | Troop Slots Enforced? | Notes |
| ----------------- | ---------------------- | ----------------- | ----------------- | -------------------- | ---------------------------- |
| **overview.html** | Display only | Display only | Display only | Display only | Show full progression state |
| **villages.html** | ✅ Enforce max villages | ✅ 1 Noble to create | ❌ | ❌ | Creating new Village requires Noble and Castle Level |
| **projects_kingdom.html** | ✅ Per project | ✅ Per project | ✅ Per project | ❌ | Each Project defines required levels |
| **alliance_projects.html** | ✅ Per project | ✅ Per project | ✅ Per project | ❌ | Alliance Projects also gated by progression |
| **quests.html** | ✅ Per quest | ✅ Per quest | ✅ Per quest | ❌ | Quest catalogue defines required progression |
| **alliance_quests.html** | ✅ Per quest | ✅ Per quest | ✅ Per quest | ❌ | Same as kingdom quests |
| **wars.html** (declare/start war) | ✅ Min level to start war | ✅ Nobles to initiate | ✅ Knights to lead | ✅ Army must fit slots | Full enforcement |
| **alliance_wars.html** | ✅ Min level to start war | ✅ Nobles to initiate | ✅ Knights to lead | ✅ Army must fit slots | Alliance War tier requires high progression |
| **train_troops.html** | ✅ To unlock unit tiers | ❌ | ✅ Required for elite units | ✅ Must fit troop slots | Cannot exceed slots |
| **kingdom_military.html** | Display only | ❌ | Display only (assigned Knights) | ✅ Must fit slots | Show slot usage |
| **diplomacy/treaties.html** | ✅ For major treaty types | ✅ Nobles to propose certain treaties | ❌ | ❌ | High diplomacy gated by Nobles and Castle |
| **policies.html** | ✅ Certain policies gated | ❌ | ❌ | ❌ | Castle Level required for policy unlocks |
| **laws.html** | ✅ Certain laws gated | ❌ | ❌ | ❌ | Castle Level required for laws |
| **market_listings.html** | ❌ | ❌ | ❌ | ❌ | Market is not gated (open economy) |
| **black_market.html** | ❌ | ❌ | ❌ | ❌ | No progression gating here |
| **temples.html** | ✅ For higher-level temples | ❌ | ❌ | ❌ | Certain temples require high Castle |

