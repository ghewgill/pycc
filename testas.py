import unittest

import pyas

def asm(s):
    return pyas.assemble_instruction(s).bytes()

class TestCharset(unittest.TestCase):
    def test_upper(self):
        self.assertEqual(pyas.apple_charset("ABC!"), [0xC1, 0xC2, 0xC3, 0xE1])
    def test_lower(self):
        with self.assertRaises(pyas.Error):
            pyas.apple_charset("abc")

class TestParser(unittest.TestCase):
    def test_decimal(self):
        self.assertEqual(pyas.parse("55"), 55)
    def test_hex(self):
        self.assertEqual(pyas.parse("$55"), 0x55)

class TestTokeinse(unittest.TestCase):
    def test_tokens(self):
        self.assertEqual(list(pyas.tokenise("lda $0")), [(pyas.WORD, "lda"), (pyas.WORD, "$0")])

class TestInstruction(unittest.TestCase):
    def test_absolute_mode(self):
        self.assertEqual(asm("lda $aa55"), [0xad, 0x55, 0xaa])
    def test_absolute_x_mode(self):
        self.assertEqual(asm("lda $aa55,x"), [0xbd, 0x55, 0xaa])
    def test_absolute_y_mode(self):
        self.assertEqual(asm("lda $aa55,y"), [0xb9, 0x55, 0xaa])
    def test_immediate_mode(self):
        self.assertEqual(asm("lda #$a5"), [0xa9, 0xa5])
    def test_indirect_mode(self):
        self.assertEqual(asm("jmp ($aa55)"), [0x6c, 0x55, 0xaa])
    def test_indirect_x_mode(self):
        self.assertEqual(asm("lda ($a5,x)"), [0xa1, 0xa5])
    def test_indirect_y_mode(self):
        self.assertEqual(asm("lda ($a5),y"), [0xb1, 0xa5])
    def test_relative_mode(self):
        self.assertEqual(asm("beq $5a"), [0xf0, 0x5a-2])
    def test_zero_page_mode(self):
        self.assertEqual(asm("lda $a5"), [0xa5, 0xa5])
    def test_zero_page_x_mode(self):
        self.assertEqual(asm("lda $a5,x"), [0xb5, 0xa5])
    def test_zero_page_y_mode(self):
        self.assertEqual(asm("ldx $a5,y"), [0xb6, 0xa5])
    def test_none(self):
        self.assertEqual(asm("nop"), [0xea])

class TestSymbols(unittest.TestCase):
    def test_add(self):
        pyas.assemble_instruction("org $800")
        pyas.assemble_instruction("foo: dat 2")
        pyas.assemble_instruction("bar: dat 2")
        self.assertEqual(pyas.symbols.get("foo"), 0x800)
        self.assertEqual(pyas.symbols.get("bar"), 0x802)

class TestSet(unittest.TestCase):
    def test_set(self):
        pyas.assemble_instruction("set five = 5")
        self.assertEqual(pyas.symbols.get("five"), 5)

class TestData(unittest.TestCase):
    def test_bytes(self):
        self.assertEqual(asm("db 1,2,3"), [1, 2, 3])
        #self.assertEqual(asm("db \"ABC\""), [0xC1, 0xC2, 0xC3])
        self.assertEqual(asm("dw 1,2,3,4000"), [1, 0, 2, 0, 3, 0, 0xa0, 0x0f])

if __name__ == "__main__":
    unittest.main()
