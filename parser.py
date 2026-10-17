# CMSC 124 - ST-5L PROJECT
# For Milestone 2: Parser for Parse Trees
# It reads the lexer's list of tokens and checks that they follow the LOLCODE grammar, building a parse tree as it goes
# It checks the order of the tokens (HAI ... KTHXBYE, statements, expressions), not what the program does when it runs
# Each rule is parse_x(tokens, pos): return (node, new_pos), or raise a ParseError with the line number if the tokens do not fit

# Imports
from symbols import SymbolTable

"""
NODE NAMES
  literal           leaf("NUMBR", "12")  leaf("NUMBAR", "3.14")  leaf("YARN", "text")  leaf("TROOF", "WIN")
  variable in expr  leaf("Identifier", "var")
  declaration       branch("VARIABLE", [leaf("Identifier", "num"), branch("Value", [expr])])
                    (the Value child is left out when there is no ITZ)
  arithmetic        branch("ARITHMETIC", [leaf("OP", "SUM OF"), left, right])
  comparison        branch("COMPARISON", [leaf("OP", "BOTH SAEM"), left, right])
  boolean           branch("BOOLEAN", [leaf("OP", "ALL OF"), operand, operand, ...])
  print / input     branch("PRINT", [expr])   branch("INPUT", [leaf("Identifier", "var")])
  assignment        branch("ASSIGNMENT", [leaf("Identifier", "var"), expr])
  typecast          branch("TYPECAST", [expr_or_identifier, leaf("TYPE", "NUMBAR")])
  if-else           branch("IF_ELSE", [branch("YA_RLY", [stmt_list]), branch("NO_WAI", [stmt_list])])
  switch            branch("SWITCH", [branch("OMG", [literal, stmt_list]), ..., branch("OMGWTF", [stmt_list])])
  loop              branch("LOOP", [leaf("Label", "lp"), step, cond, stmt_list])
  break / return    leaf("BREAK", "GTFO")   branch("RETURN", [expr])
  function          branch("FUNCTION", [leaf("Name", "add"), branch("PARAMS", [...]), stmt_list])
  call              branch("CALL", [leaf("Name", "add"), branch("ARGS", [expr, ...])])
"""

# Constants
CLS_VARIDENT = "Variable Identifier" # The classification the lexer gives to variable names
CLS_STRING_DELIM = "String Delimiter" # The classification of the " that opens and closes a string
CLS_LINEBREAK = "Linebreak" # The lexer must emit ("\n", "Linebreak", line)

SKIP_CLASSES = [] # Classifications to drop before parsing (e.g. ["Comment"] if the lexer emits comments)
TYPE_NAMES = ["NOOB", "NUMBR", "NUMBAR", "YARN", "TROOF"] # The type names that can follow MAEK or IS NOW A
LITERAL_CLASSES = ["NUMBR Literal", "NUMBAR Literal", "String Literal", "TROOF Literal"] # The classifications the lexer gives to literals

# A statement list stops when it sees one of these
STATEMENT_END = ["KTHXBYE", "OIC", "NO WAI", "MEBBE", "OMG", "OMGWTF", "IM OUTTA YR", "IF U SAY SO", "BUHBYE"]

# Nodes that only group other nodes; simplify() splices them into their parent so the printed tree is shorter
WRAPPERS = ["MAIN", "MAIN_BODY", "WAZZUP"]

# =====================================================================
# HELPERS AND ERROR HANDLING
# =====================================================================

# ParseError is raised when the tokens do not follow the grammar
class ParseError(Exception):
    def __init__(self, message, line):
        Exception.__init__(self, message)
        self.message = message # The text describing what went wrong
        self.line = line # The line number where it went wrong

# Builds a leaf node which is a name and a piece of text, e.g. ("Identifier", "var")
def leaf(name, text):
    return (name, text)

# Builds a branch node which is a name and a list of child nodes, e.g. ("PRINT", [expr])
def branch(name, children):
    return (name, children)

# Looks at the token at pos + offset without consuming it
def peek(tokens, pos, offset=0):
    i = pos + offset # The index of the token we want to look at
    if i < len(tokens): # Make sure we are not past the end of the list
        if tokens[i][1] in LITERAL_CLASSES: # tokens[i][1] is the classification
            return "<literal>"
        return tokens[i][0] # tokens[i][0] is the lexeme text
    
    return None

