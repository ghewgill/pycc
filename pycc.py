class SyntaxError(BaseException):
    pass

Keywords = {
    "char",
    "int",
}

class TokenKind:
    def __init__(self, name):
        self.name = name

IDENTIFIER = TokenKind("IDENTIFIER")
PUNCTUATION = TokenKind("PUNCTUATION")
STRING = TokenKind("STRING")

class Token:
    def __init__(self, type, value, pos):
        self.type = type
        self.value = value
        self.pos = pos
    def __repr__(self):
        return "<Token {} {} {}:{}>".format(self.type.name, self.value, self.pos[0], self.pos[1])

def lex(source):
    line = 1
    linestart = 0
    i = 0

    def lex_number():
        nonlocal i
        j = 1
        while source[i + j].isdigit():
            j += 1
        r = Token(NUMBER, source[i:i+j], (line, i - linestart + 1))
        i += j
        return r

    def lex_string():
        nonlocal i
        s = ""
        j = 1
        while source[i + j] != '"':
            if source[i + j] == "\\":
                s += source[i + j + 1]
            else:
                s += source[i + j]
            j += 1
        r = Token(STRING, s, (line, i - linestart + 1))
        i += j + 1
        return r

    def lex_ident():
        nonlocal i
        j = 1
        while source[i + j].isalnum():
            j += 1
        k = source[i:i+j]
        i += j
        if k in Keywords:
            return Token(IDENTIFIER, k, (line, i - linestart + 1))
        else:
            return Token(IDENTIFIER, k, (line, i - linestart + 1))

    while i < len(source):
        if source[i].isdigit():
            yield lex_number()
        elif source[i] == '"':
            yield lex_string()
        elif source[i] == "'":
            yield lex_char()
        elif source[i].isalpha():
            yield lex_ident()
        elif source[i].isspace():
            if source[i] == "\n":
                line += 1
                linestart = i + 1
            i += 1
        else:
            yield Token(PUNCTUATION, source[i], (line, i - linestart + 1))
            i += 1

def parse(tokens):
    # based on http://lists.canonical.org/pipermail/kragen-hacks/1999-October/000201.html

    def parse_assignment_expression(t):
        

    def parse_expression(t):
        while True:
            t = parse_assignment_expression(t)
            if t.value != ",":
                break
            t = next(tokens)

    def parse_statement(t):
        if t == "if":
            t = next(tokens)
            if t.value != "(":
                raise SyntaxError("Open parenthesis expected")
            t = parse_expression()
            if t != ")":
                raise SyntaxError("Close parenthesis expected")
            return parse_statement()
        else:
            return parse_expression(t)

    def parse_block():
        t = next(tokens)
        while t.value != "}":
            t = parse_statement(t)

    def parse_function(returntype, name):
        t = next(tokens)
        while t.value != ")":
            if t.type is not IDENTIFIER:
                raise SyntaxError("Type identifier expected")
            typename = t.value
            t = next(tokens)
            if t.type is not IDENTIFIER:
                raise SyntaxError("Identifier expected")
            name = t.value
            t = next(tokens)
            if t.value == ",":
                t = next(tokens)
        t = next(tokens)
        if t.value != "{":
            raise SyntaxError("Opening brace expected")
        parse_block()

    def parse_declaration():
        t = next(tokens)
        if t.type is not IDENTIFIER:
            raise SyntaxError("Type identifier expected")
        typename = t.value
        t = next(tokens)
        if t.type is not IDENTIFIER:
            raise SyntaxError("Identifier expected")
        name = t.value
        t = next(tokens)
        if t.type is PUNCTUATION and t.value == ";":
            return parse_global()
        elif t.type is PUNCTUATION and t.value == "(":
            return parse_function(typename, name)
        else:
            raise SyntaxError("Declaration expected")

    def parse_translation_unit():
        r = []
        try:
            while True:
                r.append(parse_declaration())
        except StopIteration:
            pass
        return r

    try:
        return parse_translation_unit()
    except SyntaxError as e:
        print("Syntax error: {}".format(e))

def main():
    source = open("hello.c").read()
    tokens = list(lex(source))
    print(tokens)
    tree = parse(iter(tokens))

if __name__ == "__main__":
    main()
