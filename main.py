# CMSC 124 - ST-5L PROJECT
# Temporary command-line tester for the lexer
# It reads a .lol file, runs the lexer on it, and prints every token
# The UI (ui.py) will do the same thing and show the result in a table (after implementation)

# Imports
import sys # sys lets us read what the user typed after "python main.py" (the file name)
from lexer import tokenize, LexerError # tokenize() is the lexer's main function; LexerError is raised on bad input
from parser import parse, tree_to_string, ParseError # parse() is the parser's main function; tree_to_string() converts the parse tree to a string

# Main Function
def main():
    # sys.argv is the list of words typed in the terminal:
    # python main.py tests/basic.lol  ->  ["main.py", "tests/basic.lol"]
    if len(sys.argv) < 2:
        print("Usage: python main.py <file.lol>")
        return

    # sys.argv[1] is the file name
    with open(sys.argv[1]) as f:
        source = f.read()

    # Run the lexer
    try:
        tokens = tokenize(source) # List of (lexeme, classification, line)
    except LexerError as e:
        print("Error on line " + str(e.line) + ": " + e.message) # e.line and e.message were set in LexerError (see lexer.py)
        return 

    # Run the parser
    try:
        tree = parse(tokens) # parse() takes the list of tokens and returns a parse tree
    except ParseError as e:
        print("Syntax error on line " + str(e.line) + ": " + e.message) # e.line and e.message were set in ParseError (see parser.py)
        return
    print(tree_to_string(tree))

    # Find the longest lexeme
    width = len("Lexeme")
    for lexeme, classification, line in tokens: # Go through every token
        if len(lexeme) > width:  # Remember the widest lexeme seen so far
            width = len(lexeme)

    print("Line".ljust(6) + "Lexeme".ljust(width + 2) + "Classification")
    print("-" * (6 + width + 2 + 14))

    # Go through the token list and print one row per token
    for lexeme, classification, line in tokens:
        print(str(line).ljust(6) + lexeme.ljust(width + 2) + classification)
    print()

main()