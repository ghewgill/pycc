import re
import sys

class Error(BaseException):
    pass

class Instruction:
    def __init__(self, size, opcode, operand):
        self._size = size
        self.opcode = opcode
        self.operand = operand
    def bytes(self):
        return [self.opcode] + self.operand()
    def size(self):
        return self._size

class Data:
    def __init__(self, data):
        self.data = data
    def bytes(self):
        return self.data
    def size(self):
        return len(self.data)

class Emitter:
    def __init__(self):
        self.pc = 0
        self.ranges = []
    def dump(self):
        for r in self.ranges:
            pc = r[0]
            for ins in r[1]:
                print("{:x}- {}".format(pc, " ".join("{:02x}".format(x) for x in ins.bytes())))
                pc += ins.size()
    def emit(self, ins):
        self.ranges[-1][1].append(ins)
        self.pc += ins.size()
    def get_pc(self):
        return self.pc
    def set_org(self, pc):
        self.pc = pc
        self.ranges.append((pc, []))

emitter = Emitter()
symbols = {}

def find(f, seq):
    """Return first item in sequence where f(item) == True."""
    for item in seq:
        if f(item): 
            return item

def strip(s):
    return s.translate({ord(" "): None})

def parse(value):
    if value.startswith("$"):
        return int(value[1:], 16)
    elif value[0].isdigit():
        return int(value)
    else:
        return None

class TokenKind:
    pass

WORD = TokenKind()
STRING = TokenKind()

def tokenise(s):
    i = 0
    while i < len(s):
        if s[i] == '"':
            m = re.match(r'"((\\.|[^"])*)"', s[i:])
            if m is not None:
                yield (STRING, m.group(1))
                i += m.end(0)
            else:
                raise Error("Unterminated string")
        elif not s[i].isspace():
            m = re.match(r"\S+", s[i:])
            yield (WORD, m.group(0))
            i += m.end(0)
        else:
            i += 1

def evaluate(s):
    offset = 0
    m = re.search(r"\+\s*(\d+)", s)
    if m is not None:
        offset = int(m.group(1))
        s = s[:m.start(0)]
    val = parse(s)
    if val is not None:
        return val + offset
    val = symbols.get(s)
    if val is not None:
        return val + offset
    raise Error("Unknown symbol: {}".format(s))

def operand_byte(x):
    if 0 <= x <= 0xff:
        return [x]
    else:
        raise Error("Immediate value out of range: {}".format(x))

def operand_sbyte(x):
    if -0x80 <= x <= 0x7f:
        if x < 0:
            x += 0x100
        return [x]
    else:
        raise Error("Address value too far: {}".format(x))

def operand_word(x):
    if 0 <= x <= 0xffff:
        return [x & 0xff, x >> 8]
    else:
        raise Error("Address value out of range: {}".format(x))

def absolute_mode(operand):
    return 3, lambda: operand_word(evaluate(operand))

def absolute_x_mode(operand):
    m = re.match(r"(.+),X$", strip(operand), re.IGNORECASE)
    if m is None:
        return None
    s = m.group(1)
    return 3, lambda: operand_word(evaluate(s))

def absolute_y_mode(operand):
    m = re.match(r"(.+),Y$", strip(operand), re.IGNORECASE)
    if m is None:
        return None
    s = m.group(1)
    return 3, lambda: operand_word(evaluate(s))

def immediate_mode(operand):
    m = re.match(r"#(([<>])?(.+))$", strip(operand))
    if m is None:
        return None
    s = m.group(3)
    hilo = m.group(2)
    if hilo:
        if hilo == ">":
            return 2, lambda: operand_byte(evaluate(s) & 0xff)
        elif hilo == "<":
            return 2, lambda: operand_byte(evaluate(s) >> 8)
    else:
        return 2, lambda: operand_byte(evaluate(s))

def indirect_mode(operand):
    m = re.match(r"\((.+)\)$", strip(operand))
    if m is None:
        return None
    s = m.group(1)
    return 3, lambda: operand_word(evaluate(s))

def indirect_x_mode(operand):
    m = re.match(r"\((.+),X\)$", strip(operand), re.IGNORECASE)
    if m is None:
        return None
    s = m.group(1)
    return 2, lambda: operand_byte(evaluate(s))

def indirect_y_mode(operand):
    m = re.match(r"\((.+)\),Y$", strip(operand), re.IGNORECASE)
    if m is None:
        return None
    s = m.group(1)
    return 2, lambda: operand_byte(evaluate(s))

def relative_mode(operand):
    m = re.match(r"(.+)$", strip(operand))
    if m is None:
        return None
    s = m.group(1)
    pc = emitter.get_pc()
    return 2, lambda: operand_sbyte(evaluate(s) - (pc + 2))

def zero_page_mode(operand):
    m = re.match(r"(.+)$", strip(operand))
    if m is None:
        return None
    s = m.group(1)
    return 2, lambda: operand_byte(evaluate(s))