# Same as peek, but returns the classification (e.g. "Variable Identifier") instead of the lexeme
def peek_cls(tokens, pos, offset=0):
    i = pos + offset # The index of the token we want to look at
    if i < len(tokens):
        return tokens[i][1] # tokens[i][1] is the classification
    
    return None 

# Gives the line number to put in an error message
def current_line(tokens, pos):
    if pos < len(tokens): # If we are not past the end of the token list, use the line of the next token
        return tokens[pos][2] # tokens[pos][2] is the line number of that token
    
    if len(tokens) > 0: # If we are past the end of the token list, use the line of the last token
        return tokens[len(tokens) - 1][2] # Past the end, so use the line of the last token
    
    return 1 # No tokens at all

# Describes the token at pos for an error message, e.g. "'VISIBLE'" or "end of line"
def describe(tokens, pos):
    if pos >= len(tokens): # Past the end of the token list
        return "end of file"
    
    if tokens[pos][1] == CLS_LINEBREAK: # A linebreak token has no useful text
        return "end of line"
    
    return "'" + tokens[pos][0] + "'"

# Raises a ParseError like "expected 'KTHXBYE', found end of file"
def error_here(tokens, pos, expected):
    raise ParseError("expected " + expected + ", found " + describe(tokens, pos), current_line(tokens, pos))

# Consumes one keyword and returns the new position, e.g. pos = expect(tokens, pos, "HAI")
def expect(tokens, pos, lexeme):
    if peek(tokens, pos) == lexeme: # The next token is the keyword we wanted
        return pos + 1 # Move past it
    
    error_here(tokens, pos, "'" + lexeme + "'") # Anything else is a syntax error

# Consumes a variable name and returns (name, new_pos)
def expect_varident(tokens, pos):
    if peek_cls(tokens, pos) == CLS_VARIDENT: # The next token must be a variable identifier
        return tokens[pos][0], pos + 1
    
    error_here(tokens, pos, "a variable name")

# Consumes a function name and returns (name, new_pos)
def expect_funcident(tokens, pos):
    if peek_cls(tokens, pos) == CLS_VARIDENT: # The next token must be a function identifier (same classification as a variable)
        return tokens[pos][0], pos + 1
    
    error_here(tokens, pos, "a function name")

# True if the next token is a linebreak
def at_linebreak(tokens, pos):
    return peek_cls(tokens, pos) == CLS_LINEBREAK

# Consumes zero or more linebreaks (blank lines, comment-only lines)
def skip_linebreaks(tokens, pos):
    while at_linebreak(tokens, pos): # Keep going while the next token is a linebreak
        pos = pos + 1

    return pos

# Consumes one or more linebreaks; it is an error if there is none
def expect_linebreak(tokens, pos):
    if not at_linebreak(tokens, pos): # A statement must be followed by a new line
        error_here(tokens, pos, "a new line")

    return skip_linebreaks(tokens, pos) # Also swallow any blank lines after it

# Placeholder for a rule nobody has written yet; every unfinished rule calls this
# TODO: [DELETE ONCE ALL DONE]
def not_written(tokens, pos, rule):
    raise ParseError("parser rule not written yet: " + rule,
                     current_line(tokens, pos))

# Turns a parse tree into the indented text
def tree_to_string(node):
    lines = [] # One string per printed line
    tree_lines(node, "", True, True, lines)
    return "\n".join(lines) # Join the lines with newlines

# Adds the printed lines for one node and for each of its children
def tree_lines(node, prefix, is_last, is_root, lines):
    name = node[0] # A node is (name, payload)
    payload = node[1] # The payload is a string (leaf) or a list of children (branch)

    if isinstance(payload, str): # A leaf prints as "NAME: text"
        text = name + ": " + payload
    else: # A branch prints as just its name
        text = name

    if is_root: # The root node has no branch drawing in front of it
        lines.append(text)
        child_prefix = ""
    else:
        if is_last: # The last child gets an elbow and its children get blank indentation
            lines.append(prefix + "\u2514\u2500\u2500 " + text) # └── 
            child_prefix = prefix + "    "
        else: # Other children get a tee and their children get a vertical line
            lines.append(prefix + "\u251c\u2500\u2500 " + text) # ├── 
            child_prefix = prefix + "\u2502   " # │

    if not isinstance(payload, str): # Only branches have children to print
        for i in range(len(payload)):
            tree_lines(payload[i], child_prefix, i == len(payload) - 1, False, lines) # This is the last child

