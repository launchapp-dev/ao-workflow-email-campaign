# Email Campaign Pipeline — Workflow Plan

## Overview

Automated end-to-end email campaign production pipeline. Takes a campaign brief (product launch, feature announcement, newsletter, etc.), segments the audience, generates personalized copy variants for A/B testing, validates CAN-SPAM/GDPR compliance, builds responsive HTML email templates, computes optimal send schedules based on timezone distribution, and produces performance tracking dashboards.

Email marketing delivers 36:1 ROI — the highest of any marketing channel. Yet campaign production is tedious: segmenting lists, writing copy variants, checking compliance, coding HTML, and scheduling sends across timezones. This pipeline automates the entire flow using filesystem MCP for data I/O, sequential-thinking MCP for strategy decisions, and command phases with python3/node for computation.

## Agents

| Agent | Model | Role |
|---|---|---|
| **campaign-strategist** | claude-opus-4-6 | High-level strategy — audience segmentation, messaging framework, A/B test design |
| **copywriter** | claude-sonnet-4-6 | Creative — writes subject lines, preheaders, body copy, CTAs per segment and variant |
| **compliance-checker** | claude-haiku-4-5 | Fast validation — CAN-SPAM, GDPR, unsubscribe links, sender identity, content rules |
| **template-builder** | claude-sonnet-4-6 | Technical — generates responsive HTML email templates from copy + brand guidelines |
| **campaign-analyst** | claude-sonnet-4-6 | Analytics — computes send schedules, generates A/B test configs, performance reports |

## Phase Pipeline

```
plan-campaign → write-copy → check-compliance ──┐
                    ↑                            │
                    └─── rework (fix-required) ──┘
                                                 │
                                            build-templates → optimize-schedule → finalize-campaign
```

## Phase Details

### 1. plan-campaign (agent: campaign-strategist)
**What:** Read the campaign brief from `config/brief.json`. Define audience segments based on subscriber data in `data/subscribers.csv`. Build a messaging framework: key value propositions per segment, tone guidelines, and A/B test hypotheses. Design the test matrix (which elements to vary: subject line, CTA, hero image, body length). Use sequential-thinking MCP for structured strategy reasoning.
**Input:** `config/brief.json` — campaign goals, product info, brand guidelines; `data/subscribers.csv` — subscriber list with segments, timezones, engagement history
**Output:** `data/campaign-strategy.json` — segments, messaging framework, A/B test matrix, tone guidelines
**MCP:** sequential-thinking for audience segmentation strategy and test design
**Decision:** verdict = `ready` | `insufficient-data` (terminates if brief or subscriber data is missing/incomplete)

### 2. write-copy (agent: copywriter)
**What:** Generate email copy variants for each segment x A/B variant combination. For each variant produce: subject line (max 60 chars), preheader text (max 100 chars), hero section copy, body copy (3 sections: hook, value, proof), CTA button text + fallback link text, and a plain-text version. If `data/compliance-feedback.json` exists (rework loop), revise flagged content while preserving approved sections.
**Input:** `data/campaign-strategy.json`, `config/brief.json`, `templates/copy-guidelines.md` (+ `data/compliance-feedback.json` if rework)
**Output:** `output/copy/` — one JSON file per segment-variant (e.g., `segment-active-variant-a.json`), `output/copy/manifest.json` — index of all variants with metadata
**Decision:** None (always advances)

### 3. check-compliance (agent: compliance-checker)
**What:** Fast validation of all copy variants against email marketing regulations and best practices:
- **CAN-SPAM:** Physical mailing address present, unsubscribe mechanism mentioned, no deceptive subject lines, sender identity clear
- **GDPR:** Consent language appropriate, data processing disclosure, right-to-unsubscribe honored
- **Best practices:** No spam trigger words in subject lines, image-to-text ratio guidance, link count within limits, mobile-friendly text length
- **Brand:** Copy aligns with tone guidelines from strategy

Check each variant independently. Produce per-variant compliance reports.
**Input:** `output/copy/`, `data/campaign-strategy.json`, `config/compliance-rules.json`
**Output:** `data/compliance-report.json` — per-variant pass/fail with specific issues; `data/compliance-feedback.json` (only if rework — specific revision instructions per variant)
**Decision:** verdict = `compliant` | `fix-required` | `blocked`
  - `compliant` → proceed to build templates
  - `fix-required` → loop back to write-copy with per-variant feedback (max 3 attempts)
  - `blocked` → terminate (fundamental compliance issue that cannot be fixed, e.g., missing required legal entity info)

### 4. build-templates (agent: template-builder)
**What:** Generate responsive HTML email templates for each copy variant. Templates must:
- Work across major email clients (Gmail, Outlook, Apple Mail, Yahoo)
- Use table-based layout for Outlook compatibility
- Include dark mode support via `@media (prefers-color-scheme: dark)`
- Inline critical CSS
- Include plain-text fallback (already generated in write-copy)
- Use placeholder tokens for personalization fields ({{first_name}}, {{company}}, etc.)
- Include tracking pixel placeholder and UTM-tagged links

