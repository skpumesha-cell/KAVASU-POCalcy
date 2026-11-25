"""KAVASU PostofficeCalcy - desktop calculator (Python 3.8, tkinter; runs on Windows 7+ 32/64-bit)."""
import os
import sys
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

import calc_engine as ce
import report_html

APP_TITLE = "KAVASU PostofficeCalcy"
NAVY, ORANGE, SOFT = "#1B4B7F", "#F26B1D", "#E6EEF7"
DEV_LINES = [
    "Designed By: Umesha H N LSGPA, Hassan Division, Karnataka 573201",
    "Contact: 9449759640  |  Email: skpumesha@gmail.com",
]

ROWS_MONTHLY = [("RD - 5 Year Maturity", "rd5"), ("RD - 10 Year (with deposits)", "rd10_with"),
                ("RD - 10 Year (without deposits)", "rd10_without"),
                ("PPF - 15 Years", "ppf"), ("SSA - 21 Years", "ssa")]
ROWS_FD = [("1 Year TD", "td1"), ("2 Year TD", "td2"), ("3 Year TD", "td3"), ("5 Year TD", "td5"),
           ("5 Year NSC", "nsc"), ("KVP maturity (x2)", "kvp"), ("KVP doubles in (months)", "kvp_months")]
ROWS_INCOME = [("MIS - Monthly interest", "mis_monthly"), ("SCSS - Quarterly interest", "scss_quarterly"),
               ("SCSS - Average monthly", "scss_monthly"),
               ("MIS interest -> RD denom.", "mis_rd_denom"), ("Principal + RD (MIS)", "mis_rd"),
               ("SCSS interest -> RD denom.", "scss_rd_denom"), ("Principal + RD (SCSS)", "scss_rd")]


def res_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", name)