# Splices the children of wrapper nodes into their parent (for display only)
def simplify(node):
    if isinstance(node[1], str): # A leaf has nothing to simplify
        return node
    
    kids = [] # The new list of children
    for child in node[1]:
        child = simplify(child) # Simplify the child first
        if child[0] in WRAPPERS: # A wrapper is replaced by its own children
            kids.extend(child[1])
        else:
            kids.append(child)

    return (node[0], kids)

# T=akes the list of tokens from the lexer and returns a parse tree
def parse(tokens):
    clean = [] # The tokens we actually parse
    for tok in tokens:
        if tok[1] not in SKIP_CLASSES: # Drop any classification listed in SKIP_CLASSES
            clean.append(tok)
    tree, pos = parse_program(clean, 0) # Start at the first token with the top rule
    
    return simplify(tree) # Tidy the tree before handing it back


# =====================================================================
# PROGRAM STRUCTURE
# =====================================================================

# <program> ::= <main> | <func_list> <linebreak> <main>
#             | <main> <linebreak> <func_list>
#             | <func_list> <linebreak> <main> <linebreak> <func_list>
def parse_program(tokens, pos):
    children = [] # Functions and the main program, in the order they appear
    pos = skip_linebreaks(tokens, pos) # Skip blank or comment-only lines before the program

    while peek(tokens, pos) == "HOW IZ I": # Functions may come before HAI
        func, pos = parse_func_def(tokens, pos)
        children.append(func)
        pos = skip_linebreaks(tokens, pos)

    main, pos = parse_main(tokens, pos) # The HAI ... KTHXBYE part
    children.append(main)
    pos = skip_linebreaks(tokens, pos)
    
    while peek(tokens, pos) == "HOW IZ I": # Functions may also come after KTHXBYE
        func, pos = parse_func_def(tokens, pos)
        children.append(func)
        pos = skip_linebreaks(tokens, pos)
    
    if pos < len(tokens): # Anything left over after all that is not allowed
        error_here(tokens, pos, "end of file")
    return branch("PROGRAM", children), pos

# <main> ::= HAI <linebreak> KTHXBYE | HAI <linebreak> <main_body> KTHXBYE
def parse_main(tokens, pos):
    pos = expect(tokens, pos, "HAI") # The program must start with HAI
    children = [leaf("START", "HAI")]
    pos = expect_linebreak(tokens, pos)
    
    if peek(tokens, pos) is None: # The file ended right after HAI
        error_here(tokens, pos, "'KTHXBYE'")
    
    if peek(tokens, pos) != "KTHXBYE": # If it is not KTHXBYE yet, there is a body to parse
        body, pos = parse_main_body(tokens, pos)
        children.append(body)
    
    pos = expect(tokens, pos, "KTHXBYE") # The program must end with KTHXBYE
    children.append(leaf("END", "KTHXBYE"))
    return branch("MAIN", children), pos

# <main_body> ::= <wazzup> <linebreak>
#               | <wazzup> <linebreak> <statement_list> <linebreak>
#               | <statement_list> <linebreak>
def parse_main_body(tokens, pos):
    children = []
    if peek(tokens, pos) == "WAZZUP": # The variable section must come first
        wazzup, pos = parse_wazzup(tokens, pos)
        children.append(wazzup)
        pos = expect_linebreak(tokens, pos) # The linebreak after BUHBYE
    
    if peek(tokens, pos) != "KTHXBYE": # Whatever is left before KTHXBYE is the statements
        stmts, pos = parse_statement_list(tokens, pos)
        children.append(stmts)
    
    return branch("MAIN_BODY", children), pos

# <statement_list> ::= <statement> <linebreak> <statement_list> | <statement>
def parse_statement_list(tokens, pos):
    stmts = [] # The statements found so far
    pos = skip_linebreaks(tokens, pos) # Skip blank lines before the first statement
    
    while peek(tokens, pos) is not None and peek(tokens, pos) not in STATEMENT_END: # Stop at the end of the file or a closing keyword
        stmt, pos = parse_statement(tokens, pos) # Parse one statement
        stmts.append(stmt)
        pos = expect_linebreak(tokens, pos) # Every statement must end with a new line
    
    if len(stmts) == 0: # The grammar needs at least one statement
        error_here(tokens, pos, "a statement")

    return branch("STATEMENT_LIST", stmts), pos