def zero_page_x_mode(operand):
    m = re.match(r"(.+),X$", strip(operand), re.IGNORECASE)
    if m is None:
        return None
    s = m.group(1)
    return 2, lambda: operand_byte(evaluate(s))

def zero_page_y_mode(operand):
    m = re.match(r"(.+),Y$", strip(operand), re.IGNORECASE)
    if m is None:
        return None
    s = m.group(1)
    return 2, lambda: operand_byte(evaluate(s))

OpcodeParseOrder = (
    indirect_x_mode,    # (zzz,X)
    indirect_y_mode,    # (zzz),Y
    zero_page_x_mode,   # zzz,X
    zero_page_y_mode,   # zzz,Y
    absolute_x_mode,    # zzz,X
    absolute_y_mode,    # zzz,Y
    immediate_mode,     # #zzz
    indirect_mode,      # (zzz)
    zero_page_mode,     # zzz
    absolute_mode,      # zzz
    relative_mode,      # zzz
    None
)

Opcodes = {
    "ADC": [(0x61, indirect_x_mode),
            (0x65, zero_page_mode),
            (0x69, immediate_mode),
            (0x6D, absolute_mode),
            (0x71, indirect_y_mode),
            (0x75, zero_page_x_mode),
            (0x79, absolute_y_mode),
            (0x7D, absolute_x_mode)],
    "AND": [(0x21, indirect_x_mode),
            (0x25, zero_page_mode),
            (0x29, immediate_mode),
            (0x2D, absolute_mode),
            (0x31, indirect_y_mode),
            (0x35, zero_page_x_mode),
            (0x39, absolute_y_mode),
            (0x3D, absolute_x_mode)],
    "ASL": [(0x06, zero_page_mode),
            (0x0E, absolute_mode),
            (0x16, zero_page_x_mode),
            (0x1E, absolute_x_mode),
            (0x0A, None)],
    "BCC": [(0x90, relative_mode)],
    "BCS": [(0xB0, relative_mode)],
    "BEQ": [(0xF0, relative_mode)],
    "BIT": [(0x24, zero_page_mode),
            (0x2C, absolute_mode)],
    "BMI": [(0x30, relative_mode)],
    "BNE": [(0xD0, relative_mode)],
    "BPL": [(0x10, relative_mode)],
    "BRK": [(0x00, None)],
    "BVC": [(0x50, relative_mode)],
    "BVS": [(0x70, relative_mode)],
    "CLC": [(0x18, None)],
    "CLD": [(0xD8, None)],
    "CLI": [(0x58, None)],
    "CLV": [(0xB8, None)],
    "CMP": [(0xC1, indirect_x_mode),
            (0xC5, zero_page_mode),
            (0xC9, immediate_mode),
            (0xCD, absolute_mode),
            (0xD1, indirect_y_mode),
            (0xD5, zero_page_x_mode),
            (0xD9, absolute_y_mode),
            (0xDD, absolute_x_mode)],
    "CPX": [(0xE0, immediate_mode),
            (0xE4, zero_page_mode),
            (0xEC, absolute_mode)],
    "CPY": [(0xC0, immediate_mode),
            (0xC4, zero_page_mode),
            (0xCC, absolute_mode)],
    "DEC": [(0xC6, zero_page_mode),
            (0xCE, absolute_mode),
            (0xD6, zero_page_x_mode),
            (0xDE, absolute_x_mode)],
    "DEX": [(0xCA, None)],
    "DEY": [(0x88, None)],
    "EOR": [(0x41, indirect_x_mode),
            (0x45, zero_page_mode),
            (0x49, immediate_mode),
            (0x4D, absolute_mode),
            (0x51, indirect_y_mode),
            (0x55, zero_page_x_mode),
            (0x59, absolute_y_mode),
            (0x5D, absolute_x_mode)],
    "INC": [(0xE6, zero_page_mode),
            (0xEE, absolute_mode),
            (0xF6, zero_page_x_mode),
            (0xFE, absolute_x_mode)],
    "INX": [(0xE8, None)],
    "INY": [(0xC8, None)],
    "JMP": [(0x4C, absolute_mode),
            (0x6C, indirect_mode)],
    "JSR": [(0x20, absolute_mode)],
    "LDA": [(0xA1, indirect_x_mode),
            (0xA5, zero_page_mode),
            (0xA9, immediate_mode),
            (0xAD, absolute_mode),
            (0xB1, indirect_y_mode),
            (0xB5, zero_page_x_mode),
            (0xB9, absolute_y_mode),
            (0xBD, absolute_x_mode)],
    "LDX": [(0xA2, immediate_mode),
            (0xA6, zero_page_mode),
            (0xAE, absolute_mode),
            (0xB6, zero_page_y_mode),
            (0xBE, absolute_y_mode)],
    "LDY": [(0xA0, immediate_mode),
            (0xA4, zero_page_mode),
            (0xAC, absolute_mode),
            (0xB4, zero_page_x_mode),
            (0xBC, absolute_x_mode)],
    "LSR": [(0x46, zero_page_mode),
            (0x4E, absolute_mode),
            (0x56, zero_page_x_mode),
            (0x5E, absolute_x_mode),
            (0x4A, None)],
    "NOP": [(0xEA, None)],
    "ORA": [(0x01, indirect_x_mode),
            (0x05, zero_page_mode),
            (0x09, immediate_mode),
            (0x0D, absolute_mode),
            (0x11, indirect_y_mode),
            (0x15, zero_page_x_mode),
            (0x19, absolute_y_mode),
            (0x1D, absolute_x_mode)],
    "PHA": [(0x48, None)],
    "PHP": [(0x08, None)],
    "PLA": [(0x68, None)],
    "PLP": [(0x28, None)],
    "ROL": [(0x26, zero_page_mode),
            (0x2E, absolute_mode),
            (0x36, zero_page_x_mode),
            (0x3E, absolute_x_mode),
            (0x2A, None)],
    "ROR": [(0x66, zero_page_mode),
            (0x6E, absolute_mode),
            (0x76, zero_page_x_mode),
            (0x7E, absolute_x_mode),
            (0x6A, None)],
    "RTI": [(0x40, None)],
    "RTS": [(0x60, None)],
    "SBC": [(0xE1, indirect_x_mode),
            (0xE5, zero_page_mode),
            (0xE9, immediate_mode),
            (0xED, absolute_mode),
            (0xF1, indirect_y_mode),
            (0xF5, zero_page_x_mode),
            (0xF9, absolute_y_mode),
            (0xFD, absolute_x_mode)],
    "SEC": [(0x38, None)],
    "SED": [(0xF8, None)],
    "SEI": [(0x78, None)],
    "STA": [(0x81, indirect_x_mode),
            (0x85, zero_page_mode),
            (0x8D, absolute_mode),
            (0x91, indirect_y_mode),
            (0x95, zero_page_x_mode),
            (0x99, absolute_y_mode),
            (0x9D, absolute_x_mode)],
    "STX": [(0x86, zero_page_mode),
            (0x8E, absolute_mode),
            (0x96, zero_page_y_mode)],
    "STY": [(0x84, zero_page_mode),
            (0x8C, absolute_mode),
            (0x94, zero_page_x_mode)],
    "TAX": [(0xAA, None)],
    "TAY": [(0xA8, None)],
    "TSX": [(0xBA, None)],
    "TXA": [(0x8A, None)],
    "TXS": [(0x9A, None)],
    "TYA": [(0x98, None)],
}