def to_float(text):
    try:
        return float(str(text).replace(",", "").strip())
    except ValueError:
        return 0.0


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.title(APP_TITLE)
        self.resizable(False, False)
        try:
            self.iconbitmap(res_path("kavasu.ico"))
        except Exception:
            pass
        self.rates = ce.load_rates()
        self.results = {}
        self.vars = {}
        self.rate_vars = {}
        self.logo = None
        try:
            self.logo = tk.PhotoImage(file=res_path("logo.png"))
        except Exception:
            pass
        self._build_header()
        self._build_panels()
        self._build_rates()
        self._build_footer()
        self._splash()

    # ------------------------------------------------------------ layout
    def _build_header(self):
        h = tk.Frame(self, bg="white")
        h.pack(fill="x")
        try:
            self.header_logo = tk.PhotoImage(file=res_path("logo_header.png"))
            tk.Label(h, image=self.header_logo, bg="white").pack(side="left", padx=10, pady=6)
        except Exception:
            pass
        tk.Label(h, text=APP_TITLE, font=("Segoe UI", 18, "bold"), fg=NAVY, bg="white").pack(side="left", padx=8)
        tk.Frame(self, bg=ORANGE, height=4).pack(fill="x")

    def _build_panels(self):
        wrap = ttk.Frame(self, padding=(6, 6, 6, 0))
        wrap.pack(fill="both")
        self._panel(wrap, 0, "1. Monthly Contribution (RD / PPF / SSA)", "Monthly amount (Rs.):",
                    "monthly_in", self.calc_monthly, ROWS_MONTHLY)
        self._panel(wrap, 1, "2. FD Comparison (TD / NSC / KVP)", "FD amount (Rs.):",
                    "fd_in", self.calc_fd, ROWS_FD)
        self._panel(wrap, 2, "3. Regular Income (MIS & SCSS)", "Principal (Rs.):",
                    "inc_in", self.calc_income, ROWS_INCOME, joint=True)

    def _panel(self, parent, col, title, prompt, key, command, rows, joint=False):
        lf = ttk.LabelFrame(parent, text=title, padding=10)
        lf.grid(row=0, column=col, sticky="nsew", padx=4, pady=4)
        ttk.Label(lf, text=prompt).grid(row=0, column=0, sticky="w")
        v = tk.StringVar()
        self.vars[key] = v
        e = ttk.Entry(lf, textvariable=v, width=14)
        e.grid(row=0, column=1, padx=6)
        e.bind("<Return>", lambda _e: command())
        ttk.Button(lf, text="Calculate", command=command).grid(row=0, column=2)
        r = 1
        if joint:
            self.vars["joint"] = tk.BooleanVar(value=False)
            ttk.Checkbutton(lf, text="Joint account (MIS limit 15 L)", variable=self.vars["joint"]
                            ).grid(row=1, column=0, columnspan=3, sticky="w", pady=2)
            r = 2
        for n, (label, k) in enumerate(rows):
            ttk.Label(lf, text=label).grid(row=r + n, column=0, columnspan=2, sticky="w", pady=2)
            sv = tk.StringVar(value="-")
            self.vars[k] = sv
            tk.Label(lf, textvariable=sv, font=("Segoe UI", 10, "bold"), fg=NAVY, anchor="e", width=14
                     ).grid(row=r + n, column=2, sticky="e")
        msg = tk.StringVar()
        self.vars[key + "_msg"] = msg
        tk.Label(lf, textvariable=msg, fg="#C0392B", wraplength=330, justify="left", font=("Segoe UI", 8)
                 ).grid(row=r + len(rows), column=0, columnspan=3, sticky="w", pady=(6, 0))

    def _build_rates(self):
        lf = ttk.LabelFrame(self, text="4. Interest Rates (% p.a.) - edit and press Save Rates", padding=8)
        lf.pack(fill="x", padx=10, pady=6)
        for i, name in enumerate(self.rates):
            row, col = divmod(i, 6)
            ttk.Label(lf, text=name).grid(row=row * 2, column=col, padx=6, sticky="w")
            sv = tk.StringVar(value="%.2f" % self.rates[name])
            self.rate_vars[name] = sv
            ttk.Entry(lf, textvariable=sv, width=9, justify="right").grid(row=row * 2 + 1, column=col, padx=6, pady=(0, 4))
        bf = ttk.Frame(lf)
        bf.grid(row=0, column=6, rowspan=4, padx=14)
        ttk.Button(bf, text="Save Rates", command=self.save_rates).pack(fill="x", pady=2)
        ttk.Button(bf, text="Reset Defaults", command=self.reset_rates).pack(fill="x", pady=2)

    def _build_footer(self):
        b = ttk.Frame(self)
        b.pack(fill="x", padx=10)
        ttk.Button(b, text="Generate HTML Report", command=self.make_report).pack(side="left")
        ttk.Button(b, text="About", command=self.about).pack(side="left", padx=6)
        ttk.Button(b, text="Exit", command=self.destroy).pack(side="right")
        d = tk.Frame(self, bg=SOFT)
        d.pack(fill="x", pady=(8, 0))
        for line in DEV_LINES:
            tk.Label(d, text=line, bg=SOFT, font=("Segoe UI", 8)).pack()

    # ------------------------------------------------------------ rates
    def _apply_rates(self):
        new = {}
        for name, sv in self.rate_vars.items():
            v = to_float(sv.get())
            if v <= 0 or v > 30:
                messagebox.showwarning("Interest Rates", "Enter a valid rate for %s (e.g. 7.4)." % name)
                return False
            new[name] = v
        self.rates = new
        return True

    def save_rates(self):
        if self._apply_rates():
            ce.save_rates(self.rates)
            messagebox.showinfo("Update Successful", "Interest rates saved.")

    def reset_rates(self):
        if messagebox.askyesno("Reset", "Restore the default interest rates?"):
            for k, v in ce.DEFAULT_RATES.items():
                self.rate_vars[k].set("%.2f" % v)
            self._apply_rates()
            ce.save_rates(self.rates)

    # ------------------------------------------------------------ calculations
    def _show(self, data, rows):
        for _, k in rows:
            val = data[k]
            self.vars[k].set(str(val) if k == "kvp_months" else ce.inr(val))

    def calc_monthly(self):
        if not self._apply_rates():
            return
        try:
            d = ce.monthly_contribution(to_float(self.vars["monthly_in"].get()), self.rates)
        except ValueError as e:
            return messagebox.showwarning("Missing Information", str(e))
        self.results["monthly"] = d
        self._show(d, ROWS_MONTHLY)
        self.vars["monthly_in_msg"].set(d["message"])

    def calc_fd(self):
        if not self._apply_rates():
            return
        try:
            d = ce.fd_compare(to_float(self.vars["fd_in"].get()), self.rates)
        except ValueError as e:
            return messagebox.showwarning("Missing Amount", str(e))
        self.results["fd"] = d
        self._show(d, ROWS_FD)

    def calc_income(self):
        if not self._apply_rates():
            return
        try:
            d = ce.income_schemes(to_float(self.vars["inc_in"].get()), bool(self.vars["joint"].get()), self.rates)
        except ValueError as e:
            return messagebox.showwarning("Invalid Input", str(e))
        self.results["income"] = d
        self._show(d, ROWS_INCOME)
        self.vars["inc_in_msg"].set("MIS: %s\nSCSS: %s" % (d["mis_msg"], d["scss_msg"]))

    # ------------------------------------------------------------ report / about
    def make_report(self):
        if not self.results:
            return messagebox.showinfo("Report", "Please run at least one calculation first.")
        try:
            path = report_html.save_report(self.results)
            webbrowser.open("file:///" + path.replace("\\", "/"))
        except Exception as e:
            messagebox.showerror("Report Error", str(e))

    def about(self):
        messagebox.showinfo("About " + APP_TITLE, APP_TITLE + "\n\n" + "\n".join(DEV_LINES))

    def _splash(self):
        s = tk.Toplevel(self)
        s.overrideredirect(True)
        box = tk.Frame(s, bg="white", highlightbackground=NAVY, highlightthickness=3)
        box.pack()
        if self.logo:
            tk.Label(box, image=self.logo, bg="white").pack(padx=30, pady=(20, 6))
        tk.Label(box, text=APP_TITLE, font=("Segoe UI", 18, "bold"), fg=NAVY, bg="white").pack(padx=30)
        for line in DEV_LINES:
            tk.Label(box, text=line, bg="white", font=("Segoe UI", 9)).pack(padx=30)
        tk.Label(box, text="", bg="white").pack()
        s.update_idletasks()
        w, h = s.winfo_reqwidth(), s.winfo_reqheight()
        s.geometry("+%d+%d" % ((s.winfo_screenwidth() - w) // 2, (s.winfo_screenheight() - h) // 2))

        def done():
            s.destroy()
            self.deiconify()
        self.after(2200, done)


if __name__ == "__main__":
    App().mainloop()