# <statement> ::= <print> | <gimmeh> | <assignment> | <typecast> | <ifelse>
#               | <switch> | <loop_delimiter> | <func_call> | <return> | <gtfo> | <expr>
def parse_statement(tokens, pos):
    word = peek(tokens, pos) # The first word decides which rule to call

    if word == "VISIBLE":
        return parse_print(tokens, pos) 
    if word == "GIMMEH":
        return parse_gimmeh(tokens, pos)
    if word == "GTFO":
        return parse_gtfo(tokens, pos)  
    if word == "MAEK":
        return parse_typecast(tokens, pos) 
    if word == "O RLY?":
        return parse_ifelse(tokens, pos)
    if word == "WTF?":
        return parse_switch(tokens, pos)
    if word == "IM IN YR":
        return parse_loop(tokens, pos)  
    if word == "I IZ":
        return parse_func_call(tokens, pos)
    if word == "FOUND YR":
        return parse_return(tokens, pos)
    
    if word == "I HAS A": # Declarations are only allowed inside WAZZUP ... BUHBYE
        raise ParseError("declarations must go inside WAZZUP ... BUHBYE", current_line(tokens, pos))

    if peek_cls(tokens, pos) == CLS_VARIDENT: # A statement that starts with a variable name
        after = peek(tokens, pos, 1) # Look at the token after the variable
        if after == "R":
            return parse_assignment(tokens, pos)
        if after == "IS NOW A":
            return parse_typecast(tokens, pos)
    expr, pos = parse_expression(tokens, pos) # Anything else must be an expression used as a statement

    return branch("EXPRESSION_STATEMENT", [expr]), pos

# =====================================================================
# TODO: SAMUEL -- expressions, input/output, assignment, typecasting, calls
# =====================================================================

# <expr> ::= <arith> | <comparison> | <boolean> | <literal> | varident
# Look at the next token to decide which rule to call:
#   SUM OF / DIFF OF / PRODUKT OF / QUOSHUNT OF / MOD OF / BIGGR OF / SMALLR OF -> parse_arith
#   BOTH SAEM / DIFFRINT -> parse_comparison
#   BOTH OF / EITHER OF / WON OF / NOT / ALL OF / ANY OF -> parse_boolean
#   SMOOSH -> parse_smoosh
#   a literal token (classification in LITERAL_CLASSES, or a String Delimiter) -> parse_literal
#   CLS_VARIDENT -> leaf("Identifier", name)
#   I IZ -> parse_func_call        MAEK -> parse_typecast   (so calls/casts can be operands)
# Return the inner node directly (do not wrap it in an EXPRESSION node).
def parse_expression(tokens, pos):
    not_written(tokens, pos, "parse_expression")

# <literal> ::= numbr | numbar | yarn | troof
# The lexer already tells you the type through the classification:
#   "NUMBR Literal" -> leaf("NUMBR", text)    "NUMBAR Literal" -> leaf("NUMBAR", text)
#   "TROOF Literal" -> leaf("TROOF", text)
# A string is: String Delimiter, an OPTIONAL String Literal, String Delimiter.
# An empty string "" is just the two delimiters. Return leaf("YARN", text) (text = "" if empty).
# Read a literal's real text with tokens[pos][0] (peek hides it).
def parse_literal(tokens, pos):
    not_written(tokens, pos, "parse_literal")

# <arith> ::= <arith_op> <expr> AN <expr>
# Operands are <expr>, so call parse_expression twice (that is the recursion).
def parse_arith(tokens, pos):
    not_written(tokens, pos, "parse_arith")

# <comparison> ::= <comp_op> <expr> AN <expr>        comp_op: BOTH SAEM | DIFFRINT
def parse_comparison(tokens, pos):
    not_written(tokens, pos, "parse_comparison")

