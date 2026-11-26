FD_MIN = 1000                # TD / KVP / NSC: minimum investment Rs. 1,000
FD_MULTIPLE = 100            # ... and further investment in multiples of Rs. 100
FD_OK_MSG = "Denomination is in Proper Validation"
FD_INVALID_MSG = ("Invalid Investment for TD, NSC and KVP. "
                  "Minimum Rs. 1,000 and in multiples of Rs. 100")


def fd_compare(p, rates):
    if p <= 0:
        raise ValueError("Please enter a valid FD Amount.")
    if not (p >= FD_MIN and _mult(p, FD_MULTIPLE)):
        return {
            "td1": 0, "td2": 0, "td3": 0, "td5": 0, "nsc": 0, "kvp": 0,
            "kvp_months": 0, "amount": p,
            "ok": False, "message": FD_INVALID_MSG,
        }
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
        "ok": True, "message": FD_OK_MSG,
    }
