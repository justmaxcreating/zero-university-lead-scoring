"""Build the ranked call list: score every flagged account 0-100 from usage
signals and reply labels, assign a call band, and write a one-line reason.

Usage: python scripts/build_call_list.py <workspaces.csv> <replies.csv> <reply_labels.csv> <out.csv>
"""
import re
import sys

import pandas as pd

LABEL_ORDER = ["ready_to_buy", "evaluating", "wrong_contact", "not_now", "not_interested"]
OPT_OUT = r"Unsubscribe|remove me|stop emailing"
AUTO_REPLY = r"out of the office|travelling this week|on leave until|not monitored"
BANDS = ["Call now", "Call this week", "Nurture"]  # team bands: 80-100, 50-79, 0-49


# ---------- usage signals (max 100) ----------
def signal_points(r):
    pts = {}
    s = r.company_domain_seats
    pts["team_size"] = 30 if s >= 25 else 10 if s >= 5 else 0
    i = r.integrations_connected
    pts["integrations"] = 20 if i >= 4 else 15 if i == 3 else 5 if i == 2 else 0
    t = r.teamspaces
    pts["teamspaces"] = 15 if t >= 5 else 8 if t == 4 else 4 if t == 3 else 0
    w = r.weekly_active_users
    pts["weekly_active_users"] = 15 if w >= 40 else 10 if w >= 20 else 3 if w >= 6 else 0
    share = w / r.total_members if r.total_members else 0
    pts["active_share"] = 5 if w >= 20 and share >= 0.25 else 0
    v = r.pricing_page_visits_30d
    pts["buying_intent"] = 15 if v >= 10 else 8 if v >= 5 else 4 if v >= 3 else 0
    return pts


# ---------- reply adjustment ----------
REPLY_ADJ = {"ready_to_buy": 30, "evaluating": 15, "wrong_contact": 0, "not_now": -10, "not_interested": -25}
READY_FLOOR = 80  # an explicit request to buy always lands in Call now


# ---------- what the rep can say, keyed on the reply text ----------
def say_from_reply(body: str, label: str) -> "str | None":
    n = re.search(r"\d+", body)
    n = n.group(0) if n else None
    rules = [
        (r"order form", f"You asked for a Business order form for about {n} seats, so I can get that to you today."),
        (r"Enterprise cost", f"You asked about Enterprise for {n} users and a contract, so I'd like to walk you through both."),
        (r"needs a quote", f"Your finance lead needs a quote for {n} seats before month end, and I can send it today."),
        (r"send pricing for", f"You asked for Business pricing for about {n} seats on annual billing, so I'll go through that with you."),
        (r"process to upgrade", f"You asked how to move all {n} of your people over with SSO, so I can take you through the steps."),
        (r"volume discount", f"You asked about a volume discount above {n} seats, so let's go through pricing against your other quote."),
        (r"data residency", "You asked about EU data residency, so I'd like to cover how we handle it."),
        (r"permissions work", "You asked how permissions work across teamspaces for your security review, and I can show you."),
        (r"compare to Confluence", "You're comparing us with Confluence for engineering docs, so I'd like to show the differences."),
        (r"trialling a few", f"You're trialling tools for your {n}-person team, so I'd like to show what Notion does for wikis."),
        (r"SAML SSO", "You asked whether Business includes SAML SSO and audit logs, so I'll go through what each plan covers."),
        (r"import our Confluence", "You asked about importing Confluence spaces with page history, and I can show how migration works."),
        (r"sync with Jira", "You said Jira and Slack sync would decide it for you, so I'd like to show both integrations."),
        (r"intern here", "You pointed us to your office manager, so could you introduce us?"),
        (r"Forwarding to", "You forwarded this to your head of engineering, so I'd like to set up time with them."),
        (r"Procurement decides", "You said procurement decides at your team size, so who there should I speak to?"),
        (r"not the right person", "You mentioned your IT lead handles software purchases, so could you introduce us?"),
        (r"my own notes", "You mentioned your ops manager is the right contact, so could you introduce us?"),
        (r"budgets are frozen", "You said budgets reopen next year, so I'm checking in to plan ahead."),
        (r"planning cycle", "You said you'd revisit after your planning cycle, so I'm checking in on timing."),
        (r"mid-reorg", "You mentioned a reorg a few months ago, so I'm checking whether timing works now."),
        (r"later, just not", "You said this might be a priority later, so I'm checking whether that's now."),
        (r"free plan works|happy on free", None),
    ]
    for pattern, line in rules:
        if re.search(pattern, body, re.I):
            return line
    return None


def usage_line(r) -> str:
    return (f"Your team has {r.company_domain_seats} people on company email, {r.weekly_active_users} active each week, "
            f"across {r.teamspaces} teamspaces and {r.integrations_connected} integrations, "
            f"so I'd like to show what the team plan adds at that size.")


