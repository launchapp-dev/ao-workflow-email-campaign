# Email Copywriting Guidelines

## Platform Rules

### Subject Lines
- **Max 60 characters** — critical for mobile display (most clients truncate at 60)
- **No clickbait** — subject must accurately describe email content
- **No ALL CAPS words** — use title case or sentence case only
- **No spam trigger words** — see config/compliance-rules.json spamTriggers list
- **Be specific** — "5 workflows you can automate today" beats "Automate your work"
- **Curiosity gap is OK** — but must be resolvable within the email
- **Numbers work well** — "3 teams, 30 hours saved/week" is better than vague claims
- **Avoid leading with the company name** — leads with value, not brand

### Preheaders
- **Max 100 characters** — longer text gets cut on mobile
- **Must complement the subject** — never repeat it word-for-word
- **Think of it as subject line part 2** — it appears right next to the subject in inbox
- **Avoid leaving it blank** — email clients show random body text if not set

## Segment-Specific Guidelines

### active-users
- **Tone:** Peer-to-peer, insider knowledge. They know the product. Skip the 101.
- **Assume:** They have used AO, understand agents, and are power users
- **Lead with:** New capabilities, use cases they haven't tried, community wins
- **Avoid:** Explaining what AO is. They know. Don't condescend.
- **CTA style:** Feature-forward ("Try the new workflow builder", "Explore MCP integrations")

### trial-expired
- **Tone:** Re-engagement. Acknowledge the gap. Don't be pushy.
- **Assume:** They tried AO, hit a friction point or got busy, moved on
- **Lead with:** What's changed since they left. New features, improvements, simplified onboarding.
- **Avoid:** Guilt-tripping. Don't say "you're missing out." Say "here's what's new."
- **CTA style:** Low-friction restart ("See what's changed", "Restart where you left off")

### newsletter-only
- **Tone:** Educational, discovery-oriented. They know the name but not the product.
- **Assume:** They're AI-curious, follow the space, haven't committed to a tool
- **Lead with:** Concrete use case or outcome ("Our users automate X in Y minutes")
- **Avoid:** Technical jargon, assuming familiarity with agent concepts
- **CTA style:** Low commitment ("Watch a 2-min demo", "See how it works")

### enterprise-leads
- **Tone:** Professional, ROI-focused, peer-level to engineering/ops leaders
- **Assume:** They evaluate tools for teams, care about security, compliance, scale
- **Lead with:** Team productivity, cost savings, reliability, enterprise features
- **Avoid:** Consumer-y language, startup energy, "move fast and break things" vibes
- **CTA style:** Consultative ("Schedule a 20-min walkthrough", "Talk to our team")

## Copy Structure

### Hook (opening line)
- The single most important sentence. If this doesn't land, nothing else matters.
- Pattern options:
  - Specific problem: "If your team spends more than 2 hours/week on [X], this is for you."
  - Surprising stat: "The average dev team manually handles 40% of their automatable workflows."
  - Direct announcement: "AO Workflows launches April 15. Here's what we built."
- Never start with "I" or the company name.

### Value Section
- 2-4 concrete bullet points or short paragraphs
- Each point: one feature → one benefit → one specificity
- Use numbers when possible: not "saves time" but "saves ~3 hours/week per engineer"
- For enterprise: map to outcomes they care about (uptime, cost, headcount)

### Proof Section
- Social proof: user quote, company name (with permission), or aggregate stat
- For launch emails: early access stats, beta user feedback, or launch waitlist count
- Keep it short: 1-2 lines max. Readers scan, not read.

### CTA
- One primary CTA. Never two competing CTAs.
- Button text: specific verb + outcome (not "Click here" or "Learn more")
  - Good: "Start your free trial", "Watch the 3-min demo", "Book a walkthrough"
  - Bad: "Submit", "Go", "Learn more", "Click here"
- Max 5 words in button text
- Fallback link text: slightly longer version for plain-text ("Start your free trial at ao.dev")

## Writing Style

- **Active voice** always. "We built" not "has been built."
- **Short sentences.** If it's over 20 words, break it up.
- **One idea per paragraph.** Two sentences max per paragraph in email.
- **No em dashes (—) in subject lines** — some clients render them poorly. Use hyphens instead.
- **Contractions are fine** — "we've" "you'll" "it's" make copy feel human, not corporate.
- **No ALL CAPS for emphasis** — use bold or just write with more specific language.
- **Avoid hedging language** — "might", "could", "possibly" undermine confidence.
