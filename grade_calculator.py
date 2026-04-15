"""
Grade Calculator

Usage:
    python grade_calculator.py
"""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox, filedialog
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NUMERIC_CHARS = set("0123456789.")

CATEGORIES = [
    ("exam",     "Exam"),
    ("homework", "Homework"),
    ("lab",      "Lab"),
    ("quiz",     "Quiz"),
    ("inclass",  "In-Class Work"),
    ("misc",     "Miscellaneous"),
]

ABOUT_TEXT = (
    "Thank you for using the Grade Calculator application, developed by Kora Hartman.\n\n"
    "This application is provided to you, the user, without any warranty, implied or otherwise.\n\n"
    "For questions or concerns about the application, contact hartman.devs@gmail.com."
)

# ---------------------------------------------------------------------------
# Theme palette  (greyscale)
# ---------------------------------------------------------------------------

PALETTE = {
    "win_bg":       "#e8e8e8",   # root window
    "panel":        "#f4f4f4",   # tab content frames / canvas
    "nb_bar":       "#f4f4f4",   # notebook tab-bar background
    "tab_inactive": "#5e5e5e",   # unselected tab
    "tab_hover":    "#828282",   # mouse-over tab
    "tab_active":   "#f4f4f4",   # selected tab (blends into panel)
    "tab_fg":       "#e8e8e8",   # text on dark inactive/hover tabs
    "entry_bg":     "#ffffff",   # editable entry field
    "entry_ro":     "#e4e4e4",   # read-only entry field
    "fg":           "#222222",   # primary text / icons
    "btn_bg":       "#6a6a6a",   # button face
    "btn_fg":       "#ffffff",   # button label
    "btn_hover":    "#555555",   # button hover / pressed
    "sep":          "#a0a0a0",   # separator line
}


# ---------------------------------------------------------------------------
# Functions for grade calculation logic.
# ---------------------------------------------------------------------------

def parse_list(text: str) -> list[str]:
    """Split a comma-delimited string into a cleaned list of tokens."""
    return [v.strip() for v in text.replace(" ", "").split(",") if v.strip()]


def calculate_grade(weights: list[str], grades: list[str], category: str):
    """
    Return the weighted grade contribution for one category.
    Returns Decimal on success, or raises ValueError with a descriptive message.

    Rules:
      - Both empty  ->  0
      - weights empty, grades non-empty (or vice versa)  ->  error
      - more weights than grades (or vice versa)  ->  error
      - multiple weights == multiple grades  ->  sum(grade_i * weight_i)
      - other mismatch  ->  error
    """

    if not weights and not grades:
        return Decimal(0)

    if not weights:
        raise ValueError(f"ERROR: {category} grade values were given, but no {category} weight values!")
    
    if not grades:
        raise ValueError(f"ERROR: {category} weight values were given, but no {category} grade values!")

    def to_decimal(value):
        try:
            d = Decimal(value)

            if d < 0:
                raise ValueError()
            
            return d
        except (InvalidOperation, ValueError):
            raise ValueError(f"ERROR: {value!r} is not a valid numeric value!")

    if len(weights) != len(grades):
        raise ValueError(f"ERROR: The number of {category} weights must match the number of {category} grades!")

    # weights == grades
    result = Decimal(0)

    for w_str, g_str in zip(weights, grades):
        w = to_decimal(w_str)
        g = to_decimal(g_str)
        result += g * w

    return result


def calculate_total_weight(weight_lists: list) -> Decimal:
    total = Decimal(0)

    for wlist in weight_lists:
        for w in wlist:
            if w:
                total += Decimal(w)

    return total


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

class GradeCalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Grade Calculator")
        self.geometry("620x480")
        self.resizable(True, True)

        # Per-category lists of Entry widgets
        self._weight_entry_lists: dict = {}
        self._grade_entry_lists:  dict = {}
        self._row_label_lists:    dict = {}

        # Proxy objects exposing .get()/.delete()/.insert() over those lists
        self._weight_entries: dict = {}
        self._grade_entries:  dict = {}

        # State for dynamic tabs
        self._tab_next_row:    dict = {}
        self._tab_inner_frame: dict = {}

        self._apply_theme()
        self._build_menu()
        self._build_ui()

        # Let the geometry manager compute natural widget sizes first.
        self.update_idletasks()

        nb       = self._nb
        num_tabs = len(nb.tabs())

        # 1) Tkinter's own minimum: winfo_reqwidth on the notebook already accounts
        #    for the combined tab-header widths in the clam theme.
        req_based = (nb.winfo_reqwidth() + num_tabs - 1) // num_tabs if num_tabs else 80

        # 2) Font measurement fallback: text width + left/right padding (10 px each)
        #    + 8 px render buffer to prevent off-by-one clipping.
        tab_font   = tkfont.nametofont("TkDefaultFont")
        font_based = max(
            tab_font.measure(nb.tab(i, "text")) + 28
            for i in range(num_tabs)
        ) if num_tabs else 80

        # Take whichever estimate is larger so both constraints are satisfied.
        self._min_tab_w = max(req_based, font_based)

        min_win_w = self._min_tab_w * num_tabs + 12  # +12 for notebook padx + tabmargins
        self.geometry(f"{min_win_w}x480")

        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())

        # Bind after sizing is finalised so the first event sees the correct geometry.
        nb.bind("<Configure>", self._on_notebook_configure)
        self._welcome_frame.bind("<Configure>", self._on_welcome_resize)

    # ------------------------------------------------------------------
    # Proxy: adapts a list of Entry widgets to the single-widget API
    # ------------------------------------------------------------------

    class _EntryListProxy:
        def __init__(self, entries: list):
            self._entries = entries

        def get(self) -> str:
            return ", ".join(e.get() for e in self._entries if e.get().strip())

        def insert(self, _, value: str):
            parts = [v.strip() for v in value.split(",") if v.strip()]

            for i, e in enumerate(self._entries):
                e.delete(0, tk.END)

                if i < len(parts):
                    e.insert(0, parts[i])

        def delete(self, start, end):
            for e in self._entries:
                e.delete(start, end)

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _apply_theme(self):
        P = PALETTE
        style = ttk.Style(self)
        style.theme_use("clam")

        # Base defaults inherited by all ttk widgets
        style.configure(".", background=P["panel"], foreground=P["fg"])

        # Frames & labels
        style.configure("TFrame", background=P["panel"])
        style.configure("TLabel", background=P["panel"], foreground=P["fg"])

        # Entry fields
        style.configure("TEntry",
                        fieldbackground=P["entry_bg"],
                        foreground=P["fg"],
                        insertcolor=P["fg"],
                        bordercolor=P["tab_inactive"],
                        lightcolor=P["panel"],
                        darkcolor=P["panel"])
        style.map("TEntry",
                  fieldbackground=[("readonly", P["entry_ro"])],
                  foreground=[("readonly", P["fg"])])

        # Buttons
        style.configure("TButton",
                        background=P["btn_bg"],
                        foreground=P["btn_fg"],
                        bordercolor=P["btn_hover"],
                        focuscolor=P["btn_hover"],
                        lightcolor=P["btn_bg"],
                        darkcolor=P["btn_hover"],
                        padding=[8, 4])
        style.map("TButton",
                  background=[("active", P["btn_hover"]), ("pressed", P["btn_hover"])],
                  foreground=[("active", P["btn_fg"]),    ("pressed", P["btn_fg"])])


        # Separator
        style.configure("TSeparator", background=P["sep"])

        # Notebook tab bar and tabs
        style.configure("TNotebook",
                        background=P["nb_bar"],
                        tabmargins=[2, 4, 2, 0])
        style.configure("TNotebook.Tab",
                        background=P["tab_inactive"],
                        foreground=P["tab_fg"],
                        padding=[10, 4],
                        anchor="center")
        style.map("TNotebook.Tab",
                  background=[("selected", P["tab_active"]), ("active", P["tab_hover"])],
                  foreground=[("selected", P["fg"]),         ("active", "#ffffff")],
                  expand=[("selected", [1, 2, 1, 0])])

        # Root window
        self.configure(background=P["win_bg"])

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New",  command=self._handle_new)
        file_menu.add_command(label="Open", command=self._handle_open)
        file_menu.add_command(label="Save", command=self._handle_save)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._handle_exit)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._handle_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    # ------------------------------------------------------------------
    # UI layout
    # ------------------------------------------------------------------

    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=4, pady=4)
        self._nb = nb

        self._build_welcome_tab(nb)

        for key, tab_label in CATEGORIES:
            self._build_dynamic_tab(nb, key, tab_label)

        self._build_results_tab(nb)

        # Welcome(1) + all dynamic tabs = index of Results
        self._results_tab_index = 1 + len(CATEGORIES)

    def _on_notebook_configure(self, event):
        num_tabs = len(self._nb.tabs())

        if not num_tabs:
            return

        ttk.Style().configure(
            "TNotebook.Tab", width=max(self._min_tab_w, event.width // num_tabs)
        )

    def _on_welcome_resize(self, event):
        w = max(event.width - 28, 1)  # subtract 14px padding on each side
        for lbl in self._welcome_wrap_labels:
            lbl.configure(wraplength=w)

    # ---- Welcome tab -----------------------------------------------
    def _build_welcome_tab(self, nb):
        frame = ttk.Frame(nb, padding=14)
        nb.add(frame, text="Welcome")

        # Intro — centered
        intro_label = ttk.Label(
            frame,
            text=(
                "Welcome to the grade calculator! Determine your grade by following these steps:"
            ),
            wraplength=480, justify="center"
        )
        intro_label.grid(row=0, column=0, pady=(0, 12))

        # Steps — centered as a block; items stay left-aligned within the block
        steps_frame = ttk.Frame(frame)
        steps_frame.grid(row=1, column=0, pady=(0, 4))

        steps = [
            "1. Enter the total weight value possible for the course below (defaults to 100 for 100%).",
            "2. In each category tab, enter a Weight and Grade for each item. Use '+ Add New Grade' to add additional rows.",
            "3. Click 'Calculate Grades' in the Results tab to see your final grade.",
        ]

        step_labels = []
        for i, step in enumerate(steps):
            lbl = ttk.Label(steps_frame, text=step, wraplength=420, justify="left")
            lbl.grid(row=i, column=0, sticky="w", pady=(0, 4))
            step_labels.append(lbl)

        # Weight Possible — centered
        wp_frame = ttk.Frame(frame)
        wp_frame.grid(row=2, column=0, pady=(16, 0))
        ttk.Label(wp_frame, text="Weight Possible:").pack(side="left", padx=(0, 8))
        self._weight_possible = ttk.Entry(wp_frame, width=12)
        self._weight_possible.insert(0, "100")
        self._weight_possible.pack(side="left")
        self._weight_possible.bind("<KeyRelease>", self._filter_numeric_list)
        ttk.Label(wp_frame, text="%").pack(side="left", padx=(4, 0))

        frame.columnconfigure(0, weight=1)

        # Store refs so __init__ can bind after sizing is finalised.
        self._welcome_frame = frame
        self._welcome_wrap_labels = [intro_label] + step_labels

    # ---- Generic dynamic tab (Exams / Homework / Labs / Quizzes / In-Class) ---

    def _build_dynamic_tab(self, nb, key: str, tab_label: str):
        outer = ttk.Frame(nb, padding=14)
        nb.add(outer, text=tab_label)

        canvas = tk.Canvas(outer, highlightthickness=0, bd=0, background=PALETTE["panel"])
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)

        def _set_scroll(first, last):
            scrollbar.set(first, last)
            if float(first) <= 0.0 and float(last) >= 1.0:
                scrollbar.grid_remove()
            else:
                scrollbar.grid()

        canvas.configure(yscrollcommand=_set_scroll)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)

        frame = ttk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=frame, anchor="nw")

        def update_scroll_region():
            canvas.configure(scrollregion=(
                0, 0,
                frame.winfo_reqwidth(),
                max(frame.winfo_reqheight(), canvas.winfo_height()),
            ))

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
            update_scroll_region()

        frame.bind("<Configure>", lambda _: update_scroll_region())
        canvas.bind("<Configure>", on_canvas_configure)

        ttk.Label(frame, text="Weight", font=("", 10, "bold")).grid(
            row=0, column=1, padx=(0, 6), pady=(0, 4), sticky="w"
        )
        ttk.Label(frame, text="Grade", font=("", 10, "bold")).grid(
            row=0, column=2, padx=(6, 0), pady=(0, 4), sticky="w"
        )
        ttk.Separator(frame, orient="horizontal").grid(
            row=1, column=0, columnspan=3, sticky="ew", pady=(0, 6)
        )

        self._weight_entry_lists[key] = []
        self._grade_entry_lists[key]  = []
        self._row_label_lists[key]    = []
        self._tab_inner_frame[key]    = frame
        self._tab_next_row[key]       = 2

        self._weight_entries[key] = self._EntryListProxy(self._weight_entry_lists[key])
        self._grade_entries[key]  = self._EntryListProxy(self._grade_entry_lists[key])

        self._add_grade_row(key)  # seed one row

        ttk.Button(
            frame, text="+ Add New Grade",
            command=lambda k=key: self._add_grade_row(k)
        ).grid(row=999, column=0, columnspan=3, pady=(10, 2))

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)

    def _add_grade_row(self, key: str):
        frame = self._tab_inner_frame[key]
        row   = self._tab_next_row[key]
        self._tab_next_row[key] += 1

        idx = len(self._weight_entry_lists[key]) + 1
        lbl = ttk.Label(frame, text=f"#{idx}")
        lbl.grid(row=row, column=0, sticky="e", padx=(0, 6), pady=3)
        self._row_label_lists[key].append(lbl)

        w_entry = ttk.Entry(frame, width=18)
        w_entry.grid(row=row, column=1, sticky="ew", padx=(0, 6), pady=3)
        w_entry.bind("<KeyRelease>", self._filter_numeric_list)
        self._weight_entry_lists[key].append(w_entry)

        g_entry = ttk.Entry(frame, width=18)
        g_entry.grid(row=row, column=2, sticky="ew", pady=3)
        g_entry.bind("<KeyRelease>", self._filter_numeric_list)
        self._grade_entry_lists[key].append(g_entry)

        w_entry.focus_set()

    # ---- Results tab -----------------------------------------------

    def _build_results_tab(self, nb):
        frame = ttk.Frame(nb, padding=14)
        nb.add(frame, text="Results")

        result_labels = [("final", "Final Grade")] + [(k, f"{lbl} Grade") for k, lbl in CATEGORIES]
        self._result_vars = {}

        for row, (key, label) in enumerate(result_labels):
            ttk.Label(frame, text=label).grid(
                row=row, column=0, sticky="w", pady=5, padx=(0, 10)
            )
            var = tk.StringVar()
            ttk.Entry(frame, textvariable=var, state="readonly").grid(
                row=row, column=1, sticky="ew", pady=5
            )
            self._result_vars[key] = var

        ttk.Button(
            frame, text="Calculate Grades", command=self._handle_calculate
        ).grid(row=len(result_labels) + 1, column=0, columnspan=2, pady=(16, 4))

        frame.columnconfigure(1, weight=1)

    # ------------------------------------------------------------------
    # Input filtering
    # ------------------------------------------------------------------

    def _filter_numeric_list(self, event):
        widget = event.widget
        text = widget.get()
        cleaned = "".join(c for c in text if c in NUMERIC_CHARS)

        if cleaned.count(".") > 1:
            first_dot = cleaned.index(".")
            cleaned = cleaned[:first_dot + 1] + cleaned[first_dot + 1:].replace(".", "")

        if cleaned != text:
            pos = widget.index(tk.INSERT)
            widget.delete(0, tk.END)
            widget.insert(0, cleaned)
            widget.icursor(min(pos, len(cleaned)))

    # ------------------------------------------------------------------
    # Calculate
    # ------------------------------------------------------------------

    def _handle_calculate(self):
        wp_text = self._weight_possible.get().strip()

        if not wp_text:
            self._error("ERROR: Weight Possible field is empty!")
            return
        
        try:
            weight_possible = Decimal(wp_text) / Decimal(100)
        except InvalidOperation:
            self._error(f"ERROR: {wp_text!r} is not a valid number for Weight Possible!")
            return

        weights = {k: parse_list(self._weight_entries[k].get()) for k, _ in CATEGORIES}
        grades  = {k: parse_list(self._grade_entries[k].get())  for k, _ in CATEGORIES}

        # Convert whole-number weights (e.g. 25) to decimal form (0.25)
        # A weight is treated as a whole number when it is >= 1.
        def normalise_weights(wlist):
            result = []
            for w in wlist:
                try:
                    d = Decimal(w)
                except InvalidOperation:
                    raise ValueError(f"ERROR: {w!r} is not a valid numeric value!")
                result.append(str(d / Decimal(100)) if d >= 1 else w)
            return result

        try:
            weights = {k: normalise_weights(v) for k, v in weights.items()}
            total_weight = calculate_total_weight([weights[k] for k, _ in CATEGORIES])
        except Exception as exc:
            self._error(str(exc))
            return

        if total_weight.compare(weight_possible) != Decimal(0):
            messagebox.showwarning(
                "Warning",
                f"Weights entered do not equal {wp_text}%!\n\n"
                f"(Current total: {float(total_weight * 100):.4g}%)",
                parent=self,
            )

        results = {}
        for key, label in CATEGORIES:
            try:
                results[key] = calculate_grade(weights[key], grades[key], label.lower())
            except ValueError as exc:
                self._error(str(exc))
                return

        final = sum(results.values(), Decimal(0))
        q = Decimal("0.1")
        self._result_vars["final"].set(str(final.quantize(q, ROUND_HALF_UP)) + "%")

        for key, _ in CATEGORIES:
            self._result_vars[key].set(str(results[key].quantize(q, ROUND_HALF_UP)) + "%")

        self._nb.select(self._results_tab_index)

    # ------------------------------------------------------------------
    # Error helper
    # ------------------------------------------------------------------

    def _error(self, message: str):
        for var in self._result_vars.values():
            var.set("ERROR: SEE ALERT.")
        
        messagebox.showerror("Error", message, parent=self)

    # ------------------------------------------------------------------
    # File menu handlers
    # ------------------------------------------------------------------

    def _handle_new(self):
        self._weight_possible.delete(0, tk.END)
        self._weight_possible.insert(0, "100")

        for key, _ in CATEGORIES:
            self._reset_tab_rows(key)
        
        for var in self._result_vars.values():
            var.set("")
        
        self._nb.select(0)

    def _reset_tab_rows(self, key: str):
        for widget_list in (self._row_label_lists[key],
                            self._weight_entry_lists[key],
                            self._grade_entry_lists[key]):
            for w in widget_list:
                w.destroy()
            
            widget_list.clear()
        
        self._tab_next_row[key] = 2
        self._add_grade_row(key)

    def _handle_open(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Select a File to Open",
            filetypes=[("All Files", "*.*"), ("Text Files", "*.txt *.text")],
        )
        
        if not path:
            return
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
            
            # File format:
            # 0: weightPossible
            # 1/2: examW/G, 3/4: hwW/G, 5/6: labW/G,
            # 7/8: quizW/G, 9/10: inclassW/G, 11/12: miscW/G
            order = [k for k, _ in CATEGORIES]
            self._weight_possible.delete(0, tk.END)
            self._weight_possible.insert(0, lines[0] if lines else "100")

            for i, key in enumerate(order):
                w_val = lines[1 + i * 2] if (1 + i * 2) < len(lines) else ""
                g_val = lines[2 + i * 2] if (2 + i * 2) < len(lines) else ""

                w_parts = [v.strip() for v in w_val.split(",") if v.strip()]
                g_parts = [v.strip() for v in g_val.split(",") if v.strip()]
                needed  = max(len(w_parts), len(g_parts), 1)

                self._reset_tab_rows(key)
                for _ in range(needed - 1):
                    self._add_grade_row(key)

                self._weight_entries[key].insert(0, w_val)
                self._grade_entries[key].insert(0, g_val)
        except Exception:
            messagebox.showerror(
                "Error",
                "ERROR: File could not be loaded correctly. "
                "It may have been moved, deleted, or it may be corrupt.",
                parent=self,
            )

    def _handle_save(self):
        path = filedialog.asksaveasfilename(
            parent=self, title="Create/Select a File to Save",
        )

        if not path:
            return
        
        try:
            order = [k for k, _ in CATEGORIES]
            lines = [self._weight_possible.get()]

            for key in order:
                lines.append(self._weight_entries[key].get())
                lines.append(self._grade_entries[key].get())
            
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except Exception:
            messagebox.showerror(
                "Error", "ERROR: File could not be written to correctly.", parent=self,
            )

    def _handle_exit(self):
        self.destroy()

    def _handle_about(self):
        messagebox.showinfo("About the Grade Calculator", ABOUT_TEXT, parent=self)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = GradeCalculatorApp()
    app.mainloop()
