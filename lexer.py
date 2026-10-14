# CMSC 124 - ST-5L PROJECT
# For Milestone 1: Lexemes (Lexical Analyzer)
# It reads a .lol program and cuts it into lexemes (HAI, I HAS A, var, ITZ, 12, ...), each with a label 
# It checks only what each piece is, not whether the order is valid 
# Each matcher is match_x(source, pos): return None if nothing starts at pos, else ([(lexeme, classification)], new_pos)

# Imports
import re # for regular expressions

# LexerError is raised when the lexer cannot read the input
class LexerError(Exception):
    def __init__(self, message, line):
        Exception.__init__(self, message)
        self.message = message # The text describing what went wrong
        self.line = line # The line number where it went wrong

# List of Literals and Keywords with their corresponding Classification
TROOF_LITERALS = [
    ("WIN", "TROOF Literal"),
    ("FAIL", "TROOF Literal")
]

TYPE_LITERALS = [
    ("NOOB", "Type Literal"),
    ("NUMBR", "Type Literal"),
    ("NUMBAR", "Type Literal"),
    ("YARN", "Type Literal"),
    ("TROOF", "Type Literal")
]

SINGLE_WORD_KEYWORDS = [
    ("HAI", "Code Delimiter"),
    ("KTHXBYE", "Code Delimiter"),
    ("WAZZUP", "Variable Declaration Delimiter"),
    ("BUHBYE", "Variable Declaration Delimiter"),
    ("ITZ", "Variable Assignment"),
    ("R", "Assignment Operator"),
    ("NOT", "Boolean Operator"),
    ("DIFFRINT", "Comparison Operator"),
    ("SMOOSH", "String Concatenation"),
    ("MAEK", "Typecast Keyword"),
    ("A", "Typecast Keyword"),
    ("VISIBLE", "Output Keyword"),
    ("GIMMEH", "Input Keyword"),
    ("MEBBE", "If-Else Keyword"),
    ("OIC", "If-Else/Switch Delimiter"),
    ("OMG", "Switch Case"),
    ("OMGWTF", "Switch Default"),
    ("GTFO", "Break Keyword"),
    ("UPPIN", "Loop Increment"),
    ("NERFIN", "Loop Decrement"),
    ("YR", "Loop/Function Parameter Keyword"),
    ("TIL", "Loop Condition"),
    ("WILE", "Loop Condition"),
    ("MKAY", "Expression Delimiter"),
    ("AN", "Operand Separator"),
]

MULTI_WORD_KEYWORDS = [
    ("I HAS A", "Variable Declaration"),
    ("SUM OF", "Arithmetic Operator"),
    ("DIFF OF", "Arithmetic Operator"),
    ("PRODUKT OF", "Arithmetic Operator"),
    ("QUOSHUNT OF", "Arithmetic Operator"),
    ("MOD OF", "Arithmetic Operator"),
    ("BIGGR OF", "Arithmetic Operator"),
    ("SMALLR OF", "Arithmetic Operator"),
    ("BOTH OF", "Boolean Operator"),
    ("EITHER OF", "Boolean Operator"),
    ("WON OF", "Boolean Operator"),
    ("ANY OF", "Boolean Operator"),
    ("ALL OF", "Boolean Operator"),
    ("BOTH SAEM", "Comparison Operator"),
    ("IS NOW A", "Typecast Keyword"),
    ("O RLY?", "If-Else Delimiter"),
    ("YA RLY", "If-Else Keyword"),
    ("NO WAI", "If-Else Keyword"),
    ("WTF?", "Switch Delimiter"),
    ("IM IN YR", "Loop Delimiter"),
    ("IM OUTTA YR", "Loop Delimiter"),
    ("HOW IZ I", "Function Delimiter"),
    ("IF U SAY SO", "Function Delimiter"),
    ("FOUND YR", "Return Keyword"),
    ("I IZ", "Function Call"),
]

# Gives the length of a keyword entry to be used for sorting
def keyword_length(entry):
    return len(entry[0]) # entry[0] is the lexeme text, e.g. "I HAS A"

# Sort the longest keyword first 
# e.g., "IM OUTTA YR" is tried before anything shorter that starts with the same letters
MULTI_WORD_KEYWORDS.sort(key=keyword_length, reverse=True)

# Checks whether a keyword is allowed to end right before position pos
# This stops "HAIR" from being read as the keyword "HAI" followed by "R"
def is_boundary(source, pos):
    if pos >= len(source): # The end of the file counts as a boundary
        return True
    
    ch = source[pos] # Look at the character right after the keyword

    # A space, tab, newline, carriage return, or comma ends a keyword
    return ch == " " or ch == "\t" or ch == "\n" or ch == "\r" or ch == ","

# Skips spaces, tabs, and newlines; produces no tokens
def match_whitespace(source, pos):
    start = pos # Remember the position where we started
    while pos < len(source) and source[pos] in " \t\r": # Move forward while the current character is whitespace
        pos += 1
    
    if pos == start: # If we did not move, there was no whitespace here
        return None
    
    return ([], pos) # Empty token list (nothing to record), but pos moves forward

# Skips a single newline; produces one token for the linebreak
def match_newline(source, pos):
    if source[pos] == "\n": # If the current character is a newline, we found a linebreak
        return ([("\n", "Linebreak")], pos + 1)
    return None

