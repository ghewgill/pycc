import re
import sys

class Error(BaseException):
    pass

class Emitter:
    def __init__(self):
        self.pc = 0
    def emit(self, bytes):
        print(" ".join("{:02x}".format(x) for x in bytes))
        self.pc += len(bytes)
    def get_pc(self):
        return self.pc
    def set_org(self, pc):
        self.pc = pc

emitter = Emitter()
symbols = {}

def strip(s):
    return s.translate({ord(" "): None})

def parse(value):
    if value.startswith("$"):
        return int(value[1:], 16)
    else:
        return int(value)

def absolute_mode(operand):
    m = re.match(r"([$\w]+)$", strip(operand))
    if m is None:
        return None
    s = m.group(1)
    a = symbols.get(s)
    if a is None:
        a = parse(s)
    if 0 <= a <= 0xffff:
        return [a & 0xff, a >> 8]
    else:
        raise Error("Address value out of range: {}".format(a))

def absolute_x_mode(operand):
    m = re.match(r"([$\w]+),X$", strip(operand), re.IGNORECASE)
    if m is None:
        return None
    s = m.group(1)
    a = symbols.get(s)
    if a is None:
        a = parse(s)
    if 0 <= a <= 0xffff:
        return [a & 0xff, a >> 8]
    else:
        raise Error("Address value out of range: {}".format(a))

def absolute_y_mode(operand):
    m = re.match(r"([$\w]+),Y$", strip(operand), re.IGNORECASE)
    if m is None:
        return None
    s = m.group(1)
    a = symbols.get(s)
    if a is None:
        a = parse(s)
    if 0 <= a <= 0xffff:
        return [a & 0xff, a >> 8]
    else:
        raise Error("Address value out of range: {}".format(a))

def immediate_mode(operand):
    m = re.match(r"#([<>])?([$\w]+)$", strip(operand))
    if m is None:
        return None
    s = m.group(2)
    v = symbols.get(s)
    if v is None:
        v = parse(s)
    hilo = m.group(1)
    if hilo:
        if hilo == ">":
            v = v & 0xff
        elif hilo == "<":
            v = v >> 8
    if 0 <= v <= 0xff:
        return [v]
    else:
        raise Error("Immediate value out of range: {}".format(v))

def indirect_mode(operand):
    m = re.match(r"\(([$\w]+)\)$", strip(operand))
    if m is None:
        return None
    s = m.group(1)
    a = symbols.get(s)
    if a is None:
        a = parse(s)
    if 0 <= a <= 0xffff:
        return [a & 0xff, a >> 8]
    else:
        raise Error("Address value out of range: {}".format(a))

def indirect_x_mode(operand):
    m = re.match(r"\(([$\w]+),X\)$", strip(operand), re.IGNORECASE)
    if m is None:
        return None
    s = m.group(1)
    a = symbols.get(s)
    if a is None:
        a = parse(s)
    if 0 <= a <= 0xff:
        return [a]
    else:
        raise Error("Address out of range: {}".format(a))

def indirect_y_mode(operand):
    m = re.match(r"\(([$\w]+)\),Y$", strip(operand), re.IGNORECASE)
    if m is None:
        return None
    s = m.group(1)
    a = symbols.get(s)
    if a is None:
        a = parse(s)
    if 0 <= a <= 0xff:
        return [a]
    else:
        raise Error("Address out of range: {}".format(a))

def relative_mode(operand):
    m = re.match(r"([$\w]+)$", strip(operand))
    if m is None:
        return None
    s = m.group(1)
    a = symbols.get(s)
    if a is None:
        a = parse(s)
    if 0 <= a <= 0xffff:
        r = a - (emitter.get_pc() + 2)
        if -0x80 <= r <= 0x7f:
            if r < 0:
                r += 0x100
            return [r]
        else:
            raise Error("Address value too far: {}".format(a))
    else:
        raise Error("Address value out of range: {}".format(a))

def zero_page_mode(operand):
    m = re.match(r"([$\w]+)$", strip(operand))
    if m is None:
        return None
    s = m.group(1)
    a = symbols.get(s)
    if a is None:
        a = parse(s)
    if 0 <= a <= 0xff:
        return [a]
    else:
        return None

def zero_page_x_mode(operand):
    m = re.match(r"([$\w]+)$", strip(operand), re.IGNORECASE)
    if m is None:
        return None
    s = m.group(1)
    a = symbols.get(s)
    if a is None:
        a = parse(s)
    if 0 <= a <= 0xff:
        return [a]
    else:
        return None

def zero_page_y_mode(operand):
    m = re.match(r"([$\w]+)$", strip(operand), re.IGNORECASE)
    if m is None:
        return None
    s = m.group(1)
    a = symbols.get(s)
    if a is None:
        a = parse(s)
    if 0 <= a <= 0xff:
        return [a]
    else:
        return None

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

def op_DW(operand):
    emitter.set_org(emitter.get_pc() + parse(operand))

def op_ORG(operand):
    emitter.set_org(parse(operand))

def opcode(mnemonic, operand):
    modes = Opcodes.get(mnemonic.upper())
    if modes is None:
        return False
    for op, amode in modes:
        if amode is None:
            if operand:
                return False
            bytes = []
            break
        bytes = amode(operand)
        if bytes is not None:
            break
    else:
        return False
    emitter.emit([op] + bytes)
    return True

def main():
    f = open(sys.argv[1])
    for s in f:
        i = s.find(";")
        if i >= 0:
            s = s[:i]
        m = re.search(r"((\w+)\s*:)?\s*((\w+)(\s+(.+))?)?\s*$", s)
        #               12             34    5   6
        if m is None:
            raise Error("Syntax error")
        label = m.group(2)
        mnemonic = m.group(4)
        operand = m.group(6)
        if label is not None:
            if label in symbols:
                raise Error("Duplicate symbol: {}".format(label))
            symbols[label] = emitter.get_pc()
        if mnemonic is None:
            continue
        f = globals().get("op_" + mnemonic.upper())
        if f is not None:
            f(operand)
        else:
            if not opcode(mnemonic, operand):
                print(s)
                raise Error("Unknown opcode: {}".format(mnemonic))

if __name__ == "__main__":
    main()
