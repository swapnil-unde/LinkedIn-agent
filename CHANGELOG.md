# Changelog

All notable changes to this project are documented in this file.

Update this file **every time you push** to the repo. Add entries under `[Unreleased]` first, then move them to a dated version when you tag or release.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added
- (nothing yet — add your next changes here)

### Changed
- (nothing yet)

### Fixed
- (nothing yet)

---

## [2026-06-01] — Documentation split

### Added
- `README.md` — setup, usage, architecture
- `CHANGELOG.md` — version history for each push

---

## [2026-06-01] — LinkedIn full post + series polish

### Added
- `agents/linkedin/text_format.py` — escape LinkedIn “little text” reserved characters (`(`, `)`, `#`, `*`, etc.) to prevent silent truncation
- Writer few-shot examples (Stop Words, Bag of Words) in `agents/writer/prompt.py`
- Hashtags at end of posts
- “Next I'll explain” teaser (replaces “Tomorrow I'll explain”)
- Image prompt on Telegram as a **second message** after draft
- Telegram photo upload → save image → publish with post on Approve
- `topics_store.get_next_topic_in_series()` for teaser line
- `test_gemini_image.py` (optional standalone Gemini image test)

### Changed
- LinkedIn agent: text-only → **text + image** (initializeUpload → PUT → post with media)
- Image prompt: **black background** (was blue/white)
- Writer: match series format; shorter posts (~900–1100 chars); no code truncation
- Approval agent: image required before publish; topic status updates on approve/reject

### Fixed
- LinkedIn posts cutting off at `(TF)` — little-text escaping
- Telegram `409 Conflict` — `deleteWebhook` on startup, single poller reminder
- `ModuleNotFoundError: agents` when running `python agents/approval/agent.py` — `sys.path` bootstrap
- Removed post truncation in writer/LinkedIn agents (user-facing text must stay complete)

---

## [2026-05-31] — Topics JSON migration

### Added
- `topics.json` — 106 topics (Generative AI curriculum, sections 1–9)
- `topics_store.py` — load/save topics, `active` / `posted` / `rejected`
- Line-by-line topic selection: first `active` row in file order
- Topics 1–16 marked `posted`; 17+ `active`

### Changed
- Researcher: DynamoDB reads **commented out**; reads from `topics.json` instead
- `config.py`: `TOPICS_FILE`; `DYNAMODB_TABLE_NAME` deprecated in `.env.example`

### Removed
- Runtime dependency on DynamoDB for topic lookup (table optional / legacy)

---

## [Initial] — Core multi-agent pipeline

### Added
- `start.py` — entry point for research → writer → Telegram
- **Research agent** — Amazon Bedrock (Nova Pro), saves `agents/researcher/research/*.md`
- **Writer agent** — LinkedIn post generation, saves `agents/writer/post/*.md`
- **Telegram agent** — draft + Approve/Reject inline buttons
- **Approval agent** — long-polling Telegram callbacks
- **LinkedIn agent** — publish post via REST API (`w_member_social`)
- `_drafts.json` — draft metadata per `topicId`
- `config.py` + `.env.example`

---

## How to add an entry on each push

1. Edit **`[Unreleased]`** at the top with your changes under `Added`, `Changed`, `Fixed`, or `Removed`.
2. On release (or end of day), rename `[Unreleased]` to a dated section, e.g. `## [2026-06-02]`.
3. Add a fresh empty `[Unreleased]` section above it.

**Example:**

```markdown
## [Unreleased]

### Added
- Docker Compose for approval bot + cron scheduler

### Fixed
- Writer omitting hashtags on long research notes
```
