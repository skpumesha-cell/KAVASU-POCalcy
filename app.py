    def calc_fd(self):
        try:
            d = ce.fd_compare(to_float(self.vars["fd_in"].get()), self.rates)
        except ValueError as e:
            return messagebox.showwarning("Missing Amount", str(e))
        self.vars["fd_in_msg"].set(d["message"])
        if not d["ok"]:                      # below Rs. 1,000 or not a multiple of Rs. 100
            self.results.pop("fd", None)     # keep invalid data out of the HTML report
            for _, k in ROWS_FD:
                self.vars[k].set("Invalid")
            return
        self.results["fd"] = d
        self._show(d, ROWS_FD)