# <boolean> ::= <bool_op> <expr> AN <expr> | NOT <expr> | <bool_op_inf> <expr_list> MKAY
#   bool_op: BOTH OF | EITHER OF | WON OF      bool_op_inf: ALL OF | ANY OF
# <expr_list> ::= <expr> AN <expr_list> | <expr>   (a loop: parse an expr, keep going while next is AN)
def parse_boolean(tokens, pos):
    not_written(tokens, pos, "parse_boolean")

# <smoosh> ::= SMOOSH <expr_list>
# <expr_list> ::= <expr> AN <expr_list> | <expr>
# expect SMOOSH, parse_expression, then loop while the next token is AN: skip it and
# parse another expression. There is NO MKAY. Return branch("SMOOSH", [expr, expr, ...]).
def parse_smoosh(tokens, pos):
    not_written(tokens, pos, "parse_smoosh")

# <assignment> ::= varident R <expr>
def parse_assignment(tokens, pos):
    not_written(tokens, pos, "parse_assignment")

# <typecast> ::= MAEK <expr> A <type> | MAEK <expr> <type> | varident IS NOW A <type>
# <type> is one of TYPE_NAMES. Handle all three forms (A is optional in the MAEK form).
def parse_typecast(tokens, pos):
    not_written(tokens, pos, "parse_typecast")

# <print> ::= VISIBLE <expr> | VISIBLE <expr> + <print_list> | VISIBLE <expr> <print_list>
# <print_list> ::= <expr> + <print_list> | <expr> <print_list> | <expr>
# i.e. one or more operands, separated by "+" or just by spaces.
# expect VISIBLE, parse_expression, then keep looping until the end of the line:
# skip a "+" if there is one, then parse another expression.
# Return branch("PRINT", [expr, expr, ...]).
def parse_print(tokens, pos):
    not_written(tokens, pos, "parse_print")

# <gimmeh> ::= GIMMEH varident
# expect GIMMEH, expect_varident, return branch("INPUT", [leaf("Identifier", name)]).
def parse_gimmeh(tokens, pos):
    not_written(tokens, pos, "parse_gimmeh")

# <func_call> ::= I IZ funcident MKAY | I IZ funcident <args> MKAY
# <args> ::= YR <expr> | YR <expr> AN <args>      (loop: YR expr, then while next is AN: YR expr)
# Use expect_funcident for the name.
def parse_func_call(tokens, pos):
    not_written(tokens, pos, "parse_func_call")

# <return> ::= FOUND YR <expr>
def parse_return(tokens, pos):
    not_written(tokens, pos, "parse_return")


# =====================================================================
# TODO: PHIA -- declarations, control flow, function definitions, symbol table
# =====================================================================
# NOTE: parse_statement_list and parse_var_decl_list already consume the
# linebreak after their last item. After calling one, use skip_linebreaks,
# never expect_linebreak.

# <wazzup> ::= WAZZUP <linebreak> BUHBYE
#            | WAZZUP <linebreak> <var_decl_list> <linebreak> BUHBYE
# Steps: expect WAZZUP, expect_linebreak, if the next token is not BUHBYE call
# parse_var_decl_list, then expect BUHBYE. Stop right after BUHBYE
# (parse_main_body consumes the linebreak that follows).
# Return branch("WAZZUP", [var_decl_list_node]) -- an empty list if there are no declarations.
def parse_wazzup(tokens, pos):
    not_written(tokens, pos, "parse_wazzup")

# <var_decl_list> ::= <declaration> <linebreak> <var_decl_list> | <declaration>
# Loop while the next token is I HAS A: parse_declaration, then expect_linebreak
# (that also swallows the linebreak before BUHBYE). Error if there is no declaration at all.
# Return branch("VARIABLE_DECLARATION_LIST", [declaration, ...]).
def parse_var_decl_list(tokens, pos):
    not_written(tokens, pos, "parse_var_decl_list")

# <declaration> ::= I HAS A varident | I HAS A varident ITZ <literal> | I HAS A varident ITZ <expr>
# A literal is also an <expr>, so ONE optional ITZ branch covers both:
# expect I HAS A, expect_varident, and if the next token is ITZ call parse_expression (Samuel).
# Return branch("VARIABLE", [leaf("Identifier", name), branch("Value", [expr])])
# (leave the Value child out when there is no ITZ).
def parse_declaration(tokens, pos):
    not_written(tokens, pos, "parse_declaration")

