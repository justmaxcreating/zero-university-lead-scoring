# Prompt: rep lookup page for the call list

This is the request that produced `dashboard/template.html`, written out with the requirements that shaped it. It combines the original request, the reps' 10 lookups (see `notes/rep_lookups.md`), and the follow-ups to publish the page as an artifact and fix the garbled characters.

---

Build a web page from the ranked call list (`output/call_list.csv`, the same rows as the Google Sheet) that lets Sales Development reps look up any of the 1,200 flagged accounts during calls. Every value on the page must come straight from the call list row, so the page and the sheet always agree.

For every account the page shows four things: **rank** (out of 1,200), **score** (0-100), **call priority band** and the **one-line reason** the rep can read out as the opening line. Bands: Call now (80-100), Call this week (50-79), Nurture (0-49).

The page must handle these lookups:

1. **Typed account ID** (`ACC-10001`, `ACC-10587`): show the account card with rank, score, band and reason.
2. **Last ID in the list** (`ACC-11200`): works the same, showing rank 1,200 of 1,200, so the page clearly covers all accounts and not just the top rows.
3. **Leading or trailing spaces** (` ACC-10342`): find the same account with the same four values. Ignore all whitespace in IDs.
4. **Lower case** (`acc-10918`): find the same account. IDs are case-insensitive. Also accept just the five digits.
5. **ID not in the list** (`ACC-11347`, flagged after the Q3 list was built): show a plain message that the account is not in this list and has no rank, score or band. Never crash, show a blank page or guess a score.
6. **Pick instead of type**: a dropdown of all 1,200 accounts, and workspace-name search that ignores case and extra spaces. Workspace names repeat, so when several match, list them with ID, rank, rep, score and band and let the rep pick one.
7. **Highest-ranked school or student account**: one button that shows the top-ranked account with `domain_type` university or k12_school. Its rank must be outside the top 100 and its reason must mention student sign-ups.
8. **Call now only**: a band filter on the full table that shows only Call now accounts, ordered from rank 1 down, each with score and reason.
9. **Paying accounts**: a dropdown of the 60 accounts with `converted_to_paid` = TRUE. Their card must show clearly that the account already pays (a "Paying customer" label and a banner with plan and start date: "Do not pitch an upgrade."), as well as rank, score, band and reason.
10. **No blanks**: no account anywhere on the page may show a blank score or reason.

Also:

- A full table of all 1,200 accounts sorted by rank, with filters for band, rep, paying accounts only, and ID or name text. Clicking a row opens that account's card.
- A summary line at the top: total accounts, ID range, count per band, band thresholds and build date.
- Works at phone width with no sideways page scroll; the table scrolls inside its own box.
- Follows the viewer's light or dark theme, including an explicit theme choice.
- Published as a private Claude artifact: the page is a fragment (no doctype, html, head or body tags) with its own title, and the account data ships beside it as `data.json`, fetched by relative URL, because 1,200 accounts are too large to embed.
- Keep the page source ASCII-only (entities in markup, `\u` escapes in script) so separators like "·" and "–" never render as "Â·" when a server omits the charset.
- The build script (`scripts/build_dashboard.py`) generates both a local copy with the data embedded and the artifact copy. Both contain every account's data and stay out of git.
