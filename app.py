"""KAVASU PostofficeCalcy - desktop calculator (Python 3.8, tkinter; runs on Windows 7+ 32/64-bit)."""
import os
import sys
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

import calc_engine as ce
import report_html

APP_TITLE = "KAVASU PostofficeCalcy"
NAVY, ORANGE = "#1B4B7F", "#F26B1D"
DEV_LINES = [
    "Designed By: Umesha H N LSGPA, Hassan Division, Karnataka 573201",
    "Contact: 9449759640  |  Email: skpumesha@gmail.com",
]


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
        self.logo = None
        try:
            self.logo = tk.PhotoImage(file=res_path("logo.png"))
        except Exception:
            pass
        self._build_header()
        self._build_tabs()
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
        tk.Label(h, text=APP_TITLE, font=("Segoe UI", 18, "bold"), fg=NAVY, bg="white").pack(
            side="left", padx=8)
        tk.Frame(self, bg=ORANGE, height=4).pack(fill="x")

    def _build_tabs(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)
        self.vars = {}
        self._calc_tab(nb, "Monthly Contribution", "Monthly Contribution (Rs.):", "monthly_in",
                       self.calc_monthly, [
            ("RD - 5 Year Maturity", "rd5"), ("RD - 10 Year (with deposits)", "rd10_with"),
            ("RD - 10 Year (without deposits)", "rd10_without"),
            ("PPF - 15 Years", "ppf"), ("SSA - 21 Years", "ssa")])
        self._calc_tab(nb, "FD Comparison", "FD Amount (Rs.):", "fd_in", self.calc_fd, [
            ("1 Year TD", "td1"), ("2 Year TD", "td2"), ("3 Year TD", "td3"), ("5 Year TD", "td5"),
            ("5 Year NSC", "nsc"), ("KVP maturity (x2)", "kvp"), ("KVP doubles in (months)", "kvp_months")])
        self._calc_tab(nb, "MIS & SCSS", "Principal Amount (Rs.):", "inc_in", self.calc_income, [
            ("MIS - Monthly interest", "mis_monthly"), ("SCSS - Quarterly interest", "scss_quarterly"),
            ("SCSS - Average monthly", "scss_monthly"),
            ("MIS interest -> RD denomination", "mis_rd_denom"),
            ("Principal + RD maturity (MIS)", "mis_rd"),
            ("SCSS interest -> RD denomination", "scss_rd_denom"),
            ("Principal + RD maturity (SCSS)", "scss_rd")], joint=True)
        self._rates_tab(nb)

    def _calc_tab(self, nb, title, prompt, key, command, rows, joint=False):
        f = ttk.Frame(nb, padding=12)
        nb.add(f, text=title)
        ttk.Label(f, text=prompt).grid(row=0, column=0, sticky="w")
        v = tk.StringVar()
        self.vars[key] = v
        e = ttk.Entry(f, textvariable=v, width=18)
        e.grid(row=0, column=1, padx=8)
        r = 1
        if joint:
            self.vars["joint"] = tk.BooleanVar()
            ttk.Checkbutton(f, text="Joint account (MIS limit Rs. 15 L)", variable=self.vars["joint"]
                            ).grid(row=1, column=0, columnspan=2, sticky="w", pady=2)
            r = 2
        ttk.Button(f, text="Calculate", command=command).grid(row=0, column=2, padx=4)
        for n, (label, k) in enumerate(rows):
            ttk.Label(f, text=label).grid(row=r + 1 + n, column=0, sticky="w", pady=2)
            sv = tk.StringVar(value="-")
            self.vars[k] = sv
            ttk.Label(f, textvariable=sv, font=("Segoe UI", 10, "bold"), width=22, anchor="e"
                      ).grid(row=r + 1 + n, column=1, columnspan=2, sticky="e")
        msg = tk.StringVar()
        self.vars[key + "_msg"] = msg
        ttk.Label(f, textvariable=msg, foreground="#C0392B", wraplength=420).grid(
            row=r + len(rows) + 2, column=0, columnspan=3, sticky="w", pady=6)
        e.bind("<Return>", lambda _e: command())

    def _rates_tab(self, nb):
        f = ttk.Frame(nb, padding=12)
        nb.add(f, text="Interest Rates")
        self.tree = ttk.Treeview(f, columns=("s", "r"), show="headings", height=11)
        self.tree.heading("s", text="Scheme")
        self.tree.heading("r", text="Rate % p.a.")
        self.tree.column("s", width=200)
        self.tree.column("r", width=110, anchor="e")
        self.tree.grid(row=0, column=0, columnspan=4)
        self.tree.bind("<<TreeviewSelect>>", self._pick_rate)
        self.sel = tk.StringVar()
        self.newrate = tk.StringVar()
        ttk.Label(f, textvariable=self.sel, width=14).grid(row=1, column=0, pady=8, sticky="w")
        ttk.Entry(f, textvariable=self.newrate, width=8).grid(row=1, column=1)
        ttk.Button(f, text="Update Rate", command=self._update_rate).grid(row=1, column=2, padx=4)
        ttk.Button(f, text="Reset Defaults", command=self._reset_rates).grid(row=1, column=3)
        self._refresh_rates()

    def _build_footer(self):
        b = ttk.Frame(self)
        b.pack(fill="x", padx=8)
        ttk.Button(b, text="Generate HTML Report", command=self.make_report).pack(side="left")
        ttk.Button(b, text="About", command=self.about).pack(side="left", padx=6)
        ttk.Button(b, text="Exit", command=self.destroy).pack(side="right")
        d = tk.Frame(self, bg="#E6EEF7")
        d.pack(fill="x", pady=(8, 0))
        for line in DEV_LINES:
            tk.Label(d, text=line, bg="#E6EEF7", font=("Segoe UI", 8)).pack()

    # ------------------------------------------------------------ calculations
    def _show(self, data, keys):
        for k in keys:
            if k in self.vars and k in data:
                val = data[k]
                self.vars[k].set(str(val) if k == "kvp_months" else ce.inr(val))

    def calc_monthly(self):
        try:
            d = ce.monthly_contribution(to_float(self.vars["monthly_in"].get()), self.rates)
        except ValueError as e:
            return messagebox.showwarning("Missing Information", str(e))
        self.results["monthly"] = d
        self._show(d, d.keys())
        self.vars["monthly_in_msg"].set(d["message"])

    def calc_fd(self):
        try:
            d = ce.fd_compare(to_float(self.vars["fd_in"].get()), self.rates)
        except ValueError as e:
            return messagebox.showwarning("Missing Amount", str(e))
        self.results["fd"] = d
        self._show(d, d.keys())

    def calc_income(self):
        try:
            d = ce.income_schemes(to_float(self.vars["inc_in"].get()), self.vars["joint"].get(), self.rates)
        except ValueError as e:
            return messagebox.showwarning("Invalid Input", str(e))
        self.results["income"] = d
        self._show(d, d.keys())
        self.vars["inc_in_msg"].set("MIS: %s\nSCSS: %s" % (d["mis_msg"], d["scss_msg"]))

    # ------------------------------------------------------------ rates
    def _refresh_rates(self):
        self.tree.delete(*self.tree.get_children())
        for k, v in self.rates.items():
            self.tree.insert("", "end", iid=k, values=(k, "%.2f" % v))

    def _pick_rate(self, _e):
        s = self.tree.selection()
        if s:
            self.sel.set(s[0])
            self.newrate.set("%.2f" % self.rates[s[0]])

    def _update_rate(self):
        k = self.sel.get()
        v = to_float(self.newrate.get())
        if not k or v <= 0 or v > 30:
            return messagebox.showwarning("Rate", "Select a scheme and enter a valid rate (e.g. 7.4).")
        self.rates[k] = v
        ce.save_rates(self.rates)
        self._refresh_rates()
        messagebox.showinfo("Update Successful", "Interest rate for [%s] updated to %.2f%%." % (k, v))

    def _reset_rates(self):
        if messagebox.askyesno("Reset", "Restore the default interest rates?"):
            self.rates = dict(ce.DEFAULT_RATES)
            ce.save_rates(self.rates)
            self._refresh_rates()

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
        box = tk.Frame(s, bg="white", highlightbackground="#1B4B7F", highlightthickness=3)
        box.pack()
        if self.logo:
            tk.Label(box, image=self.logo, bg="white").pack(padx=30, pady=(20, 6))
        tk.Label(box, text=APP_TITLE, font=("Segoe UI", 18, "bold"), fg="#1B4B7F", bg="white").pack(padx=30)
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
