# CMSC 124 - ST-5L PROJECT
# For Milestone 2: Parser for Parse Trees
# It reads the lexer's list of tokens and checks that they follow the LOLCODE grammar, building a parse tree as it goes
# It checks the order of the tokens (HAI ... KTHXBYE, statements, expressions), not what the program does when it runs
# Each rule is parse_x(tokens, pos): return (node, new_pos), or raise a ParseError with the line number if the tokens do not fit