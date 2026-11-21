"""Label outbound email replies with the team's five buying-intent labels.

Usage: python scripts/label_replies.py <reply_export.csv> <output.csv>
"""
import sys
import pandas as pd

# Checked in order; the first match wins.
RULES = [
    ("ready_to_buy", r"order form|send a contract|needs a quote|send pricing for|process to upgrade|volume discount"),
    ("evaluating", r"data residency|permissions work|compare to Confluence|trialling a few|SAML SSO|import our Confluence|sync with Jira"),
    # Unmonitored inbox: nobody reads it, so it's the wrong contact.
    ("wrong_contact", r"intern here|Forwarding to|Procurement decides|not the right person|my own notes|not monitored"),
    # Timing replies, happy-on-free replies, and out-of-office auto-replies (retry after return date).
    ("not_now", r"later, just not|budgets are frozen|Keep me posted|mid-reorg|free plan works|happy on free|out of the office|travelling this week|on leave until"),
    # Includes competitor wins, unsubscribe requests (also suppress these) and student discount questions.
    ("not_interested", r"^Not interested|Microsoft Loop|signed with Confluence|Unsubscribe|remove me|stop emailing|student|graduate"),
]
OPT_OUT = r"Unsubscribe|remove me|stop emailing"
AUTO_REPLY = r"out of the office|travelling this week|on leave until|not monitored"


def label(body: str) -> str:
    for name, pattern in RULES:
        if pd.Series([body]).str.contains(pattern, case=False, regex=True)[0]:
            return name
    return "unlabelled"


if __name__ == "__main__":
    df = pd.read_csv(sys.argv[1])
    df["intent_label"] = df.reply_body.map(label)
    df["opt_out"] = df.reply_body.str.contains(OPT_OUT, case=False, regex=True)
    df["auto_reply"] = df.reply_body.str.contains(AUTO_REPLY, case=False, regex=True)
    df.to_csv(sys.argv[2], index=False)
    print(df.intent_label.value_counts().to_string())
