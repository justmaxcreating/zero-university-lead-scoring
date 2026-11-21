# Zero University: Notion free-workspace lead scoring

Scripts for scoring free Notion workspaces by likelihood to upgrade and labelling outbound email replies by buying intent.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example Notion/.env   # then add your OpenRouter key
```

The OpenRouter key is read from `OPEN_ROUTER_API_KEY`. Locally it lives in `Notion/.env`, which is gitignored. In GitHub Actions it is available as the repository secret `OPEN_ROUTER_API_KEY`.

Customer CSV exports are gitignored and stay local.

## Scripts

- `scripts/lead_score.py <workspaces.csv> <out_dir>`: scores every workspace 0 to 100 and writes `lead_scores_call_list.csv` and `lead_score_rules.csv`.
- `scripts/label_replies.py <replies.csv> <out.csv>`: labels each reply as `ready_to_buy`, `evaluating`, `not_now`, `not_interested` or `wrong_contact`, with `opt_out` and `auto_reply` flags.

Scoring rules and the integration-points check are documented in the shared Google Doc "Lead Scoring System: Free Workspaces (Q3 2026)".
- `scripts/llm_label_replies.py <replies.csv> <out.csv>`: labels replies with `nvidia/nemotron-3-ultra-550b-a55b:free` on OpenRouter using `prompts/label_replies.md`. The model sees only `reply_id` and `reply_body`; `account_id` is copied from the CSV by `reply_id`.

## Output

`output/reply_labels.csv` has one row per reply (840): `reply_id`, `account_id`, `label`, `confidence`, `rationale`. The labels were assigned by Claude following `prompts/label_replies.md`, because the free model was too slow, and match `scripts/label_replies.py` on all 840 rows.