Read brand config from `config/brand.json` for colors, fonts, logo URL, footer content.
**Input:** `output/copy/`, `config/brand.json`, `templates/base-email.html`
**Output:** `output/templates/` — one HTML file per variant, `output/templates/preview-index.html` — browser-viewable preview of all templates
**MCP:** filesystem for writing HTML files

### 5. optimize-schedule (agent: campaign-analyst)
**What:** Compute optimal send times using subscriber timezone distribution and engagement history. Use command phase with python3 to:
- Parse subscriber timezones from `data/subscribers.csv`
- Calculate per-timezone send windows (optimal: 9-11 AM local, avoid weekends)
- Generate a send schedule that batches by timezone
- Create A/B test configuration: test group size (10-20% of each segment), winner criteria (open rate or click rate), test duration (4-24 hours), auto-send winner timing

**Input:** `data/subscribers.csv`, `data/campaign-strategy.json`
**Output:** `output/schedule.json` — per-timezone batch send times; `output/ab-test-config.json` — test parameters, group assignments, winner criteria
**Command phase:** python3 script for timezone calculations and engagement scoring

### 6. finalize-campaign (agent: campaign-analyst)
**What:** Assemble the final campaign package. Generate a comprehensive campaign summary with:
- Campaign overview (brief recap, segment counts, variant counts)
- Copy variant summary table (subject lines, preheaders, word counts)
- Compliance status (all-clear confirmation)
- Template preview links
- Send schedule visualization (timezone distribution chart as ASCII/text)
- A/B test plan summary
- Estimated metrics (based on historical engagement rates from subscriber data)
- Pre-flight checklist (all items that should be verified before sending)

**Input:** All `output/` and `data/` files
**Output:** `output/campaign-summary.md` — human-readable campaign report, `output/campaign-package.json` — machine-readable bundle metadata

## MCP Servers Needed

| Server | Package | Purpose |
|---|---|---|
| filesystem | `@modelcontextprotocol/server-filesystem` | Read config/data files, write output artifacts |
| sequential-thinking | `@modelcontextprotocol/server-sequential-thinking` | Strategy reasoning for segmentation, messaging framework, test design |

## Directory Structure

```
email-campaign/
├── .ao/workflows/
│   ├── agents.yaml
│   ├── phases.yaml
│   ├── workflows.yaml
│   ├── mcp-servers.yaml
│   └── schedules.yaml
├── config/
│   ├── brief.json              # INPUT: campaign goals, product info, brand voice
│   ├── brand.json              # Brand colors, fonts, logo URL, footer
│   └── compliance-rules.json   # CAN-SPAM/GDPR rules and spam trigger words
├── data/                       # Runtime intermediate files
│   ├── subscribers.csv         # Subscriber list (segment, timezone, engagement)
│   └── .gitkeep
├── output/                     # Final artifacts
│   ├── copy/                   # Copy variants (JSON per segment-variant)
│   │   └── .gitkeep
│   ├── templates/              # HTML email templates
│   │   └── .gitkeep
│   └── .gitkeep
├── templates/
│   ├── copy-guidelines.md      # Copywriting rules per platform/segment
│   └── base-email.html         # Base HTML email template skeleton
├── scripts/
│   └── optimize-schedule.py    # Python script for timezone/engagement calculations
├── sample-data/
│   ├── sample-brief.json       # Demo campaign brief
│   ├── sample-subscribers.csv  # Demo subscriber list
│   └── sample-brand.json       # Demo brand config
├── CLAUDE.md
└── README.md
```

## Workflow Features Demonstrated

- **Multi-agent pipeline** — 5 agents with distinct specializations (opus for strategy, sonnet for creative/technical, haiku for fast validation)
- **Multi-model routing** — Opus for high-stakes strategy decisions, Sonnet for creative copy and HTML generation, Haiku for fast compliance checks
- **Decision contracts** — strategist gates on data sufficiency; compliance checker gates on regulatory readiness
- **Rework loops** — compliance failures loop back to copywriter with per-variant feedback (max 3 attempts)
- **Command phases** — python3 for timezone optimization and engagement scoring computations
- **Output contracts** — structured copy variants, HTML templates, send schedules, A/B test configs, campaign summaries
- **Phase routing** — early termination on insufficient data or blocked compliance; rework on fix-required
- **Sequential-thinking MCP** — structured reasoning for audience segmentation and messaging strategy
- **Scheduled runs** — daily check for new campaign briefs to process

## Sample Input (config/brief.json)

