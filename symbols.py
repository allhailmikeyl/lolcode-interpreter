# CMSC 124 - ST-5L PROJECT
# The symbol table: maps variable names to their values
# Used by parser.py (build_symbol_table), semantic.py (the interpreter), and the UI

class SymbolTable:
    def __init__(self):
        self.table = {} # Maps an identifier to its value
        self.table["IT"] = None # The sample UI shows IT in the symbol table

    # True if the identifier has been declared
    def exists(self, name):
        return name in self.table

    # Adds a new identifier (with an optional starting value)
    def declare(self, name, value=None):
        self.table[name] = value

    # Gives the value stored for an identifier
    def lookup(self, name):
        if name in self.table:
            return self.table[name]
        return None

    # Changes the value stored for an identifier
    def assign(self, name, value):
        self.table[name] = value

    # Gives a list of (identifier, value)
    def rows(self):
        result = []
        for name in self.table: # Go through every identifier
            result.append((name, self.table[name]))
        return result