# Rep lookups for the call list page

The 10 lookups Sales Development reps will run on the call list page at the final review on 2026-12-15, and what the page must show for each. Every value must match the account's row in the ranked call list (`output/call_list.csv`, the same rows as the Google Sheet).

Bands: Call now (score 80-100), Call this week (50-79), Nurture (0-49). Account IDs use the ACC-##### format.

The "Current result" column is what the page showed when built on 2026-11-21. It will change if the call list is rebuilt.

| # | Requested by | Rep enters | Rep needs to see | Current result |
|---|---|---|---|---|
| 1 | Sofia Marquez | `ACC-10001` | Rank (of 1,200), score (0-100), call priority band, one-line reason | Rank 1,000 · score 0 · Nurture · "Personal one-person workspace; no company team behind it, do not call." |
| 2 | Ethan Brooks | `ACC-10587` | Rank, score, band and the reason, read out as the opening line | Rank 138 · score 19 · Nurture · "You asked about EU data residency, so I'd like to cover how we handle it." |
| 3 | Hannah Weiss | `ACC-11200` | Rank, score, band, reason for the last ID in the list, showing the page covers all 1,200 accounts | Rank 1,200 of 1,200 · score 0 · Nurture |
| 4 | Sofia Marquez | ` ACC-10342` (leading space) | The same account and the same four values as typing `ACC-10342` | Rank 835 · score 0 · Nurture, identical to the trimmed ID |
| 5 | Ethan Brooks | `acc-10918` (lower case) | The same account and the same four values as typing `ACC-10918` | Rank 614 · score 0 · Nurture, identical to the upper-case ID |
| 6 | Daniel Okafor | `ACC-11347` | A plain message that the account is not in this list. No crash, no blank page, no guessed score | "ACC-11347 is not in this call list. The list holds the 1,200 accounts flagged in Q3 2026 (ACC-10001 to ACC-11200), so this account has no rank, score or band." |
| 7 | Sofia Marquez | Picks an account from a dropdown or list | Rank, score, band and reason for the picked account, the same as typing its ID | "Or pick from the list" dropdown, plus workspace-name search (case and spacing ignored) |
| 8 | Ethan Brooks | Asks for the highest-ranked `university` or `k12_school` account | That account's rank, score, band and reason. Rank outside the top 100, reason mentions student sign-ups | "Highest-ranked school / student account" button: ACC-10575 · rank 567 · score 0 · Nurture · "Student workspace with 190 student sign-ups…" |
| 9 | Hannah Weiss | Filters to Call now only, sorted by rank | Only Call now accounts, ordered from rank 1 down, each with score and reason | Band filter "Call now": 33 accounts, ranks 1-33 |
| 10 | Daniel Okafor | Picks one of the 60 paying accounts (`converted_to_paid` = TRUE) | Rank, score, band and reason, plus a clear sign the account already pays. No account shows a blank reason or score | "Paying accounts (60)" dropdown. Example ACC-11038: green "Paying customer" label and banner "Already a paying customer: Enterprise since 2026-08-23. Do not pitch an upgrade." · rank 483 · score 0 · Nurture |

Screenshot of lookup 10 (ACC-11038) with the Call now filter applied: [`notes/call_list_page.webp`](call_list_page.webp). It was taken before the character-encoding fix, so separators show as "Â·" there; the current page shows "·".
