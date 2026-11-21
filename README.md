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
