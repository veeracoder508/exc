import customtkinter as ctk
import tkinter
from tkinter import filedialog
from PIL import Image
import re
from tkinter import messagebox
import tkinter.font
import os

import compiler

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# New, refreshed color palette for syntax highlighting
SYNTAX_MAP = {
    "Display.": "#E57A84", "Display": "#E57A84", ".out": "#F47A7B", ".in": "#F47A7B", ".clear": "#F47A7B",
    "if": "#748FFC", "else": "#748FFC", "endif": "#748FFC", "while": "#748FFC", "endwhile": "#748FFC",
    "import": "#748FFC", "sub": "#748FFC", "let": "#748FFC", "pass": "#748FFC", "break": "#748FFC",
    "continue": "#748FFC", "endsub": "#748FFC",
    "end":"#D6638C",
    "int": "#20C997", "float": "#20C997", "char": "#20C997", "string": "#20C997", "bool": "#20C997",
    "list": "#20C997", "dict": "#20C997",
    "int_val": "#FAB005", "float_val": "#E67700", "bool_val": "#339AF0", "string_val": "#84A864",
    "comments": "#5C7667", "breakets": "#E0E0E0", "declared_var": "#B77C93",
    "arithmetic_op": "#A55EEA",
    "relational_op": "#F45B69",
    "logical_op": "#FFD43B",
    "bitwise_op": "#63E6BE"
}

