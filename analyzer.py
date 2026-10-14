# CMSC 124 - ST-5L PROJECT
# Runs the whole pipeline on a program: lexer -> parser -> symbol table
# main.py (command line) and ui.py (the UI) both call analyze(), so they always show the same thing

# Imports
from lexer import tokenize, LexerError # tokenize() is the lexer's main function; LexerError is raised on bad input
from parser import parse, build_symbol_table, ParseError # parse() builds the parse tree; build_symbol_table() lists the variables; ParseError is raised on bad syntax

# Main Function
def analyze(source):
    result = {"tokens": [], "tree": None, "symbols": [], "error": None} # Start with an empty result

    # Run the lexer, then the parser
    try:
        result["tokens"] = tokenize(source) # List of (lexeme, classification, line)
        result["tree"] = parse(result["tokens"]) # parse() takes the list of tokens and returns a parse tree
    except LexerError as e:
        result["error"] = ("Lexical error", e.line, e.message) # e.line and e.message were set in LexerError (see lexer.py)
        return result
    except ParseError as e:
        result["error"] = ("Syntax error", e.line, e.message) # e.line and e.message were set in ParseError (see parser.py)
        return result

    # Build the symbol table from the finished tree
    try:
        result["symbols"] = build_symbol_table(result["tree"]).rows() # rows() gives a list of (identifier, value)
    except ParseError:
        pass # [NOT YET WRITTEN build_symbol_table]

    return result