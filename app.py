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
               ("SCSS - Avg monthly (payable Qly only)", "scss_monthly"),
               ("MIS to SB to RD - denom.", "mis_rd_denom"), ("Principal + RD (MIS)", "mis_rd"),
               ("SCSS to SB to RD - denom.", "scss_rd_denom"), ("Principal + RD (SCSS)", "scss_rd")]


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
        tk.Label(lf, textvariable=msg, fg="#C0392B", wraplength=340, justify="left", font=("Segoe UI", 8)
                 ).grid(row=r + len(rows), column=0, columnspan=3, sticky="w", pady=(6, 0))

    def _build_rates(self):
        lf = ttk.LabelFrame(self, text="4. Interest Rates (% p.a.)", padding=8)
        lf.pack(fill="x", padx=10, pady=6)
        self.rate_vars = {}
        for i, name in enumerate(self.rates):
            row, col = divmod(i, 6)
            ttk.Label(lf, text=name).grid(row=row * 2, column=col, padx=10, sticky="w")
            sv = tk.StringVar()
            self.rate_vars[name] = sv
            tk.Label(lf, textvariable=sv, font=("Segoe UI", 10, "bold"), fg=NAVY, anchor="w"
                     ).grid(row=row * 2 + 1, column=col, padx=10, sticky="w", pady=(0, 4))
        ttk.Button(lf, text="Edit Rates", command=self.edit_rates).grid(row=0, column=6, rowspan=4, padx=16)
        self._refresh_rates()

    def _refresh_rates(self):
        for name, sv in self.rate_vars.items():
            sv.set("%.2f %%" % self.rates[name])

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

    # ------------------------------------------------------------ rates (separate edit window)
    def edit_rates(self):
        win = tk.Toplevel(self)
        win.title("Edit Interest Rates")
        win.resizable(False, False)
        win.transient(self)
        try:
            win.iconbitmap(res_path("kavasu.ico"))
        except Exception:
            pass
        ttk.Label(win, text="Enter new rates (% p.a.) and press Save", font=("Segoe UI", 9, "bold")
                  ).grid(row=0, column=0, columnspan=2, padx=12, pady=(10, 6))
        entries = {}
        for i, (name, val) in enumerate(self.rates.items()):
            ttk.Label(win, text=name).grid(row=i + 1, column=0, sticky="w", padx=(12, 6), pady=2)
            sv = tk.StringVar(value="%.2f" % val)
            entries[name] = sv
            ttk.Entry(win, textvariable=sv, width=10, justify="right").grid(row=i + 1, column=1, padx=(0, 12))

        def save():
            new = {}
            for name, sv in entries.items():
                v = to_float(sv.get())
                if v <= 0 or v > 30:
                    return messagebox.showwarning("Interest Rates", "Enter a valid rate for %s (e.g. 7.4)." % name,
                                                  parent=win)
                new[name] = v
            self.rates = new
            ce.save_rates(new)
            self._refresh_rates()
            win.destroy()
            messagebox.showinfo("Update Successful", "Interest rates saved.")

        bf = ttk.Frame(win)
        bf.grid(row=len(entries) + 1, column=0, columnspan=2, pady=10)
        ttk.Button(bf, text="Save", command=save).pack(side="left", padx=6)
        ttk.Button(bf, text="Cancel", command=win.destroy).pack(side="left", padx=6)
        win.update_idletasks()
        win.geometry("+%d+%d" % (self.winfo_rootx() + 80, self.winfo_rooty() + 80))
        win.grab_set()

    # ------------------------------------------------------------ calculations
    def _show(self, data, rows):
        for _, k in rows:
            val = data[k]
            if k == "kvp_months":
                self.vars[k].set(str(val))
            elif k in ("rd5", "rd10_with", "rd10_without", "ppf", "ssa") and not val:
                self.vars[k].set("Invalid")
            else:
                self.vars[k].set(ce.inr(val))

    def calc_monthly(self):
        try:
            d = ce.monthly_contribution(to_float(self.vars["monthly_in"].get()), self.rates)
        except ValueError as e:
            return messagebox.showwarning("Missing Information", str(e))
        self.results["monthly"] = d
        self._show(d, ROWS_MONTHLY)
        self.vars["monthly_in_msg"].set(d["message"])

    def calc_fd(self):
        try:
            d = ce.fd_compare(to_float(self.vars["fd_in"].get()), self.rates)
        except ValueError as e:
            return messagebox.showwarning("Missing Amount", str(e))
        self.results["fd"] = d
        self._show(d, ROWS_FD)

    def calc_income(self):
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
