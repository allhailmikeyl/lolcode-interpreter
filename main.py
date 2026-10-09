# CMSC 124 - ST-5L PROJECT
# Temporary command-line tester for the lexer
# It reads a .lol file, runs the lexer on it, and prints every token
# The UI (ui.py) will do the same thing and show the result in a table (after implementation)

# Imports
import sys # sys lets us read what the user typed after "python main.py" (the file name)
from lexer import tokenize, LexerError # tokenize() is the lexer's main function; LexerError is raised on bad input.

# Main Function
def main():
    # sys.argv is the list of words typed in the terminal:
    #   python main.py tests/basic.lol  ->  ["main.py", "tests/basic.lol"]
    if len(sys.argv) < 2:
        print("Usage: python main.py <file.lol>")
        return # stop here, nothing to lex

    # sys.argv[1] is the file name
    with open(sys.argv[1]) as f:
        source = f.read()

    # Run the lexer
    try:
        tokens = tokenize(source) # list of (lexeme, classification, line)
    except LexerError as e:
        print("Error on line " + str(e.line) + ": " + e.message) # e.line and e.message were set in LexerError (see lexer.py)
        return  # stop here, there are no tokens to print

    # Go through the token list and print one row per token.
    for lexeme, classification, line in tokens:
        print(str(line) + "\t" + lexeme + "\t" + classification)

main()