# <ifelse> ::= O RLY? <linebreak> <ya_rly> <linebreak> <no_wai> <linebreak> OIC
#            | O RLY? <linebreak> <ya_rly> <linebreak> OIC
# <ya_rly> ::= YA RLY <linebreak> <statement_list>
# <no_wai> ::= NO WAI <linebreak> <statement_list>
# NO WAI is optional: after YA RLY's statements, check if the next token is NO WAI.
# Return branch("IF_ELSE", [branch("YA_RLY", [stmt_list]), branch("NO_WAI", [stmt_list])]).
def parse_ifelse(tokens, pos):
    not_written(tokens, pos, "parse_ifelse")

# <switch> ::= WTF? <linebreak> <omg_cases> <linebreak> OIC
#            | WTF? <linebreak> <omg_cases> <linebreak> <omgwtf> <linebreak> OIC
# <omg_cases> ::= <omg> <linebreak> <omg_cases> | <omg>
# <omg> ::= OMG <literal> <linebreak> <statement_list>      (use Samuel's parse_literal)
# <omgwtf> ::= OMGWTF <linebreak> <statement_list>
# Loop while the next token is OMG. GTFO inside a case is just a normal statement.
def parse_switch(tokens, pos):
    not_written(tokens, pos, "parse_switch")

# <loop_delimiter> ::= IM IN YR varident <loop_step> <linebreak> <statement_list> <linebreak> IM OUTTA YR varident
#                    | IM IN YR varident <loop_step> <loop_cond> <linebreak> <statement_list> <linebreak> IM OUTTA YR varident
# <loop_step> ::= <step_op> YR varident        step_op: UPPIN | NERFIN
# <loop_cond> ::= TIL <expr> | WILE <expr>     (use Samuel's parse_expression)
# The loop cond is optional: check if the next token is TIL or WILE.
# Also check that the name after IM OUTTA YR matches the name after IM IN YR.
def parse_loop(tokens, pos):
    not_written(tokens, pos, "parse_loop")

# <gtfo> ::= GTFO
# expect GTFO, return leaf("BREAK", "GTFO").
def parse_gtfo(tokens, pos):
    not_written(tokens, pos, "parse_gtfo")

# <func_def> ::= HOW IZ I funcident <linebreak> <statement_list> <linebreak> IF U SAY SO
#              | HOW IZ I funcident <params> <linebreak> <statement_list> <linebreak> IF U SAY SO
# <params> ::= YR varident | YR varident AN <params>     (loop: YR varident, then while next is AN: YR varident)
# Use expect_funcident for the name. Do NOT consume a linebreak after IF U SAY SO
# (parse_program does that).
def parse_func_def(tokens, pos):
    not_written(tokens, pos, "parse_func_def")

# Walk the tree returned by parse() and declare every variable it finds.
# Look for nodes named "VARIABLE". Their children are a leaf "Identifier" and an
# optional branch "Value" (the Value's child is the expression). If that expression
# is a plain literal leaf, declare(name, its text); otherwise declare(name) with no value.
# Then recurse into the children of every branch node. Return the SymbolTable.
def build_symbol_table(tree):
    not_written([], 0, "build_symbol_table")

# =====================================================================
# SKELETON SELF-TEST: python parser.py --> DELETE ONCE ALL DONE
# =====================================================================

