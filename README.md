# email-campaign

Automated end-to-end email campaign production pipeline — segments audiences, generates personalized copy variants, validates CAN-SPAM/GDPR compliance, builds responsive HTML templates, computes timezone-optimized send schedules, and configures statistically-sized A/B tests.

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  config/brief.json + data/subscribers.csv  (INPUT)              │
└───────────────────────────┬─────────────────────────────────────┘
                            ▼
               ┌────────────────────────┐
               │   plan-campaign        │  claude-opus-4-6
               │   campaign-strategist  │  + sequential-thinking MCP
               └────────────┬───────────┘
                            │ verdict: ready | insufficient-data
                            ▼
               ┌────────────────────────┐
               │   write-copy           │  claude-sonnet-4-6
               │   copywriter           │  8 variants (4 segs × 2)
               └────────────┬───────────┘
                            │
                 ┌──────────▼──────────┐
                 │  check-compliance   │  claude-haiku-4-5
                 │  compliance-checker │  CAN-SPAM + GDPR + spam
                 └──────────┬──────────┘
                            │
              ┌─────────────┼──────────────┐
        compliant      fix-required     blocked
              │             │               │
              │         write-copy       STOP
              │       (max 3 retries)
              ▼
               ┌────────────────────────┐
               │   build-templates      │  claude-sonnet-4-6
               │   template-builder     │  responsive HTML
               └────────────┬───────────┘
                            │
               ┌────────────▼───────────┐
               │   compute-schedule     │  python3 (command phase)
               │   timezone optimizer   │  schedule + A/B config
               └────────────┬───────────┘
                            │
               ┌────────────▼───────────┐
               │   finalize-campaign    │  gemini/gemini-2.5-flash
               │   campaign-analyst     │  summary + package
               └────────────┬───────────┘
                            │
               ┌────────────▼───────────┐
               │  manual-preflight-     │  HUMAN GATE
               │  review                │  approve before send
               └────────────────────────┘
```

## Quick Start

```bash
# 1. Clone and enter the project
cd examples/email-campaign

# 2. Configure your campaign
cp sample-data/sample-brief.json config/brief.json
# Edit config/brief.json with your campaign details

# 3. Add your subscriber list
# Replace data/subscribers.csv with your actual export
# (CSV must have: id, email, first_name, segment, timezone, open_rate, click_rate, days_since_last_open)

# 4. Configure brand identity
cp sample-data/sample-brand.json config/brand.json
# Edit config/brand.json with your brand colors, logo, and footer

# 5. Start the pipeline
ao daemon start
ao queue enqueue --title "email-campaign" --description "Spring Product Launch" --workflow-ref email-campaign-pipeline

# 6. Watch progress
ao daemon stream --pretty

# 7. Review outputs
open output/templates/preview-index.html   # All 8 email templates
cat output/campaign-summary.md             # Campaign report
```

## Agents and Roles

| Agent | Model | Role |
|---|---|---|
| **campaign-strategist** | claude-opus-4-6 | Reads brief + subscriber data, segments audience, builds messaging framework and A/B test matrix using sequential-thinking MCP |
| **copywriter** | claude-sonnet-4-6 | Generates complete email copy for each segment × variant (subject, preheader, hero, body, CTA, plain text). Revises flagged content on rework loops. |
| **compliance-checker** | claude-haiku-4-5 | Fast validation of all variants against CAN-SPAM, GDPR, spam trigger words, brand alignment. Issues per-variant feedback for rework. |
| **template-builder** | claude-sonnet-4-6 | Generates cross-client responsive HTML templates with dark mode, bulletproof CTA buttons, tracking pixels, and UTM parameters. |
| **campaign-analyst** | gemini/gemini-2.5-flash | Assembles final campaign summary, performance estimates, and pre-flight checklist. Also runs schedule and A/B config computation. |

## AO Features Demonstrated

| Feature | Where |
|---|---|
| **Multi-agent pipeline** | 5 specialized agents with distinct models (Opus, Sonnet, Haiku, Gemini) |
| **Decision contracts** | plan-campaign gates on data sufficiency; check-compliance gates on regulatory readiness |
| **Rework loops** | compliance → copywriter rework cycle (max 3 attempts) with per-variant feedback |
| **Command phases** | python3 for timezone optimization and statistical A/B test sizing |
| **Manual gates** | Pre-flight review gate before campaign goes live |
| **Phase routing** | Early termination on insufficient-data or blocked; rework on fix-required |
| **MCP integration** | sequential-thinking for strategy reasoning; filesystem for all data I/O |
| **Multiple workflows** | email-campaign-pipeline, compliance-only, reschedule |
| **Scheduled runs** | Optional daily check for new campaign briefs (disabled by default) |

## Output Files

```
output/
├── copy/
│   ├── manifest.json                           # Index of all variants
│   ├── segment-active-users-variant-a.json     # Copy per segment-variant
│   ├── segment-active-users-variant-b.json
│   ├── segment-trial-expired-variant-a.json
│   ├── segment-trial-expired-variant-b.json
│   ├── segment-newsletter-only-variant-a.json
│   ├── segment-newsletter-only-variant-b.json
│   ├── segment-enterprise-leads-variant-a.json
│   └── segment-enterprise-leads-variant-b.json
├── templates/
│   ├── preview-index.html                      # Browser preview of all templates
│   ├── segment-active-users-variant-a.html     # HTML email per variant
│   └── ...
├── schedule.json                               # Per-timezone send batches
├── ab-test-config.json                        # A/B test group assignments
├── campaign-summary.md                        # Human-readable report
└── campaign-package.json                      # Machine-readable artifact bundle
```

## Requirements

### No External API Keys Needed
This pipeline uses only local computation and AO agents. No third-party email API required.

### Tools
- `node` + `npx` — for MCP servers
- `python3` — for schedule optimization script (stdlib only, no pip installs)
- `ao` CLI — for running the daemon and workflows

### Subscriber CSV Format
```csv
id,email,first_name,company,segment,timezone,open_rate,click_rate,days_since_last_open,lifecycle_stage,country
1,alice@corp.com,Alice,Corp,active-users,US/Eastern,0.42,0.08,3,retention,US
```

Required columns: `email`, `segment`, `timezone`, `open_rate`, `click_rate`, `days_since_last_open`
Optional columns: `id`, `first_name`, `company`, `lifecycle_stage`, `country`

Supported segments: `active-users`, `trial-expired`, `newsletter-only`, `enterprise-leads`

Supported timezones: `US/Eastern`, `US/Central`, `US/Mountain`, `US/Pacific`,
`Europe/London`, `Europe/Berlin`, `Europe/Paris`, `Asia/Tokyo`, `Asia/Singapore`, `UTC`

### Campaign Brief
Edit `config/brief.json` before each campaign run. Key fields:
- `product.launch_date` — determines send date for all timezone batches
- `audience.segments` — which segments to target (must match CSV segment values)
- `ab_test.test_percentage` — % of each segment used for A/B test (15-20% recommended)
- `sender.physical_address` — REQUIRED for CAN-SPAM compliance
