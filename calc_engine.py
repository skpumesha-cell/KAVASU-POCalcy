"""KAVASU PostofficeCalcy - calculation engine (ported from the Access/VBA logic)."""
import json
import math
import os

APP_NAME = "KAVASU_PostofficeCalcy"

DEFAULT_RATES = {          # percent p.a. - editable inside the app (Interest Rates tab)
    "1 Year TD": 6.9, "2 Year TD": 7.0, "3 Year TD": 7.1, "5 Year TD": 7.5,
    "NSC": 7.7, "KVP": 7.5, "RD": 6.7, "PPF": 7.1, "SSA": 8.2,
    "MIS": 7.4, "SCSS": 8.2,
}


# ---------------------------------------------------------------- rates store
def rates_path():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    folder = os.path.join(base, "KAVASU", "POCalcy")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "rates.json")


def load_rates():
    rates = dict(DEFAULT_RATES)
    try:
        with open(rates_path(), "r", encoding="utf-8") as f:
            saved = json.load(f)
        for k in rates:
            if k in saved:
                rates[k] = float(saved[k])
    except Exception:
        pass
    return rates


def save_rates(rates):
    with open(rates_path(), "w", encoding="utf-8") as f:
        json.dump(rates, f, indent=2)


# ---------------------------------------------------------------- helpers
def inr(n):
    """Indian digit grouping: 1234567 -> 'Rs. 12,34,567'."""
    n = int(round(n))
    sign = "-" if n < 0 else ""
    s = str(abs(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return "%sRs. %s" % (sign, s)


def _mult(p, k):
    return abs(p / k - round(p / k)) < 1e-9


def _r(rates, name):
    return float(rates[name]) / 100.0


# ---------------------------------------------------------------- FD comparison
def td_maturity(p, rate, years):
    """Quarterly-compounded annual interest, paid out each year (as in the VBA)."""
    annual = round(p * ((1 + rate / 4.0) ** 4 - 1))
    return round(p + annual * years)


def fd_compare(p, rates):
    if p <= 0:
        raise ValueError("Please enter a valid FD Amount.")
    r_kvp = _r(rates, "KVP")
    return {
        "td1": td_maturity(p, _r(rates, "1 Year TD"), 1),
        "td2": td_maturity(p, _r(rates, "2 Year TD"), 2),
        "td3": td_maturity(p, _r(rates, "3 Year TD"), 3),
        "td5": td_maturity(p, _r(rates, "5 Year TD"), 5),
        "nsc": round(p * (1 + _r(rates, "NSC")) ** 5),
        "kvp": round(p * 2),
        "kvp_months": round(12 * math.log(2) / math.log(1 + r_kvp)) if r_kvp > 0 else 0,
        "amount": p,
    }


# ---------------------------------------------------------------- monthly schemes
def rd_maturity(p, rate, months):
    total = 0.0
    for m in range(1, months + 1):
        total += p * (1 + rate / 4.0) ** ((months - m + 1) / 3.0)
    return total


def _ppf_ssa(p, rate, years, deposit_years):
    bal = 0.0
    for yr in range(1, years + 1):
        run, interest = bal, 0.0
        for _ in range(12):
            if yr <= deposit_years:
                run += p
            interest += run * (rate / 12.0)
        interest = round(interest)
        bal = bal + (p * 12.0 if yr <= deposit_years else 0.0) + interest
    return bal


PPF_SSA_MONTHLY_MAX = 12500          # Rs. 1,50,000 per financial year
LIMIT_MSG = ("Invalid Investment for SSA and PPF. "
             "Maximum investment limit 1.5L per Financial Year")


def monthly_contribution(p, rates):
    if p <= 0:
        raise ValueError("Please enter a valid Monthly Contribution amount.")
    r_rd, r_ppf, r_ssa = _r(rates, "RD"), _r(rates, "PPF"), _r(rates, "SSA")
    over_limit = p > PPF_SSA_MONTHLY_MAX
    valid_rd = p >= 100 and _mult(p, 10)
    base_ssa = p >= 250 and _mult(p, 50)
    base_ppf = p >= 500 and _mult(p, 50)

    rd5 = rd10w = rd10wo = 0.0
    if valid_rd:
        rd5 = rd_maturity(p, r_rd, 60)
        rd10w = rd_maturity(p, r_rd, 120)
        rd10wo = rd5 * (1 + r_rd / 4.0) ** 20
    res = {
        "monthly": p,
        "rd5": round(rd5), "rd10_with": round(rd10w), "rd10_without": round(rd10wo),
        "ppf": round(_ppf_ssa(p, r_ppf, 15, 15)) if (base_ppf and not over_limit) else 0,
        "ssa": round(_ppf_ssa(p, r_ssa, 21, 15)) if (base_ssa and not over_limit) else 0,
    }
    denom_ok = valid_rd and base_ssa and base_ppf
    msgs = []
    if over_limit:
        msgs.append(LIMIT_MSG)
    if not denom_ok:
        msgs.append("You inserted Invalid Denomination "
                    "(RD: min 100, x10 | SSA: min 250, x50 | PPF: min 500, x50)")
    if not msgs:
        msgs.append("Denomination is in Proper Validation")
    res["ok"] = denom_ok and not over_limit
    res["message"] = "\n".join(msgs)
    return res


# ---------------------------------------------------------------- MIS & SCSS
def _rd_from_interest(monthly, rate, principal):
    if monthly < 100:
        return 0, 0
    denom = int(monthly // 10 * 10)
    return denom, round(rd_maturity(denom, rate, 60)) + principal


def income_schemes(principal, joint, rates):
    if principal <= 0:
        raise ValueError("Please enter a valid Principal Amount.")
    mis_rate, scss_rate, rd_rate = _r(rates, "MIS"), _r(rates, "SCSS"), _r(rates, "RD")

    scss_ok = principal >= 1000 and _mult(principal, 1000) and principal <= 3000000
    max_mis = 1500000 if joint else 900000
    mis_ok = principal >= 1000 and _mult(principal, 1000) and principal <= max_mis

    scss_q = round(principal * scss_rate / 12 * 3) if scss_ok else 0
    scss_m = round(principal * scss_rate / 12) if scss_ok else 0
    mis_m = round(principal * mis_rate / 12) if mis_ok else 0

    mis_denom, mis_rd = _rd_from_interest(mis_m, rd_rate, principal)
    scss_denom, scss_rd = _rd_from_interest(scss_m, rd_rate, principal)
    return {
        "principal": principal, "joint": joint,
        "mis_monthly": mis_m, "scss_quarterly": scss_q, "scss_monthly": scss_m,
        "mis_msg": "Maximum limit is 9L/Single and 15L for joint" if mis_ok else "Invalid Investment",
        "scss_msg": "Maximum limit is 30 Lakhs" if scss_ok else "Invalid Investment",
        "mis_rd_denom": mis_denom, "mis_rd": mis_rd,
        "scss_rd_denom": scss_denom, "scss_rd": scss_rd,
    }