# Reads a string like and splits it into three tokens: opening quote, the text inside, closing quote
def match_string(source, pos):
    if source[pos] != '"': # A string must start with a double quote
        return None

    # Look for the closing quote, stopping at the end of the line
    end = pos + 1
    while end < len(source) and source[end] != '"' and source[end] != "\n":
        end += 1

    # No closing quote was found before the line ended so unterminated string
    if end >= len(source) or source[end] != '"':
        return None

    # The text between the two quotes
    contents = source[pos + 1:end]

    # Build the token list
    tokens = [] 
    tokens.append(('"', "String Delimiter")) # Opening quote
    if contents != "": # The text inside (an empty string "" has no Literal row)
        tokens.append((contents, "String Literal"))
    tokens.append(('"', "String Delimiter")) # Closing quote

    return (tokens, end + 1) # Continue reading right after the closing quote

def match_number(source, pos):
    # check NUMBAR/float nummbers first so the decimal point isn't split from the integer part
    numbar_match = re.match(r'^-?\d+\.\d+', source[pos:])  
    if numbar_match:
        lexeme = numbar_match.group(0)  # extract matched text 
        end = pos + len(lexeme)          
        if is_boundary(source, end):    # ensure the number ends at a valid separator
            return ([(lexeme, "NUMBAR Literal")], end)

    # check NUMBR/integers second if NUMBAR did not match
    numbr_match = re.match(r'^-?\d+', source[pos:])  
    if numbr_match:
        lexeme = numbr_match.group(0)  
        end = pos + len(lexeme)          
        if is_boundary(source, end):   
            return ([(lexeme, "NUMBR Literal")], end)

    return None  

def match_troof(source, pos):
    for lexeme, classification in TROOF_LITERALS:
        end = pos + len(lexeme)  # to calculate the end position for the target literal
        
        if source[pos:end] == lexeme and is_boundary(source, end): # check if the text matches the exact lexeme and ends at a word boundary
            return ([(lexeme, classification)], end)
    return None  

def match_type(source, pos):
    for lexeme, classification in TYPE_LITERALS:
        end = pos + len(lexeme)  # to calculate end position for the target type keyword
        
        if source[pos:end] == lexeme and is_boundary(source, end): 
            return ([(lexeme, classification)], end)
    return None

def match_comment(source, pos):
    # Single line comment
    if source.startswith("BTW", pos) and is_boundary(source, pos + 3):
        end = pos + 3
        while end < len(source) and source[end] != "\n":
            end += 1
        return ([], end)

    # Multiline comment
    if source.startswith("OBTW", pos) and is_boundary(source, pos + 4):
        search = pos + 4
        while True:
            tldr_pos = source.find("TLDR", search)

            # No TLDR left in the file, so the comment was never closed
            if tldr_pos == -1:
                line = source[:pos].count("\n") + 1 # Line where the OBTW started
                raise LexerError("OBTW has no matching TLDR", line)

            if source[tldr_pos - 1] in " \t\r\n" and is_boundary(source, tldr_pos + 4):
                return ([], tldr_pos + 4)

            search = tldr_pos + 1

    return None

def match_keyword(source, pos):
    for keyword, classification in SINGLE_WORD_KEYWORDS:
        end = pos + len(keyword)
        if source[pos:end] == keyword and is_boundary(source, end):
            return ([(keyword, classification)], end)

    return None

def match_identifier(source, pos):
    # Identifiers must start with a letter
    if not source[pos].isalpha():
        return None

    end = pos + 1
    # Can contain letters, digits, or underscores
    while end < len(source) and (source[end].isalnum() or source[end] == "_"):
        end += 1

    lexeme = source[pos:end]
    return ([(lexeme, "Variable Identifier")], end)

# Tries every multi-word keyword at the current position
def match_multiword_keyword(source, pos):
    for keyword, classification in MULTI_WORD_KEYWORDS:
        end = pos + len(keyword) # The index right after where the keyword would end
        
        if source[pos:end] == keyword and is_boundary(source, end): # The text must match exactly AND end at a word boundary
            return ([(keyword, classification)], end) # Return one token for the whole keyword
   
    return None  # None of the keywords matched at this position

# VISIBLE operands are separated by a "+" symbol
def match_plus(source, pos):
    if source[pos] == "+":
        return ([("+", "Print Separator")], pos + 1)
    return None

# The list of matcher functions, in the order they should be tried
MATCHERS = [
    match_whitespace,           # skip spaces and tabs
    match_newline,              # newlines
    match_plus,                 # + between VISIBLE operands
    match_comment,              # comments (BTW, OBTW...TLDR)
    match_multiword_keyword,    # "I HAS A", "SUM OF", ... before shorter words
    match_string,               # "..." strings
    match_number,               # NUMBAR and NUMBR
    match_keyword,              # one-word keywords (HAI, ITZ, ...)
    match_troof,                # WIN, FAIL
    match_type,                 # NUMBR, YARN, ... as type literals
    match_identifier,           # anything else that looks like a name
]

# Main Function for the Lexer
def tokenize(source):
    tokens = [] # The list of (lexeme, classification, line) we will return
    pos = 0 # The index of the character we are looking at
    line = 1 # Line starts at 1 and goes up each time we pass a newline

    # Keep going until we have read the whole file
    while pos < len(source):
        matched = False # Flag variable for matching
        for matcher in MATCHERS:
            result = matcher(source, pos) # Try to match at the current position
            if result:
                matched = True # A matcher found something
                break

        # If nobody matched, this character is not valid LOLCODE
        if not matched:
            raise LexerError("Unrecognized character '" + source[pos] + "'", line)

        found, new_pos = result # Unpack what the matcher found
        if new_pos <= pos: # Safety check for infinite loops
            raise LexerError(matcher.__name__ + " did not move forward", line)

        # Add each found token to the list, tagged with the current line
        for lexeme, classification in found:
            tokens.append((lexeme, classification, line))

        line = line + source[pos:new_pos].count("\n") # Count the newlines consumed to update the line number
        pos = new_pos # Move to the next unread character

    return tokens
