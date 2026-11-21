"""Write the call list and a Notes tab into one .xlsx for Google Sheets import.

Usage: python scripts/write_call_list_sheet.py <call_list.csv> <out.xlsx>
"""
import sys
import pandas as pd

KEY_PROMPT = [
    "Build the ranked call list for all 1,200 flagged accounts.",
    "Score each account 0 to 100 from usage signals: company_domain_seats, integrations_connected, teamspaces, weekly_active_users, active share, pricing_page_visits_30d.",
    "Don't score total_members or pages_created_30d (students inflate them), current_plan (says Free for paid accounts), or the conversion columns (they are the outcome).",
    "Adjust by the latest reply from a person: ready_to_buy +30 and at least 80, evaluating +15, wrong_contact 0, not_now -10, not_interested -25. Auto-replies only count as not_now.",
    "Overrides: last reply not_interested capped at 49; opted out of email = 0; any student sign-ups = 0; school or university capped at 15; personal email domain = 0; already paying (converted_to_paid) = 0.",
    "Bands (team definition): Call now 80-100, Call this week 50-79, Nurture 0-49. Rank 1-1,200 by score, then pricing-page visits, then account_id.",
    "Reason: one sentence a rep can say on the call, based on the reply or the team's usage, never mentioning pricing-page visits. Accounts that must not be called get an internal note that says so.",
]
CHANGES = [
    ("Bands switched to the team's definition", "Call now 80-100, Call this week 50-79, Nurture 0-49 (was Call first / Call next / Nurture / Do not call). Rank is now by score alone, 1 to 1,200."),
    ("Reply labels added to the score", "The earlier score used usage signals only. The latest reply from a person now adds or subtracts points; ready_to_buy guarantees at least 80 (Call now)."),
    ("Personal email workspaces always score 0", "All 307 are one-person workspaces (1 weekly user, 1 teamspace) and none upgraded. 16 had replies quoting 17 to 140 seats and would otherwise be in Call first; their reason now says to check for a company workspace first."),
    ("Already-paying accounts score 0", "current_plan says Free for all 1,200 rows, including the 60 that paid, so converted_to_paid sets their score to 0 and their reason says they already pay."),
    ("Opt-outs score 0", "Any reply asking to unsubscribe or stop emailing sets the score to 0 and the band to Do not call."),
    ("A last reply of no is capped at 49", "Accounts whose latest reply from a person is not_interested stay in Nurture whatever their usage score, and their reason says not to call."),
    ("Domain type taken from the workspace file", "The reply export's domain_type disagrees with the workspace file on 497 of 840 replies, so it is not used."),
]


def main(src, out):
    o = pd.read_csv(src)
    t = o.head(100)
    raw = (o.signal_points + o.reply_adjustment).clip(0, 100)
    raw = raw.where(o.reply_label != "ready_to_buy", raw.clip(lower=80))
    pre = o.assign(raw=raw).sort_values(["raw", "pricing_page_visits_30d", "account_id"],
                                        ascending=[False, False, True]).head(100)
    school = ["k12_school", "university"]
    counts = [
        ("Top 100 before guardrails (score without overrides or paid/opt-out rules)",
         int(pre.already_paid.sum()), int(pre.domain_type.isin(school).sum()), int((pre.domain_type == "personal").sum())),
        ("Top 100 as imported (final call list)",
         int(t.already_paid.sum()), int(t.domain_type.isin(school).sum()), int((t.domain_type == "personal").sum())),
    ]
    bands = o.call_band.value_counts().reindex(["Call now", "Call this week", "Nurture"])

    with pd.ExcelWriter(out, engine="openpyxl") as xw:
        o.to_excel(xw, sheet_name="Call list", index=False)
        rows = [["Key prompt (excerpt)", ""]] + [["", line] for line in KEY_PROMPT] + [["", ""]]
        rows += [["Top 100 check", "Paying accounts | Schools/universities | Personal"]]
        rows += [[name, f"{p} | {s} | {pe}"] for name, p, s, pe in counts] + [["", ""]]
        rows += [["Accounts per band", ""]] + [[b, int(n)] for b, n in bands.items()] + [["", ""]]
        rows += [["Scoring changes", ""]] + [[a, b] for a, b in CHANGES]
        pd.DataFrame(rows, columns=["Item", "Detail"]).to_excel(xw, sheet_name="Notes", index=False)
        ws = xw.sheets["Notes"]
        ws.column_dimensions["A"].width = 60
        ws.column_dimensions["B"].width = 140
    for c in counts:
        print(c)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