def op_DB(operand):
    return Data(list(map(ord, operand)))

def op_DW(operand):
    emitter.set_org(emitter.get_pc() + parse(operand))
    return None

def op_ORG(operand):
    emitter.set_org(parse(operand))
    return None

def opcode(mnemonic, operand):
    modes = Opcodes.get(mnemonic.upper())
    if modes is None:
        return None
    size = 1
    opfunc = None
    for parser in OpcodeParseOrder:
        for op, amode in modes:
            if amode is not parser:
                continue
            if amode is None:
                if operand:
                    return None
                return Instruction(size, op, lambda: [])
            r = amode(operand)
            if r is not None:
                size, opfunc = r
                return Instruction(size, op, opfunc)
    return None

def assemble(infile, outfile):
    with open(infile) as inf:
        for s in inf:
            a = list(tokenise(s))
            comment = find(lambda x: x[1][0] is WORD and x[1][1].startswith(";"), enumerate(a))
            if comment:
                a = a[:comment[0]]
            it = iter(a)
            tok = next(it, None)
            if tok is None:
                continue
            if tok[0] is WORD and tok[1].endswith(":"):
                label = tok[1][:-1]
                if label in symbols:
                    raise Error("Duplicate symbol: {}".format(label))
                symbols[label] = emitter.get_pc()
                tok = next(it, None)
            if tok is None:
                continue
            if tok[0] is not WORD:
                raise Error("Mnemonic expected: {}".format(tok))
            mnemonic = tok[1]
            operand = list(it)
            print(operand)
            it = iter(operand)
            tok = next(it, None)
            operand = ""
            while tok:
                operand += tok[1]
                tok = next(it, None)
            if tok is not None:
                raise Error("Extra input on line: {}".format(s))
            op = globals().get("op_" + mnemonic.upper())
            if op is not None:
                ins = op(operand)
                if ins is not None:
                    emitter.emit(ins)
            else:
                ins = opcode(mnemonic, operand)
                if ins is None:
                    print(s)
                    raise Error("Unknown opcode: {}".format(mnemonic))
                emitter.emit(ins)
        emitter.dump()

def main():
    fn = sys.argv[1]
    assemble(fn, fn[:-2] + ".o")

if __name__ == "__main__":
    main()
