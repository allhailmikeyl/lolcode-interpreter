import os 
import tkinter as tk
from tkinter import filedialog, ttk 
import customtkinter as ctk  # modern UI framework for VS Code aesthetic

try:
    from analyzer import analyze  # bridge to lexer, parser, and symbol logic
except ImportError:
    analyze = None  # fallback if analyzer.py is not yet in directory

ctk.set_appearance_mode("Dark")  # enforce dark theme ala VS Code
ctk.set_default_color_theme("blue")  # base theme (can point to themes/pink.json if present)

class LOLCodeInterpreterUI(ctk.CTk):
    def __init__(self):
        super().__init__()  # initialize CTk main window
        self.title("kids ni sol - LOLCODE Interpreter")  # set window title bar
        self.geometry("1100x750")  # default window dimensions
        self.minsize(900, 600)  # minimum window size constraints
        self.grid_columnconfigure(0, weight=1)  # allow left column (editor) to expand
        self.grid_columnconfigure(1, weight=1)  # allow right column (tables) to expand
        self.grid_rowconfigure(1, weight=3)  # allocate vertical weight for editor/tables
        self.grid_rowconfigure(3, weight=1)  # allocate vertical weight for console
        self._setup_styles()  # configure ttk treeview styling for dark mode
        self._build_top_bar()  # build file selector section (1)
        self._build_editor()  # build editable code area section (2)
        self._build_tables()  # build lexeme table (3) and symbol table placeholder (4)
        self._build_execute_bar()  # build execute/run button section (5)
        self._build_console()  # build console output section (6)

    def _setup_styles(self):
        style = ttk.Style()  # access ttk style manager
        style.theme_use("default")  # use default base for reliable color override
        style.configure(
            "Treeview", 
            background="#252526", 
            foreground="#d4d4d4", 
            fieldbackground="#252526", 
            rowheight=24, 
            borderwidth=0, 
            font=("Consolas", 10)
        )  # dark table body
        style.configure(
            "Treeview.Heading", 
            background="#333333", 
            foreground="#ffffff", 
            font=("Consolas", 10, "bold"), 
            relief="flat"
        )  # table header styling
        style.map("Treeview", background=[("selected", "#B74177")])  # pink selection accent
        style.map("Treeview.Heading", background=[("active", "#444444")])  # active header hover style

    def _build_top_bar(self):
        top_frame = ctk.CTkFrame(self, fg_color="transparent")  # container frame for file picker
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))  # place at top grid
        self.open_btn = ctk.CTkButton(
            top_frame, 
            text="Open File", 
            width=100, 
            fg_color="#B74177", 
            hover_color="#A01E5C", 
            font=("Consolas", 12, "bold"), 
            command=self.load_file
        )  # file open trigger
        self.open_btn.pack(side="left", padx=(0, 10))  # pack button to the left
        self.file_label = ctk.CTkLabel(
            top_frame, 
            text="File: (None)", 
            text_color="#858585", 
            font=("Consolas", 11)
        )  # file path label
        self.file_label.pack(side="left", fill="x")  # pack label next to button

    def _build_editor(self):
        editor_frame = ctk.CTkFrame(self, corner_radius=6)  # container frame for editor
        editor_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=5)  # place in left column
        editor_frame.grid_rowconfigure(1, weight=1)  # expand editor vertically
        editor_frame.grid_columnconfigure(0, weight=1)  # expand editor horizontally
        editor_lbl = ctk.CTkLabel(
            editor_frame, 
            text="CODE EDITOR", 
            font=("Consolas", 11, "bold"), 
            text_color="#d4d4d4"
        )  # editor title header
        editor_lbl.grid(row=0, column=0, sticky="w", padx=10, pady=(5, 0))  # position label
        
        # Note: ctk.CTkTextbox includes a built-in vertical scrollbar by default
        self.editor = ctk.CTkTextbox(
            editor_frame, 
            font=("Consolas", 12), 
            fg_color="#1e1e1e", 
            text_color="#d4d4d4", 
            wrap="none",
            activate_scrollbars=True
        )  # multiline code editor with vertical scroll support
        self.editor.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)  # attach text area
        default_code = "HAI\n  WAZZUP\n    I HAS A var ITZ 12\n  BUHBYE\n  VISIBLE \"noot noot\" var\nKTHXBYE\n"  # initial starter code
        self.editor.insert("1.0", default_code)  # pre-fill editor with LOLCODE sample

    def _build_tables(self):
        tables_frame = ctk.CTkFrame(self, corner_radius=6)  # right container for tables
        tables_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=5)  # place in right column
        tables_frame.grid_rowconfigure(1, weight=1)  # allow lexeme table to stretch
        tables_frame.grid_rowconfigure(3, weight=1)  # allow symbol table to stretch
        tables_frame.grid_columnconfigure(0, weight=1)  # stretch table horizontally
        tables_frame.grid_columnconfigure(1, weight=0)  # fixed width for scrollbar column

        lex_lbl = ctk.CTkLabel(
            tables_frame, 
            text="LEXEMES", 
            font=("Consolas", 11, "bold"), 
            text_color="#d4d4d4"
        )  # lexeme header
        lex_lbl.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(5, 0))  # span across table and scrollbar
        
        # --- (3) Lexeme Table with CTkScrollbar ---
        self.lexeme_tree = ttk.Treeview(tables_frame, columns=("Lexeme", "Classification"), show="headings", height=8)  # 2-column lexeme table
        self.lexeme_tree.heading("Lexeme", text="Lexeme")  # set column 1 title
        self.lexeme_tree.heading("Classification", text="Classification")  # set column 2 title
        self.lexeme_tree.column("Lexeme", width=180, anchor="w")  # set lexeme column properties
        self.lexeme_tree.column("Classification", width=220, anchor="w")  # set classification column properties
        self.lexeme_tree.grid(row=1, column=0, sticky="nsew", padx=(10, 0), pady=(2, 5))  # place lexeme table
        
        self.lexeme_scroll = ctk.CTkScrollbar(tables_frame, command=self.lexeme_tree.yview)  # dark-themed vertical scrollbar
        self.lexeme_scroll.grid(row=1, column=1, sticky="ns", padx=(2, 10), pady=(2, 5))  # place scrollbar beside lexeme table
        self.lexeme_tree.configure(yscrollcommand=self.lexeme_scroll.set)  # link treeview scrolling to scrollbar

        # --- (4) Symbol Table Placeholder with CTkScrollbar ---
        # TODO (Milestone 2): Hook self.symbol_tree up to dynamic AST symbol table generation from analyzer.py / symbols.py
        sym_lbl = ctk.CTkLabel(
            tables_frame, 
            text="SYMBOL TABLE (Placeholder - M2/M3)", 
            font=("Consolas", 11, "bold"), 
            text_color="#d4d4d4"
        )  # symbol table label
        sym_lbl.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=(5, 0))  # span across table and scrollbar
        
        self.symbol_tree = ttk.Treeview(tables_frame, columns=("Identifier", "Value"), show="headings", height=6)  # 2-column symbol table placeholder
        self.symbol_tree.heading("Identifier", text="Identifier")  # set column 1 title
        self.symbol_tree.heading("Value", text="Value")  # set column 2 title
        self.symbol_tree.column("Identifier", width=180, anchor="w")  # set identifier column properties
        self.symbol_tree.column("Value", width=220, anchor="w")  # set value column properties
        self.symbol_tree.grid(row=3, column=0, sticky="nsew", padx=(10, 0), pady=(2, 10))  # place symbol table

        self.symbol_scroll = ctk.CTkScrollbar(tables_frame, command=self.symbol_tree.yview)  # dark-themed vertical scrollbar
        self.symbol_scroll.grid(row=3, column=1, sticky="ns", padx=(2, 10), pady=(2, 10))  # place scrollbar beside symbol table
        self.symbol_tree.configure(yscrollcommand=self.symbol_scroll.set)  # link treeview scrolling to scrollbar

    def _build_execute_bar(self):
        exec_frame = ctk.CTkFrame(self, fg_color="transparent")  # container for run bar
        exec_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 2))  # place between editor and console
        self.exec_btn = ctk.CTkButton(
            exec_frame, 
            text="EXECUTE / RUN", 
            fg_color="#B74177", 
            hover_color="#A01E5C", 
            font=("Consolas", 13, "bold"), 
            height=32, 
            command=self.run_code
        )  # execute button
        self.exec_btn.pack(fill="x")  # stretch button across full width

    def _build_console(self):
        # TODO (Milestone 3): Route runtime evaluation (VISIBLE) and interactive user input (GIMMEH) into console
        console_frame = ctk.CTkFrame(self, corner_radius=6)  # container frame for terminal output
        console_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=(2, 10))  # place at bottom grid
        console_frame.grid_rowconfigure(1, weight=1)  # expand console vertically
        console_frame.grid_columnconfigure(0, weight=1)  # expand console horizontally
        console_lbl = ctk.CTkLabel(
            console_frame, 
            text="CONSOLE OUTPUT", 
            font=("Consolas", 11, "bold"), 
            text_color="#d4d4d4"
        )  # console label
        console_lbl.grid(row=0, column=0, sticky="w", padx=10, pady=(5, 0))  # position console label
        
        # Note: ctk.CTkTextbox handles vertical scrolling automatically
        self.console = ctk.CTkTextbox(
            console_frame, 
            font=("Consolas", 11), 
            fg_color="#181818", 
            text_color="#cccccc", 
            state="disabled",
            activate_scrollbars=True
        )  # read-only console textbox with auto vertical scrollbar
        self.console.grid(row=1, column=0, sticky="nsew", padx=10, pady=(2, 10))  # position console textbox

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("LOLCODE files", "*.lol"), ("All files", "*.*")])  # open file dialog
        if not file_path:  # check if user cancelled dialog
            return  # abort action
        self.file_label.configure(text=f"File: {os.path.basename(file_path)}")  # update label with filename
        with open(file_path, "r") as f:  # open selected .lol file
            content = f.read()  # read raw source code
        self.editor.delete("1.0", "end")  # clear existing editor text
        self.editor.insert("1.0", content)  # insert loaded content into editor

    def write_console(self, text):
        self.console.configure(state="normal")  # enable textbox for editing
        self.console.insert("end", text)  # append message to console
        self.console.see("end")  # automatically autoscroll to latest output
        self.console.configure(state="disabled")  # disable to maintain read-only state

    def run_code(self):
        for row in self.lexeme_tree.get_children():  # loop through old lexeme rows
            self.lexeme_tree.delete(row)  # wipe previous lexeme items
        for row in self.symbol_tree.get_children():  # loop through old symbol rows
            self.symbol_tree.delete(row)  # wipe previous symbol items
        self.console.configure(state="normal")  # unlock console for reset
        self.console.delete("1.0", "end")  # clear previous execution output
        self.console.configure(state="disabled")  # lock console again
        source_code = self.editor.get("1.0", "end-1c")  # extract code from editor widget

        if not analyze:  # handle case where analyzer.py is absent
            self.write_console("[Warning]: analyzer.py could not be imported. Running UI in standalone mockup mode.\n")  # warn user in console
            self.lexeme_tree.insert("", "end", values=("HAI", "Code Delimiter"))  # insert sample lexeme 1
            self.lexeme_tree.insert("", "end", values=("I HAS A", "Variable Declaration"))  # insert sample lexeme 2
            self.symbol_tree.insert("", "end", values=("IT", "NOOB"))  # insert placeholder symbol row
            self.write_console("UI ready. Connect backend parser/interpreter to execute full logic.\n")  # mock execution note
            return  # end execution

        try:
            result = analyze(source_code)  # execute bridge function returning token/symbol dict
        except Exception as e:
            self.write_console(f"[Fatal Runtime Error]: {str(e)}\n")  # print unexpected unhandled crash
            return  # stop execution

        tokens = result.get("tokens", [])  # extract list of token tuples
        for token in tokens:  # iterate through all returned tokens
            lexeme, classification = token[0], token[1]  # unpack lexeme and token classification
            if classification != "Linebreak":  # filter hidden grammatical linebreaks
                self.lexeme_tree.insert("", "end", values=(lexeme, classification))  # add token row to treeview

        symbols = result.get("symbols", [])  # retrieve symbol rows [(identifier, value)]
        for identifier, value in symbols:  # iterate through symbol entries
            self.symbol_tree.insert("", "end", values=(identifier, str(value)))  # add variable row to table

        error = result.get("error")  # check for lexical or syntax error
        if error:  # if an error exists in result dict
            err_type, line, msg = error  # unpack error components
            self.write_console(f"[{err_type} at line {line}]: {msg}\n")  # print formatted error
        else:
            self.write_console("Lexical and syntax analysis successful.\n")  # print success status in console

if __name__ == "__main__":
    app = LOLCodeInterpreterUI()  # instantiate window instance
    app.mainloop()  # start the Tkinter event loop