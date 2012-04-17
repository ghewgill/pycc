        org $20     ; globals

src:    dat 2
dest:   dat 2

        org $800

        lda #>hello
        sta src
        lda #<hello
        sta src+1
        lda #$00
        sta dest
        lda #$04
        sta dest+1
        ldy #$00
loop:
        lda (src),y
        beq out
        sta (dest),y
        iny
        jmp loop
out:
        jmp basic

hello:
        ;db  "HELLO",0
        db  $c8,$c5,$cc,$cc,$cf,0

        org $e000
basic:
