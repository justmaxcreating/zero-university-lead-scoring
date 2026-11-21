"""Build the rep lookup page from the ranked call list.

Usage: python scripts/build_dashboard.py <call_list.csv> <out.html>
Every value on the page comes straight from the call list rows.
"""
import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def main(src, out):
    o = pd.read_csv(src, keep_default_na=False).sort_values("call_rank")
    assert len(o) == 1200 and o.account_id.is_unique
    assert (o.call_reason.str.len() > 0).all() and o.lead_score.between(0, 100).all()
    rows = [{
        "rank": int(r.call_rank), "id": r.account_id, "name": r.workspace_name, "domain": r.company_domain,
        "rep": r.rep_owner, "score": int(r.lead_score), "band": r.call_band, "reason": r.call_reason,
        "dtype": r.domain_type, "paid": bool(r.already_paid) if not isinstance(r.already_paid, str) else r.already_paid == "True",
        "plan": r.converted_plan, "since": r.conversion_date,
    } for r in o.itertuples()]
    meta = {"first": o.account_id.min(), "last": o.account_id.max(), "built": date.today().isoformat()}
    page = (ROOT / "dashboard" / "template.html").read_text().replace("/*META*/", json.dumps(meta))
    # Local copy: data embedded, opens straight from disk.
    local = page.replace("/*DATA*/null", json.dumps(rows, ensure_ascii=False))
    Path(out).write_text('<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n'
                         '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
                         + local + "</html>\n")
    # Artifact copy: page fragment plus data.json beside it.
    art = ROOT / "dashboard" / "artifact"
    art.mkdir(exist_ok=True)
    (art / "index.html").write_text(page)
    (art / "data.json").write_text("[\n" + ",\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n]\n")
    print(f"wrote {out} and {art}/: {len(rows)} accounts, {sum(r['paid'] for r in rows)} paying")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