def main(ws_path, replies_path, labels_path, out_path):
    w = pd.read_csv(ws_path)
    w["already_paid"] = w.converted_to_paid.astype(str).str.lower() == "true"

    r = pd.read_csv(replies_path).merge(pd.read_csv(labels_path)[["reply_id", "label"]], on="reply_id")
    r["opt_out"] = r.reply_body.str.contains(OPT_OUT, case=False, regex=True)
    r["auto"] = r.reply_body.str.contains(AUTO_REPLY, case=False, regex=True)
    r = r.sort_values(["reply_received_date", "reply_id"])
    human = r[~r.auto]
    latest_human = human.groupby("account_id").last()
    latest_any = r.groupby("account_id").last()
    opted = r.groupby("account_id").opt_out.any()

    rows = []
    for _, a in w.iterrows():
        pts = signal_points(a)
        base = sum(pts.values())
        acc = a.account_id
        if acc in latest_human.index:
            reply = latest_human.loc[acc]
            label, body, date = reply.label, reply.reply_body, reply.reply_received_date
        elif acc in latest_any.index:  # only auto-replies: treat as not_now, retry later
            reply = latest_any.loc[acc]
            label, body, date = "not_now", reply.reply_body, reply.reply_received_date
        else:
            label, body, date = None, "", None
        opted_out = bool(opted.get(acc, False))
        adj = REPLY_ADJ.get(label, 0)
        score = max(0, min(100, base + adj))
        if label == "ready_to_buy":
            score = max(score, READY_FLOOR)

        override = ""
        if label == "not_interested":
            override, score = "Last reply was a no", min(score, 49)
        if opted_out:
            override, score = "Opted out of email", 0
        if a.student_signups > 0:
            override, score = f"{a.student_signups} student signups", 0
        elif a.domain_type in ("k12_school", "university") or a.industry in ("K-12 Education", "Higher Education"):
            override, score = "School or university", min(score, 15)
        elif a.domain_type != "company":
            # One-person workspaces never upgraded (0 of 307), and their buying
            # replies quote seat counts the workspace can't back up.
            override, score = "Personal email domain", 0
        if a.already_paid:
            # current_plan still says Free; converted_to_paid is the truth.
            override, score = "Already pays", 0

        band = "Call now" if score >= 80 else "Call this week" if score >= 50 else "Nurture"

        # reason
        if a.already_paid:
            reason = f"Already a paying customer: upgraded to {a.converted_plan} on {a.conversion_date}; no upgrade call needed."
        elif opted_out:
            reason = "Asked to stop emails; do not contact."
        elif a.student_signups > 0:
            reason = f"Student workspace with {a.student_signups} student sign-ups; not a team buyer, do not call."
        elif override == "School or university":
            reason = "School or university workspace; kept low under the school rule, do not call."
        elif override == "Personal email domain":
            n = re.search(r"\d+", body) if label in ("ready_to_buy", "evaluating") else None
            reason = ("Personal one-person workspace"
                      + (f"; reply mentions {n.group(0)} seats but the workspace has {a.total_members} members, "
                         "so check for a company workspace before any outreach; do not call." if n and label == "ready_to_buy"
                         else "; no company team behind it, do not call."))
        elif label == "not_interested":
            reason = "Said no or chose another tool in their last reply; don't call."
        else:
            said = say_from_reply(body, label) if label else None
            reason = said or usage_line(a)

        rows.append({
            "account_id": acc, "workspace_name": a.workspace_name, "company_domain": a.company_domain,
            "rep_owner": a.rep_owner, "lead_score": int(score), "call_band": band, "call_reason": reason,
            "reply_label": label or "no_reply", "last_reply_date": date, "opted_out": opted_out,
            "already_paid": bool(a.already_paid),
            "converted_plan": a.converted_plan if a.already_paid else "",
            "conversion_date": a.conversion_date if a.already_paid else "", "override": override,
            "signal_points": base, "reply_adjustment": adj,
            **{f"pts_{k}": v for k, v in pts.items()},
            "domain_type": a.domain_type, "industry": a.industry, "country": a.country,
            "company_domain_seats": a.company_domain_seats, "total_members": a.total_members,
            "student_signups": a.student_signups, "weekly_active_users": a.weekly_active_users,
            "teamspaces": a.teamspaces, "integrations_connected": a.integrations_connected,
            "pricing_page_visits_30d": a.pricing_page_visits_30d, "last_active_date": a.last_active_date,
        })

    out = pd.DataFrame(rows)
    out = out.sort_values(["lead_score", "pricing_page_visits_30d", "account_id"],
                          ascending=[False, False, True])
    out.insert(0, "call_rank", range(1, len(out) + 1))
    out.to_csv(out_path, index=False)
    return out


if __name__ == "__main__":
    o = main(*sys.argv[1:5])
    print(o.call_band.value_counts().reindex(BANDS).to_string())
