# CMSC 124 - ST-5L PROJECT
# For Milestone 3: Semantic Analyzer
# It walks the parse tree from parse() and does what the program says
# It checks what the program MEANS (is the variable declared? can this value become a number?)
# Each rule is exec_x(node) (does something) or eval_x(node) (returns a value)

# Imports
from symbols import SymbolTable

# SemanticError is raised when the program is valid LOLCODE but does something that makes no sense
class SemanticError(Exception):
    def __init__(self, message, line):
        Exception.__init__(self, message)
        self.message = message # The text describing what went wrong
        self.line = line # The line number where it went wrong (0 if the tree does not carry lines yet)
 
# GTFO and FOUND YR have to jump out of whatever is running; these classes carry that jump
class BreakSignal(Exception):
    pass
 
class ReturnSignal(Exception):
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value # The value FOUND YR sent back
 
# Gives the line stored in a node
def node_line(node):
    if len(node) > 2:
        return node[2]
    return 0
 
# Gives the LOLCODE type name of a Python value
def type_of(value):
    if value is None:
        return "NOOB"
    if isinstance(value, bool): # Check bool BEFORE int, because True is also an int in Python
        return "TROOF"
    if isinstance(value, int):
        return "NUMBR"
    if isinstance(value, float):
        return "NUMBAR"
    return "YARN"