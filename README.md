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

## Call list and rep lookup page

```bash
python scripts/build_call_list.py "Notion/<workspaces>.csv" "Notion/<replies>.csv" output/reply_labels.csv output/call_list.csv
python scripts/write_call_list_sheet.py output/call_list.csv output/call_list.xlsx
python scripts/build_dashboard.py output/call_list.csv dashboard/index.html
```

- `build_call_list.py` scores all 1,200 accounts 0 to 100 from usage signals plus the latest reply label, applies the overrides (opt-outs, students, schools, personal domains, already paying) and assigns the team bands: Call now 80-100, Call this week 50-79, Nurture 0-49. Rank is by score. Each account gets a one-line reason.
- `write_call_list_sheet.py` writes the call list plus a Notes tab (key prompt, top-100 check, scoring changes) for Google Sheets.
- `build_dashboard.py` builds the rep lookup page from `dashboard/template.html`: `dashboard/index.html` (data embedded, opens from disk) and `dashboard/artifact/` (page plus `data.json`).

The generated call list, workbook and pages hold every account's data and are gitignored.