if __name__ == "__main__": # Only runs when you type "python parser.py", not when another file imports it
    # Builds a stand-in rule that just records its own name
    def make_dummy(name):
        def dummy(tokens, pos):
            first = tokens[pos][0] # The first lexeme of the statement
            while pos < len(tokens) and tokens[pos][1] != CLS_LINEBREAK:
                pos = pos + 1               # Eat the rest of the line
            return leaf(name, first), pos
        return dummy

    # Builds a tiny program: HAI, one statement line (if given), KTHXBYE
    def make_tokens(statement):
        toks = [("HAI", "Code Delimiter", 1), ("\n", CLS_LINEBREAK, 1)]
        if len(statement) > 0:
            for word, cls in statement:
                toks.append((word, cls, 2))
            toks.append(("\n", CLS_LINEBREAK, 2))
        toks.append(("KTHXBYE", "Code Delimiter", 3))
        return toks

    # Pulls the list of statements out of a finished tree
    def statements_of(tree):
        for child in tree[1]:
            if child[0] == "STATEMENT_LIST":
                return child[1]
        return []

    OK = True # Becomes False if any check fails

    # Prints PASS or FAIL for one check
    def check(label, passed):
        global OK
        if passed:
            print("PASS  " + label)
        else:
            print("FAIL  " + label)
            OK = False

    # 1. An empty program must parse
    tree = parse(make_tokens([]))
    check("HAI / KTHXBYE parses", tree[0] == "PROGRAM")

    # 2. Missing KTHXBYE must give a line number and a message
    broken = make_tokens([])
    broken = broken[:len(broken) - 1] # Remove the KTHXBYE token
    try:
        parse(broken)
        check("missing KTHXBYE is reported", False)
    except ParseError as e:
        check("missing KTHXBYE is reported (line " + str(e.line) + ": " + e.message + ")", True)

    # 3. The dispatcher sends each kind of statement to the right rule
    fake_names = ["parse_print", "parse_gimmeh", "parse_gtfo", "parse_typecast",
                  "parse_ifelse", "parse_switch", "parse_loop", "parse_func_call",
                  "parse_return", "parse_declaration", "parse_assignment",
                  "parse_expression"]
    for name in fake_names:
        globals()[name] = make_dummy(name) # Replace the real rule with the stand-in

    cases = [ # (the tokens of one statement, the rule that should be called)
        ([("VISIBLE", "Output Keyword"), ("1", "NUMBR Literal")], "parse_print"),
        ([("GIMMEH", "Input Keyword"), ("x", CLS_VARIDENT)], "parse_gimmeh"),
        ([("GTFO", "Break Keyword")], "parse_gtfo"),
        ([("MAEK", "Typecast Keyword"), ("x", CLS_VARIDENT)], "parse_typecast"),
        ([("x", CLS_VARIDENT), ("IS NOW A", "Typecast Keyword"), ("YARN", "Type Literal")], "parse_typecast"),
        ([("O RLY?", "If-Else Delimiter")], "parse_ifelse"),
        ([("WTF?", "Switch Delimiter")], "parse_switch"),
        ([("IM IN YR", "Loop Delimiter")], "parse_loop"),
        ([("I IZ", "Function Call"), ("f", CLS_VARIDENT), ("MKAY", "Expression Delimiter")], "parse_func_call"),
        ([("FOUND YR", "Return Keyword"), ("1", "NUMBR Literal")], "parse_return"),
        ([("x", CLS_VARIDENT), ("R", "Assignment Operator"), ("5", "NUMBR Literal")], "parse_assignment"),
        ([("SUM OF", "Arithmetic Operator"), ("1", "NUMBR Literal")], "parse_expression"),
    ]
    for statement, expected in cases:
        stmts = statements_of(parse(make_tokens(statement)))
        got = ""
        if len(stmts) == 1:
            got = stmts[0][0] # The name of the dummy that was called
            if got == "EXPRESSION_STATEMENT": # An expression statement wraps the dummy inside it
                got = stmts[0][1][0][0]
        check(statement[0][0] + " -> " + expected, got == expected)

    # 4. Two statements with a blank line between them stay two statements
    two = [("HAI", "Code Delimiter", 1), ("\n", CLS_LINEBREAK, 1),
           ("VISIBLE", "Output Keyword", 2), ("1", "NUMBR Literal", 2), ("\n", CLS_LINEBREAK, 2),
           ("\n", CLS_LINEBREAK, 3),
           ("VISIBLE", "Output Keyword", 4), ("2", "NUMBR Literal", 4), ("\n", CLS_LINEBREAK, 4),
           ("KTHXBYE", "Code Delimiter", 5)]
    check("blank line between statements", len(statements_of(parse(two))) == 2)

    # 5. I HAS A outside WAZZUP is a syntax error
    try:
        parse(make_tokens([("I HAS A", "Variable Declaration"), ("x", CLS_VARIDENT)]))
        check("I HAS A outside WAZZUP is rejected", False)
    except ParseError as e:
        check("I HAS A outside WAZZUP is rejected (line " + str(e.line) + ")", True)

    print()
    if OK:
        print("Skeleton OK.")
    else:
        print("Skeleton has a problem -- see FAIL lines above.")