class CodeEditor(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.current_file_path = None
        
        self.geometry("1000x600")
        self.sidebar_visible = True
        self.search_visible = False
        self.settings_visible = False
        
        self.all_system_fonts = sorted(list(tkinter.font.families()))
        self.current_font_family = "Consolas"
        if self.current_font_family not in self.all_system_fonts:
            self.current_font_family = "Arial"
        
        self._load_icons()
        self._create_menu_bar()
        self._create_sidebar()

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(side="right", fill="both", expand=True)
        
        initial_font = ctk.CTkFont(family=self.current_font_family, size=14)
        
        self.scrollbar = ctk.CTkScrollbar(self.main_frame)
        self.scrollbar.pack(side="right", fill="y")
        
        self.line_numbers = ctk.CTkTextbox(self.main_frame, width=50, font=initial_font, state="disabled", wrap="none")
        self.line_numbers.pack(side="left", fill="y")
        
        self.text = ctk.CTkTextbox(self.main_frame, font=initial_font, wrap="none")
        self.text.pack(side="right", fill="both", expand=True)

        self.scrollbar.configure(command=self._on_scroll)
        self.text.configure(yscrollcommand=self._on_text_scroll)
        self.line_numbers.configure(yscrollcommand=self._on_line_numbers_scroll)

        self.text.bind("<KeyRelease>", self._on_key_release)
        self.text.bind("<Button-1>", self._update_line_numbers)
        self.text.bind("<Configure>", self._update_line_numbers)
        
        self.bind_all("<Control-n>", self._new_file)
        self.bind_all("<Control-o>", self._open_file)
        self.bind_all("<Control-s>", self._save_file)
        
        self.bind_all("<Escape>", lambda event: self.destroy())
        
        self._update_title_bar()
        self._update_line_numbers()
        self.current_theme = ctk.get_appearance_mode()
        self._update_ui_colors()

    def _on_scroll(self, *args):
        self.text.yview(*args)
        self.line_numbers.yview(*args)

    def _on_text_scroll(self, *args):
        self.scrollbar.set(*args)
        self.line_numbers.yview_moveto(args[0])

    def _on_line_numbers_scroll(self, *args):
        self.scrollbar.set(*args)
        self.text.yview_moveto(args[0])

    def _load_icons(self):
        try:
            self.icon_explorer = ctk.CTkImage(Image.open("icons/explorer.png"), size=(20, 20))
            self.icon_search = ctk.CTkImage(Image.open("icons/search.png"), size=(20, 20))
            self.icon_settings = ctk.CTkImage(Image.open("icons/settings.png"), size=(20, 20))
            self.icon_new = ctk.CTkImage(Image.open("icons/new.png"), size=(20,20))
            self.icon_open = ctk.CTkImage(Image.open("icons/open.png"), size=(20,20))
            self.icon_save = ctk.CTkImage(Image.open("icons/save.png"), size=(20,20))
            self.icon_menu = ctk.CTkImage(Image.open("icons/menu.png"), size=(20,20))
            self.icon_help = ctk.CTkImage(Image.open("icons/help.png"), size=(20,20))
            self.icon_commands = ctk.CTkImage(Image.open("icons/commands.png"), size=(20,20))
        except FileNotFoundError:
            self.icon_explorer = self.icon_search = self.icon_settings = None
            self.icon_new = self.icon_open = self.icon_save = self.icon_menu = self.icon_help = None
    
    def _create_menu_bar(self):
        self.menu_bar = ctk.CTkFrame(self, fg_color="#2C2C38", height=32)
        self.menu_bar.pack(side="top", fill="x")

        button_style = {
            "corner_radius": 5,
            "height": 32,
            "width": 80,
            "fg_color": "transparent",
            "hover_color": "#42425C",
            "text_color": "#D4D4D4",
            "font": ("Segoe UI", 12)
        }

        ctk.CTkButton(self.menu_bar, text="", command=self._toggle_sidebar, image=self.icon_menu, **button_style).pack(side="left", padx=4)
        ctk.CTkButton(self.menu_bar, text="New", command=self._new_file, image=self.icon_new, **button_style).pack(side="left", padx=4)
        ctk.CTkButton(self.menu_bar, text="Open", command=self._open_file, image=self.icon_open, **button_style).pack(side="left", padx=4)
        ctk.CTkButton(self.menu_bar, text="Save", command=self._save_file, image=self.icon_save, **button_style).pack(side="left", padx=4)
        ctk.CTkButton(self.menu_bar, text="Run", command=self._run_file, image=self.icon_commands, **button_style).pack(side="left", padx=4)
        ctk.CTkButton(self.menu_bar, text="Help", command=self._show_help, image=self.icon_help, **button_style).pack(side="left", padx=4)

    def _create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=180, fg_color="#2C2C38", bg_color="#2C2C38")
        self.sidebar.pack(side="left", fill="y")
        
        self.scrollable_sidebar = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.scrollable_sidebar.pack(fill="both", expand=True)

        ctk.CTkLabel(self.scrollable_sidebar, text="Sidebar", font=("Segoe UI", 14), text_color="#D4D4D4").pack(pady=10)
        
        button_style = {
            "compound": "left",
            "fg_color": "transparent",
            "hover_color": "#42425C",
            "corner_radius": 5,
            "font": ("Segoe UI", 12),
            "text_color": "#D4D4D4"
        }

        ctk.CTkButton(self.scrollable_sidebar, text="Explorer", image=self.icon_explorer, **button_style, command=self._open_file).pack(fill="x", pady=2)
        ctk.CTkButton(self.scrollable_sidebar, text="Search", image=self.icon_search, **button_style, command=self._toggle_search_section).pack(fill="x", pady=2)
        ctk.CTkButton(self.scrollable_sidebar, text="Settings", image=self.icon_settings, **button_style, command=self._toggle_settings_section).pack(fill="x", pady=2)

        self.search_frame = ctk.CTkFrame(self.scrollable_sidebar, fg_color="transparent")
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Find text...", fg_color="#21212B", border_color="#42425C")
        self.search_entry.pack(pady=2, padx=5)
        ctk.CTkButton(self.search_frame, text="Search", **button_style, command=self._search_text).pack(pady=2)

        self.settings_frame = ctk.CTkFrame(self.scrollable_sidebar, fg_color="transparent")
        ctk.CTkLabel(self.settings_frame, text="Font Size", text_color="#D4D4D4").pack(pady=(10, 2))
        self.font_slider = ctk.CTkSlider(self.settings_frame, from_=10, to=24, number_of_steps=14, command=self._apply_font_size)
        self.font_slider.set(14)
        self.font_slider.pack(pady=2, padx=5)

        ctk.CTkLabel(self.settings_frame, text="Font Search", text_color="#D4D4D4").pack(pady=(10, 2))
        self.font_search_entry = ctk.CTkEntry(self.settings_frame, placeholder_text="Search for a font...", fg_color="#21212B", border_color="#42425C")
        self.font_search_entry.pack(pady=2, padx=5, fill="x")
        self.font_search_entry.bind("<KeyRelease>", self._filter_font_list)
        
        ctk.CTkLabel(self.settings_frame, text="Font Type", text_color="#D4D4D4").pack(pady=(10, 2))
        self.font_option_menu = ctk.CTkOptionMenu(self.settings_frame, values=self.all_system_fonts, command=self._apply_font_type)
        self.font_option_menu.set(self.current_font_family)
        self.font_option_menu.pack(pady=2, padx=5)
        
        ctk.CTkLabel(self.settings_frame, text="Theme", text_color="#D4D4D4").pack(pady=(10, 2))
        self.theme_option_menu = ctk.CTkOptionMenu(self.settings_frame, values=["Dark", "Light", "System"], command=self._apply_theme)
        self.theme_option_menu.set(ctk.get_appearance_mode().capitalize())
        self.theme_option_menu.pack(pady=2, padx=5)

    def _filter_font_list(self, event=None):
        search_query = self.font_search_entry.get().lower()
        if search_query:
            filtered_fonts = [font for font in self.all_system_fonts if search_query in font.lower()]
        else:
            filtered_fonts = self.all_system_fonts
        
        self.font_option_menu.configure(values=filtered_fonts)
        if filtered_fonts:
            self.font_option_menu.set(filtered_fonts[0])
        else:
            self.font_option_menu.set("No fonts found")
            
    def _update_ui_colors(self):
        self.menu_bar.configure(fg_color="#2C2C38")
        self.sidebar.configure(fg_color="#2C2C38")
        self.text.configure(fg_color="#21212B")
        self.line_numbers.configure(fg_color="#21212B")
        self.text.configure(text_color="#D4D4D4")
        self.line_numbers.configure(text_color="#D4D4D4")

    def _apply_theme(self, theme_name):
        ctk.set_appearance_mode(theme_name.lower())
        self.current_theme = theme_name
        self._update_ui_colors()

    def _toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar.pack_forget()
        else:
            self.sidebar.pack(side="left", fill="y")
        self.sidebar_visible = not self.sidebar_visible

    def _toggle_search_section(self):
        if self.search_visible:
            self.search_frame.pack_forget()
        else:
            self.search_frame.pack(fill="x", padx=5)
        self.search_visible = not self.search_visible

    def _toggle_settings_section(self):
        if self.settings_visible:
            self.settings_frame.pack_forget()
        else:
            self.settings_frame.pack(fill="x", padx=5)
        self.settings_visible = not self.settings_visible

    def _update_title_bar(self):
        if self.current_file_path:
            file_name = os.path.basename(self.current_file_path)
            self.title(f"exc1 editor - {file_name}")
        else:
            self.title("exc1 editor - Untitled")

    def _new_file(self, event=None):
        self.text.delete("1.0", "end")
        self.current_file_path = None
        self._update_title_bar()

    def _open_file(self, event=None):
        path = filedialog.askopenfilename(filetypes=[("exc1 Files", "*.exc1"), ("Text Files Files", "*.txt"), ("All Files", "*")])
        if path:
            try:
                with open(path, "r") as f:
                    self.text.delete("1.0", "end")
                    self.text.insert("1.0", f.read())
                self.current_file_path = path
                self._update_title_bar()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")

    def open_file_shell(self, path, event=None):
        if path:
            try:
                with open(path, "r") as f:
                    self.text.delete("1.0", "end")
                    self.text.insert("1.0", f.read())
                self.current_file_path = path
                self._update_title_bar()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file: {e}")

    def _save_file(self, event=None):
        if self.current_file_path:
            path = self.current_file_path
        else:
            path = filedialog.asksaveasfilename(defaultextension=".exc1",
                                                filetypes=[("Text Files", "*.txt"), ("exc1 Files", "*.exc1"), ("All Files", "*")])
        
        if path:
            try:
                with open(path, "w") as f:
                    f.write(self.text.get("1.0", "end-1c"))
                self.current_file_path = path
                self._update_title_bar()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def _run_file(self):
        help_window = ctk.CTkToplevel(self)
        help_window.title("Run")
        help_window.geometry("300x117")
        help_window.transient(self)
        help_window.configure(fg_color="#21212B")
        
        # Main container frame for the help window
        main_frame = ctk.CTkFrame(help_window, fg_color="#2C2C38", corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Title label
        title_label = ctk.CTkLabel(main_frame, text="exc1 compiler",font=("Terminal",16,"bold"), text_color="#D4D4D4")
        title_label.pack(pady=(15, 5))
        
        # Main help text
        help_label = ctk.CTkLabel(main_frame, text="version:exc1(0.1.1[24082025])", wraplength=250, justify="center", text_color="#868686")
        help_label.pack(pady=(5, 10), padx=10)

        # run the selected file
        path = self.current_file_path
        byte_path = path + ".excbite1"
        os.system("cls")
        self._save_file()
        compiler.Compiler.compile_exc1_to_excbite1(path,byte_path)
        compiler.Compiler.run_excbite1(byte_path)
                
    def _show_help(self):
        help_window = ctk.CTkToplevel(self)
        help_window.title("Help")
        help_window.geometry("400x330")
        help_window.transient(self)
        help_window.configure(fg_color="#21212B")
        
        # Main container frame for the help window
        main_frame = ctk.CTkFrame(help_window, fg_color="#2C2C38", corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Title label
        title_label = ctk.CTkLabel(main_frame, text="Code Editor Help", font=("Segoe UI", 16, "bold"), text_color="#D4D4D4")
        title_label.pack(pady=(15, 5))
        
        # Main help text
        help_label = ctk.CTkLabel(main_frame, text="version:exc_editor1(0.1.1[24082025])", wraplength=500, justify="left", font=("Terminal",14,"bold"), text_color="#5F5F5F")
        help_label.pack(pady=(5, 10), padx=10)
        
        # Keyboard shortcuts section
        shortcuts_label = ctk.CTkLabel(main_frame, text="Keyboard Shortcuts:", font=("Segoe UI", 12, "bold"), text_color="#D4D4D4")
        shortcuts_label.pack(anchor="w", padx=15, pady=(10, 0))
        
        shortcuts_text = ctk.CTkLabel(main_frame, text="• Ctrl+N: New File\n• Ctrl+O: Open File\n• Ctrl+S: Save File\n• Escape: Quit Editor", justify="left")
        shortcuts_text.pack(anchor="w", padx=25, pady=(5, 10))

        commands_button = ctk.CTkButton(main_frame, text="Show Commands", image=self.icon_commands, command=self._show_commands_table)
        commands_button.pack(pady=10)

        commands_button = ctk.CTkButton(main_frame, text="Example code", image=self.icon_commands, command=self._show_programs_table)
        commands_button.pack(pady=10)

    def _show_commands_table(self):
        commands_window = ctk.CTkToplevel(self)
        commands_window.title("Syntax Reference")
        commands_window.geometry("500x550")
        commands_window.transient(self)
        commands_window.configure(fg_color="#21212B")

        title_frame = ctk.CTkFrame(commands_window, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(title_frame, text="Commands & Operators", font=("Segoe UI", 18, "bold"), text_color="#D4D4D4").pack(side="left")
        
        ctk.CTkLabel(commands_window, text="A quick reference guide for recognized syntax.", font=("Segoe UI", 12), text_color="#A0A0A0").pack(fill="x", padx=20, pady=(0, 10))

        scrollable_frame = ctk.CTkScrollableFrame(commands_window, fg_color="#2C2C38", corner_radius=10)
        scrollable_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # A dictionary to map categories to colors for visual consistency
        category_colors = {
            "Control Flow": SYNTAX_MAP["if"],
            "Functions": SYNTAX_MAP["sub"],
            "Terminate": SYNTAX_MAP["end"],
            "Display & IO": SYNTAX_MAP["Display."],
            "Data Types": SYNTAX_MAP["int"],
            "Variables": SYNTAX_MAP["let"],
            "Logical Operators": SYNTAX_MAP["logical_op"],
            "Relational Operators": SYNTAX_MAP["relational_op"],
            "Arithmetic Operators": SYNTAX_MAP["arithmetic_op"],
            "Bitwise Operators": SYNTAX_MAP["bitwise_op"],
        }
        
        syntax_data = {
            "Control Flow": [("if", "if (conditon)\nstatements\nendif"), ("else", "if..\nelse\nstatements\nendif"), ("endif", "if..else..endif"), ("while", "while (condition)\nstatements\nendwhile"), ("endwhile", "while..endwhile"), ("break", "while..break..endwhile"), ("continue", "while..continue..endwhile")],
            "Functions": [("sub", "sub (name)"), ("endsub", "sub..endsub")],
            "Terminate": [("end", "program..end")],
            "Display & IO": [("Display.out", "Display.out(value/variable)"), ("Display.in", "Display.in(variable)"), ("Display.clear", "Display.clear()")],
            "Data Types": [("int", "variable_name"), ("float", "variable_name"), ("char", "variable_name"), ("string", "variable_name"), ("bool", "variable_name"), ("list", "variable_name"), ("dict", "variable_name")],
            "Variables": [("let", "variable_name")],
            "Logical Operators": [("and", "a and b"), ("or", "a or b"), ("not", "not a")],
            "Relational Operators": [("==", "a == b"), ("!=", "a != b"), ("<", "a < b"), (">", "a > b"), ("<=", "a <= b"), (">=", "a >= b")],
            "Arithmetic Operators": [("+", "a + b"), ("-", "a - b"), ("*", "a * b"), ("/", "a / b"), ("%", "a % b"), ("**", "a ** b")],
            "Bitwise Operators": [("&", "a & b"), ("|", "a | b"), ("^", "a ^ b"), ("~", "~a"), ("<<", "a << b"), (">>", "a >> b")]
        }

        row_index = 0
        for category, commands in syntax_data.items():
            # Category header with color from SYNTAX_MAP
            ctk.CTkLabel(scrollable_frame, text=category, font=("Segoe UI", 14, "bold"), text_color=category_colors.get(category, "white")).grid(row=row_index, column=0, columnspan=2, padx=10, pady=(15, 5), sticky="w")
            row_index += 1
            
            for command, syntax in commands:
                command_frame = ctk.CTkFrame(scrollable_frame, fg_color="#3A3A4A", corner_radius=8)
                command_frame.grid(row=row_index, column=0, columnspan=2, padx=10, pady=4, sticky="ew")

                ctk.CTkLabel(command_frame, text=command, font=("Segoe UI", 12, "bold"), text_color=SYNTAX_MAP.get(command, "white"), fg_color="transparent").pack(side="left", padx=10, pady=5)
                ctk.CTkLabel(command_frame, text=syntax, font=("Segoe UI", 12), fg_color="transparent").pack(side="right", padx=10, pady=5)

                row_index += 1
                
        # Configure columns to expand
        scrollable_frame.grid_columnconfigure(0, weight=1)
        scrollable_frame.grid_columnconfigure(1, weight=1)

    def _search_text(self):
        query = self.search_entry.get()
        self.text.tag_remove("search", "1.0", "end")
        if query:
            idx = "1.0"
            while True:
                idx = self.text.search(query, idx, nocase=1, stopindex="end")
                if not idx: break
                lastidx = f"{idx}+{len(query)}c"
                self.text.tag_add("search", idx, lastidx)
                self.text.tag_config("search", background="#444444", foreground="#00FF00")
                idx = lastidx
    
    def _set_text_font(self):
        font_size = int(self.font_slider.get())
        new_font = ctk.CTkFont(family=self.current_font_family, size=font_size)
        self.text.configure(font=new_font)
        self.line_numbers.configure(font=new_font)

    def _apply_font_size(self, value):
        self._set_text_font()

    def _apply_font_type(self, font_name):
        self.current_font_family = font_name
        self._set_text_font()

    def _on_key_release(self, event=None):
        self._highlight_syntax()
        self._update_line_numbers()

    def _update_line_numbers(self, event=None):
        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("1.0", "end")
        lines = int(self.text.index("end-1c").split(".")[0])
        self.line_numbers.insert("1.0", "\n".join(str(i) for i in range(1, lines + 1)))
        self.line_numbers.configure(state="disabled")
    
    def _highlight_syntax(self):
        content = self.text.get("1.0", "end-1c")
        self.text.tag_delete("all")
        
        excluded_ranges = []

        string_pattern = r'(".*?"|\'.*?\')'
        for match in re.finditer(string_pattern, content):
            start = match.start(0)
            end = match.end(0)
            self._tag_match("string_val", match, start, end)
            excluded_ranges.append((start, end))

        comment_pattern = r"#.*"
        for match in re.finditer(comment_pattern, content):
            start = match.start(0)
            end = match.end(0)
            self._tag_match("comments", match, start, end)
            excluded_ranges.append((start, end))

        patterns_to_check = [
            ("logical_op", r"\b(?:and|or|not)\b"),
            ("relational_op", r"==|!=|<=|>=|<|>"),
            ("arithmetic_op", r"\*\*|\*|\/|\%|\+|\-"),
            ("bitwise_op", r"&|\||\^|~|<<|>>"),
            ("declared_var", r"\b(?:let|int|float|char|string|bool|list|dict)\s+([a-zA-Z_]\w*)"),
            ("int_val", r"\b\d+\b"),
            ("float_val", r"\b\d+\.\d+\b"),
            ("bool_val", r"\bTrue\b|\bFalse\b"),
            ("breakets", r"[\[\]\{\}\(\)]"),
        ]

        keywords = {k: v for k, v in SYNTAX_MAP.items() if k not in [p[0] for p in patterns_to_check] and k not in ["string_val", "comments"]}

        for tag, pattern in patterns_to_check:
            for match in re.finditer(pattern, content):
                start = match.start(0)
                end = match.end(0)
                
                is_excluded = False
                for ex_start, ex_end in excluded_ranges:
                    if (start >= ex_start and start < ex_end) or (end > ex_start and end <= ex_end):
                        is_excluded = True
                        break
                
                if not is_excluded:
                    group = 1 if tag == "declared_var" else 0
                    self._tag_match(tag, match, match.start(group), match.end(group))

        for keyword, color in keywords.items():
            for match in re.finditer(rf"\b{re.escape(keyword)}\b", content):
                start = match.start(0)
                end = match.end(0)
                
                is_excluded = False
                for ex_start, ex_end in excluded_ranges:
                    if (start >= ex_start and start < ex_end) or (end > ex_start and end <= ex_end):
                        is_excluded = True
                        break
                
                if not is_excluded:
                    self._tag_match(keyword, match, start, end)

    def _tag_match(self, tag, match, start_char_index, end_char_index):
        start = f"1.0 + {start_char_index} chars"
        end = f"1.0 + {end_char_index} chars"
        self.text.tag_add(tag, start, end)
        self.text.tag_config(tag, foreground=SYNTAX_MAP[tag])

    def animate_sidebar(self, show=True, speed=10):
        target_width = 200 if show else 0
        current_width = self.sidebar.winfo_width()

        def step():
            nonlocal current_width
            if show and current_width < target_width:
                current_width += speed
            elif not show and current_width > target_width:
                current_width -= speed
            else:
                return

            self.sidebar.configure(width=current_width)
            self.sidebar.update()
            self.after(10, step)

        step()

    def fade_in_widget(self, widget, steps=10):
        def step(i=0):
            if i > steps:
                return
            alpha = int(255 * (i / steps))
            widget.configure(fg_color=f"#{alpha:02x}{alpha:02x}{alpha:02x}") 
            self.after(30, lambda: step(i + 1))

        step()

    def animate_sidebar_with_fade(self, show=True):
        def on_complete():
            if show:
                for widget in self.sidebar.winfo_children():
                    self.fade_in_widget(widget)

        self.animate_sidebar(show=show)
        self.after(250, on_complete)

def invok_editer() -> None:
    app = CodeEditor()
    app.mainloop()


if __name__ == "__main__":
    invok_editer()