```json
{
  "campaign_name": "Spring Product Launch 2026",
  "campaign_type": "product-launch",
  "product": {
    "name": "AO Workflows",
    "tagline": "Automate any business process with AI agents",
    "key_features": [
      "Multi-agent orchestration",
      "Visual workflow builder",
      "50+ pre-built templates"
    ],
    "launch_date": "2026-04-15"
  },
  "goals": {
    "primary": "Drive free trial signups",
    "secondary": "Educate on use cases",
    "target_open_rate": 0.25,
    "target_click_rate": 0.05
  },
  "audience": {
    "total_subscribers": 15000,
    "segments": ["active-users", "trial-expired", "newsletter-only", "enterprise-leads"],
    "exclusions": ["unsubscribed", "bounced"]
  },
  "brand_voice": {
    "tone": "confident, clear, developer-friendly",
    "avoid": ["hype", "buzzwords", "ALL CAPS subjects"],
    "cta_style": "direct and specific"
  },
  "sender": {
    "from_name": "AO Team",
    "from_email": "team@ao.dev",
    "reply_to": "hello@ao.dev",
    "physical_address": "548 Market St, Suite 95000, San Francisco, CA 94104"
  },
  "ab_test": {
    "elements_to_test": ["subject_line", "cta_text"],
    "test_percentage": 15,
    "winner_metric": "click_rate",
    "test_duration_hours": 6
  }
}
```

## Sample Output (output/copy/manifest.json)

```json
{
  "campaign": "Spring Product Launch 2026",
  "generated_at": "2026-03-31T14:00:00Z",
  "variants": [
    {
      "segment": "active-users",
      "variant": "A",
      "file": "segment-active-variant-a.json",
      "subject_line": "You asked, we built: AO Workflows is here",
      "subject_chars": 47,
      "preheader": "Multi-agent orchestration for any business process",
      "body_word_count": 185,
      "cta_text": "Start your free trial",
      "compliance_status": "pass"
    },
    {
      "segment": "active-users",
      "variant": "B",
      "file": "segment-active-variant-b.json",
      "subject_line": "Your workflows, automated — AO launches April 15",
      "subject_chars": 52,
      "preheader": "50+ templates. Zero manual steps.",
      "body_word_count": 172,
      "cta_text": "Try AO free for 14 days",
      "compliance_status": "pass"
    },
    {
      "segment": "trial-expired",
      "variant": "A",
      "file": "segment-trial-expired-variant-a.json",
      "subject_line": "We've rebuilt AO from the ground up",
      "subject_chars": 38,
      "preheader": "Everything you wished the old version had",
      "body_word_count": 198,
      "cta_text": "See what's new",
      "compliance_status": "pass"
    }
  ],
  "total_variants": 8,
  "segments_covered": 4,
  "compliance": {
    "all_passed": true,
    "review_attempts": 1
  }
}
```

## Sample Output (output/campaign-summary.md)

```markdown
# Campaign Summary: Spring Product Launch 2026

**Generated:** 2026-03-31 | **Launch Date:** 2026-04-15 | **Status:** Ready to Send

## Audience

| Segment | Subscribers | Engagement Tier |
|---|---|---|
| Active Users | 4,200 | High |
| Trial Expired | 3,100 | Medium |
| Newsletter Only | 5,800 | Low |
| Enterprise Leads | 1,900 | High |
| **Total** | **15,000** | — |

## Copy Variants (8 total)

| Segment | Variant | Subject Line | CTA |
|---|---|---|---|
| Active Users | A | You asked, we built: AO Workflows is here | Start your free trial |
| Active Users | B | Your workflows, automated — AO launches April 15 | Try AO free for 14 days |
| Trial Expired | A | We've rebuilt AO from the ground up | See what's new |
| Trial Expired | B | The workflow tool you tried just got 10x better | Restart your trial |
| Newsletter Only | A | Introducing AO Workflows | Learn more |
| Newsletter Only | B | Automate any business process — no code required | Watch the demo |
| Enterprise Leads | A | AO Workflows: enterprise automation, simplified | Book a demo |
| Enterprise Leads | B | Your team's processes, running on autopilot | Schedule a walkthrough |

## Compliance: All Clear
- CAN-SPAM: Physical address included, unsubscribe link present
- GDPR: Consent language verified, data processing disclosed
- Spam triggers: None detected in subject lines

## Send Schedule

| Timezone Batch | Subscribers | Send Time (UTC) |
|---|---|---|
| US East (ET) | 6,200 | 2026-04-15 13:00 |
| US West (PT) | 3,800 | 2026-04-15 16:00 |
| Europe (CET) | 2,100 | 2026-04-15 08:00 |
| Asia-Pacific (JST) | 1,500 | 2026-04-15 00:00 |
| Other | 1,400 | 2026-04-15 14:00 |

## A/B Test Plan
- **Test elements:** Subject line, CTA text
- **Test group:** 15% of each segment (~2,250 subscribers)
- **Duration:** 6 hours
- **Winner metric:** Click rate
- **Auto-send winner:** After test window closes

## Pre-Flight Checklist
- [ ] Verify sender domain SPF/DKIM records
- [ ] Test email rendering in Litmus/Email on Acid
- [ ] Confirm unsubscribe link works
- [ ] Review plain-text fallback version
- [ ] Validate all UTM tracking parameters
- [ ] Load test sending infrastructure for 15K batch
```
