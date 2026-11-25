"""HTML report - fits half of an A4 sheet (A4 cut horizontally = 210 x 148 mm). No developer name."""
import datetime
import html
import os

from calc_engine import inr


def _amt(n):
    return inr(n) if n else "Invalid"


def _rows(pairs):
    return "".join("<tr><td>%s</td><td class='v'>%s</td></tr>" % (html.escape(a), html.escape(b))
                   for a, b in pairs)


def _section(num, title, pairs, note=None):
    n = "<div class='note'>%s</div>" % html.escape(note) if note else ""
    return ("<div class='sec'><h2>%d. %s</h2><table>%s</table>%s</div>"
            % (num, html.escape(title), _rows(pairs), n))


def build_html(results):
    left, right = [], []
    m, f, i = results.get("monthly"), results.get("fd"), results.get("income")
    if m:
        left.append(_section(1, "Monthly Contribution Schemes", [
            ("Monthly Investment", inr(m["monthly"])),
            ("RD - 5 Year Maturity", _amt(m["rd5"])),
            ("RD - 10 Year (with deposits)", _amt(m["rd10_with"])),
            ("RD - 10 Year (without further deposits)", _amt(m["rd10_without"])),
            ("PPF - 15 Years", _amt(m["ppf"])),
            ("SSA - 21 Years", _amt(m["ssa"])),
        ], None if m["ok"] else m["message"].replace("\n", " ")))
    if f:
        right.append(_section(2, "FD & Certificate Comparison (Amount: %s)" % inr(f["amount"]), [
            ("1 Year TD", inr(f["td1"])), ("2 Year TD", inr(f["td2"])),
            ("3 Year TD", inr(f["td3"])), ("5 Year TD", inr(f["td5"])),
            ("5 Year NSC", inr(f["nsc"])),
            ("KVP (doubles in %d months)" % f["kvp_months"], inr(f["kvp"])),
        ]))
    if i:
        left.append(_section(3, "Regular Income - MIS & SCSS (Principal: %s)" % inr(i["principal"]), [
            ("MIS - Monthly Interest", inr(i["mis_monthly"]) if i["mis_monthly"] else "Invalid"),
            ("SCSS - Quarterly Interest", inr(i["scss_quarterly"]) if i["scss_quarterly"] else "Invalid"),
            ("SCSS - Average Monthly But payable Qly only", inr(i["scss_monthly"]) if i["scss_monthly"] else "Invalid"),
        ], "MIS limit: Rs. 9 L single / Rs. 15 L joint. SCSS limit: Rs. 30 L."))
        right.append(_section(4, "Interest Routed to 5-Year RD", [
            ("MIS to SB to RD - RD denomination", inr(i["mis_rd_denom"])),
            ("MIS to SB to RD - Principal + RD maturity", inr(i["mis_rd"])),
            ("SCSS to SB to RD - RD denomination", inr(i["scss_rd_denom"])),
            ("SCSS to SB to RD - Principal + RD maturity", inr(i["scss_rd"])),
        ]))

    today = datetime.date.today().strftime("%d-%m-%Y")
    page = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Post Office Investment Plan Summary</title>
<style>
@page { size: A5 landscape; margin: 5mm; }          /* A5 landscape = 210 x 148 mm = half of A4 */
* { box-sizing: border-box; }
body { margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 9pt; color: #111; background:#e9e9e9; }
.page { width: 210mm; height: 148mm; margin: 6px auto; background: #fff; padding: 5mm; overflow: hidden; }
header { display:flex; justify-content:space-between; align-items:baseline; border-bottom: 2px solid #1B4B7F; padding-bottom: 1.5mm; }
header h1 { font-size: 12.5pt; margin: 0; color: #1B4B7F; letter-spacing: .3px; }
header .d { font-size: 9pt; }
.intro { margin: 1.5mm 0 2mm; font-size: 8.5pt; color:#333; }
.cols { display:grid; grid-template-columns: 1fr 1fr; gap: 4mm; }
.sec { margin-bottom: 3mm; }
h2 { font-size: 9.5pt; margin: 0 0 1mm; background:#E6EEF7; padding: 1mm 2mm; border-left: 3px solid #1B4B7F; }
table { width:100%; border-collapse: collapse; }
td { padding: 0.9mm 2mm; border-bottom: 1px solid #ddd; }
td.v { text-align:right; font-weight:bold; white-space:nowrap; }
.note { font-size: 7.5pt; color:#a00; margin-top: 0.8mm; }
.foot { margin-top: 1mm; font-size: 7.5pt; color:#555; border-top:1px solid #ccc; padding-top:1mm; }
.btn { position:fixed; top:8px; right:12px; padding:6px 14px; }
@media print { body{background:#fff;} .page{margin:0; padding:0; width:auto; height:auto;} .btn{display:none;} }
</style></head><body>
<button class="btn" onclick="window.print()">Print</button>
<div class="page">
<header><h1>POST OFFICE INVESTMENT PLAN SUMMARY</h1><div class="d">Date: @@DATE@@</div></header>
<div class="intro">Investment and interest is based on dated @@DATE@@</div>
<div class="cols"><div>@@LEFT@@</div><div>@@RIGHT@@</div></div>
<div class="foot">Figures are indicative projections at the interest rates in force when calculated; actual returns are as per Post Office rules at the time of investment.</div>
</div></body></html>"""
    return (page.replace("@@DATE@@", today).replace("@@LEFT@@", "".join(left))
            .replace("@@RIGHT@@", "".join(right)))


def save_report(results, folder=None):
    folder = folder or os.path.join(os.path.expanduser("~"), "Documents", "KAVASU_PostofficeCalcy_Reports")
    os.makedirs(folder, exist_ok=True)
    name = "Investment_Plan_%s.html" % datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(build_html(results))
    return path
