"""Tip Calculator with Tkinter GUI

Features:
- Enter bill amount
- Choose tip with presets, slider, or custom percent
- Choose number of people to split
- Round up per-person amount
- Save/load simple history
- Light/Dark theme toggle
- Copy result to clipboard and About dialog
"""

import json
import os
import math
import time
import tkinter as tk
from tkinter import ttk, messagebox


APP_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(APP_DIR, "tip_history.json")


def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_history(entry):
    h = load_history()
    h.insert(0, entry)
    # keep last 20
    h = h[:20]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(h, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


class TipCalculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tip Calculator")
        self.resizable(False, False)
        self.style = ttk.Style(self)
        self._use_dark = False
        self._build_ui()

    def _build_ui(self):
        pad = 8
        main = ttk.Frame(self, padding=pad)
        main.grid(row=0, column=0, sticky="nsew")

        # Bill
        ttk.Label(main, text="Bill amount ($):").grid(
            row=0, column=0, sticky="w")
        self.bill_var = tk.StringVar(value="0.00")
        self.bill_entry = ttk.Entry(main, textvariable=self.bill_var, width=20)
        self.bill_entry.grid(row=0, column=1, sticky="e")

        # Currency
        ttk.Label(main, text="Currency symbol/text:").grid(row=0,
                                                           column=2, sticky="w", padx=(10, 0))
        self.currency_var = tk.StringVar(value="$")
        self.currency_entry = ttk.Entry(
            main, textvariable=self.currency_var, width=6)
        self.currency_entry.grid(row=0, column=3, sticky="w")

        # Tip presets
        ttk.Label(main, text="Tip (%):").grid(row=1, column=0, sticky="w")
        presets = ttk.Frame(main)
        presets.grid(row=1, column=1, sticky="e")
        for p in (10, 12, 15):
            b = ttk.Button(presets, text=f"{p}%",
                           command=lambda v=p: self.set_tip(v))
            b.pack(side="left", padx=2)

        # Tip slider and custom
        self.tip_var = tk.DoubleVar(value=15.0)
        # label var to display live percent
        self.tip_display_var = tk.StringVar(value=f"{self.tip_var.get():.1f}%")
        # use command callback so label updates while dragging

        def on_tip_change(val):
            try:
                v = float(val)
            except Exception:
                v = self.tip_var.get()
            self.tip_var.set(v)
            self.tip_display_var.set(f"{v:.1f}%")

        self.tip_scale = ttk.Scale(
            main, from_=0, to=50, variable=self.tip_var, orient="horizontal", command=on_tip_change)
        self.tip_scale.grid(row=2, column=0, columnspan=2,
                            sticky="we", pady=(4, 0))
        self.tip_label = ttk.Label(main, textvariable=self.tip_display_var)
        self.tip_label.grid(row=3, column=0, columnspan=2)

        # People
        ttk.Label(main, text="Split between (# people):").grid(
            row=4, column=0, sticky="w")
        self.people_var = tk.IntVar(value=1)
        self.people_spin = ttk.Spinbox(
            main, from_=1, to=100, textvariable=self.people_var, width=6)
        self.people_spin.grid(row=4, column=1, sticky="e")

        # Round up
        self.round_var = tk.BooleanVar(value=False)
        self.round_check = ttk.Checkbutton(
            main, text="Round up per person", variable=self.round_var)
        self.round_check.grid(row=5, column=0, columnspan=2, sticky="w")

        # Buttons
        actions = ttk.Frame(main)
        actions.grid(row=6, column=0, columnspan=2, pady=(6, 0))
        calc_btn = ttk.Button(actions, text="Calculate",
                              command=self.calculate)
        calc_btn.pack(side="left", padx=4)
        copy_btn = ttk.Button(actions, text="Copy Result",
                              command=self.copy_result)
        copy_btn.pack(side="left", padx=4)
        clear_btn = ttk.Button(actions, text="Clear",
                               command=self.clear_inputs)
        clear_btn.pack(side="left", padx=4)

        # Results
        res_frame = ttk.LabelFrame(main, text="Result", padding=6)
        res_frame.grid(row=7, column=0, columnspan=2, sticky="we", pady=(8, 0))
        self.result_text = tk.StringVar(value="No calculation yet")
        ttk.Label(res_frame, textvariable=self.result_text,
                  justify="left").grid(row=0, column=0)

        # History list
        hist_frame = ttk.LabelFrame(main, text="History", padding=6)
        hist_frame.grid(row=8, column=0, columnspan=2,
                        sticky="we", pady=(8, 0))
        self.history_list = tk.Listbox(hist_frame, height=5, width=50)
        self.history_list.grid(row=0, column=0)
        load_btn = ttk.Button(hist_frame, text="Load Selected",
                              command=self.load_selected_history)
        load_btn.grid(row=1, column=0, sticky="w", pady=(4, 0))

        # Bottom controls
        bottom = ttk.Frame(main)
        bottom.grid(row=9, column=0, columnspan=2, pady=(8, 0), sticky="we")
        theme_btn = ttk.Button(bottom, text="Toggle Theme",
                               command=self.toggle_theme)
        theme_btn.pack(side="left")
        about_btn = ttk.Button(bottom, text="About", command=self.show_about)
        about_btn.pack(side="right")

        # Wire events
        # already update via command; keep trace for other updates
        self.tip_var.trace_add("write", lambda *a: self._update_tip_label())

        # initialize history
        self._update_history_list()
        self._update_tip_label()

    def _tip_text(self):
        return tk.StringVar(value=f"Tip: {self.tip_var.get():.1f}%")

    def _update_tip_label(self):
        try:
            self.tip_label.config(text=f"Tip: {self.tip_var.get():.1f}%")
        except Exception:
            pass

    def set_tip(self, percent: float):
        self.tip_var.set(percent)
        self._update_tip_label()

    def calculate(self):
        # Validate inputs
        try:
            bill = float(self.bill_var.get())
        except Exception:
            messagebox.showerror(
                "Input error", "Please enter a valid bill amount.")
            return
        if bill < 0:
            messagebox.showerror(
                "Input error", "Bill amount cannot be negative.")
            return
        try:
            people = int(self.people_var.get())
            if people < 1:
                raise ValueError()
        except Exception:
            messagebox.showerror(
                "Input error", "Please enter a valid number of people (>=1).")
            return

        tip_percent = float(self.tip_var.get())
        tip_amount = bill * (tip_percent / 100.0)
        total_bill = bill + tip_amount
        per_person = total_bill / people
        if self.round_var.get():
            per_person = math.ceil(per_person * 100) / 100.0

        c = self.currency_var.get() or "$"
        result = (
            f"Bill: {c}{bill:.2f}\n"
            f"Tip ({tip_percent:.1f}%): {c}{tip_amount:.2f}\n"
            f"Total: {c}{total_bill:.2f}\n"
            f"Each (x{people}): {c}{per_person:.2f}"
        )
        self.result_text.set(result)

        # save to history
        entry = {
            "time": int(time.time()),
            "bill": round(bill, 2),
            "tip_percent": round(tip_percent, 2),
            "people": people,
            "per_person": round(per_person, 2),
            "total": round(total_bill, 2),
        }
        save_history(entry)
        self._update_history_list()

    def copy_result(self):
        txt = self.result_text.get()
        if not txt or txt == "No calculation yet":
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(txt)
            messagebox.showinfo("Copied", "Result copied to clipboard.")
        except Exception:
            messagebox.showerror("Copy failed", "Could not copy to clipboard.")

    def clear_inputs(self):
        self.bill_var.set("0.00")
        self.tip_var.set(15)
        self.people_var.set(1)
        self.round_var.set(False)
        self.result_text.set("No calculation yet")

    def _update_history_list(self):
        self.history_list.delete(0, tk.END)
        for item in load_history()[:20]:
            t = time.strftime("%Y-%m-%d %H:%M:%S",
                              time.localtime(item.get("time", 0)))
            c = self.currency_var.get() or "$"
            s = f"{t} — {c}{item.get('bill'):.2f} +{item.get('tip_percent'):.1f}% → {c}{item.get('per_person'):.2f}/pp"
            self.history_list.insert(tk.END, s)

    def load_selected_history(self):
        sel = self.history_list.curselection()
        if not sel:
            return
        idx = sel[0]
        h = load_history()
        if idx >= len(h):
            return
        item = h[idx]
        self.bill_var.set(f"{item.get('bill'):.2f}")
        self.tip_var.set(float(item.get('tip_percent', 15)))
        self.people_var.set(int(item.get('people', 1)))
        self._update_tip_label()

    def toggle_theme(self):
        # simple dark/light toggle
        if not self._use_dark:
            self.configure(bg="#2e2e2e")
            self.style.configure(
                "TLabel", background="#2e2e2e", foreground="#ffffff")
            self.style.configure("TFrame", background="#2e2e2e")
            self.style.configure("TButton", background="#444444")
            self._use_dark = True
        else:
            self.configure(bg=None)
            self.style.configure("TLabel", background=None, foreground=None)
            self.style.configure("TFrame", background=None)
            self._use_dark = False

    def show_about(self):
        messagebox.showinfo(
            "About", "Tip Calculator\nBuilt with Tkinter.\nFeatures: presets, slider, split, history, theme, copy.\nMade by shiki")


if __name__ == "__main__":
    app = TipCalculator()
    app.mainloop()
