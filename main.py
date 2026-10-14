# CMSC 124 - ST-5L PROJECT
# Temporary command-line tester for the lexer
# It reads a .lol file, runs the lexer on it, and prints every token
# The UI (ui.py) will do the same thing and show the result in a table (after implementation)

# Imports
import sys # sys lets us read what the user typed after "python main.py" (the file name)
from analyzer import analyze # analyze() runs the lexer, the parser, and the symbol table
from parser import tree_to_string # tree_to_string() converts the parse tree to text

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

    # Run the lexer, the parser, and the symbol table
    result = analyze(source) # A dictionary with "tokens", "tree", "symbols", and "error" (see analyzer.py)
    error = result["error"] # None if everything worked, otherwise (kind, line, message)
 
    # If the lexer failed, there are no lexemes to show
    if error is not None and error[0] == "Lexical error":
        print(error[0] + " on line " + str(error[1]) + ": " + error[2]) 
        return

    tokens = result["tokens"] # List of (lexeme, classification, line)
    shown = [t for t in tokens if t[1] != "Linebreak"] # Linebreak tokens are only for the parser, so hide them in the table
    
    # Find the longest lexeme
    width = len("Lexeme")
    for lexeme, classification, line in shown: # Go through every token
        if len(lexeme) > width: # Remember the widest lexeme seen so far
            width = len(lexeme)
 
    print("Line".ljust(6) + "Lexeme".ljust(width + 2) + "Classification")
    print("-" * (6 + width + 2 + 14))

    # Go through the token list and print one row per token
    for lexeme, classification, line in shown:
        print(str(line).ljust(6) + lexeme.ljust(width + 2) + classification)
    print()
 
    # If the parser failed, there is no tree to show
    if error is not None:
        print(error[0] + " on line " + str(error[1]) + ": " + error[2])
        return

    # Print the parse tree
    print(tree_to_string(result["tree"]))
    print()

    # Print the symbol table
    print("Symbol Table")
    print("-" * 30)
    for name, value in result["symbols"]:
        print(name.ljust(16) + str(value))
 
main()