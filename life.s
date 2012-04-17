        org $40

ptr:    dat 2
src:    dat 2
dest:   dat 2
row:    dat 1
col:    dat 1
gen:    dat 1

        org $800

        set rows = 24
        set cols = 40
        set cols2 = 80
        set cells = 960

        ;lda $c050
        ;lda $c057

        lda #>grid0
        sta ptr
        lda #<grid0
        sta ptr+1
        ldx #rows
irloop:
        lda #0
        ldy #cols-1
icloop:
        sta (ptr),y
        dey
        bpl icloop
        lda ptr
        clc
        adc #cols
        sta ptr
        lda ptr+1
        adc #0
        sta ptr+1
        dex
        bpl irloop

        lda #$ff
        sta grid0+501
        sta grid0+542
        sta grid0+580
        sta grid0+581
        sta grid0+582

        lda #$b0
        sta gen

        jsr refresh

pageloop:
        lda #>grid0
        sta src
        lda #<grid0
        sta src+1
        lda #>grid1
        sta dest
        lda #<grid1
        sta dest+1
        jsr iter

        lda #>grid1
        sta src
        lda #<grid1
        sta src+1
        jsr refresh_src

        lda #>grid1
        sta src
        lda #<grid1
        sta src+1
        lda #>grid0
        sta dest
        lda #<grid0
        sta dest+1
        jsr iter

        lda #>grid0
        sta src
        lda #<grid0
        sta src+1
        jsr refresh_src

        jmp pageloop

iter:
        lda #1
        sta row

        lda dest
        clc
        adc #cols+1
        sta dest
        lda dest+1
        adc #0
        sta dest+1
rowloop:
        lda #1
        sta col
colloop:
        ldx #0
        ldy #0
        lda (src),y
        beq n0
        inx
n0:
        iny
        lda (src),y
        beq n1
        inx
n1:
        iny
        lda (src),y
        beq n2
        inx
n2:
        ldy #cols
        lda (src),y
        beq n3
        inx
n3:
        iny
        iny
        lda (src),y
        beq n5
        inx
n5:
        ldy #cols2
        lda (src),y
        beq n6
        inx
n6:
        iny
        lda (src),y
        beq n7
        inx
n7:
        iny
        lda (src),y
        beq n8
        inx
n8:
        cpx #3
        beq cellon
        cpx #2
        bne celloff
        ldy #cols+1
        lda (src),y
        ldy #0
        sta (dest),y
        jmp cellnext
celloff:
        ldy #0
        lda (dest),y
        beq cellnext
        lda #0
        sta (dest),y
        jmp cellplot
cellon:
        ldy #0
        lda (dest),y
        bne cellnext
        lda #$ff
        sta (dest),y
cellplot:
        ldx col
        ldy row
        ;jsr plot
cellnext:
        inc src
        bne _1
        inc src+1
_1:
        inc dest
        bne _2
        inc dest+1
_2:
        inc col
        lda col
        cmp #cols-1
        bcc colloop

        lda src
        clc
        adc #2
        sta src
        lda src+1
        adc #0
        sta src+1

        lda dest
        clc
        adc #2
        sta dest
        lda dest+1
        adc #0
        sta dest+1

        inc row
        lda row
        cmp #rows-1
        bcs pagedone
        jmp rowloop

pagedone:
        rts

refresh:
        lda #>grid0
        sta src
        lda #<grid0
        sta src+1
refresh_src:
        lda #0
        sta row
rrloop:
        ldy #cols
        dey
        sty col
rcloop:
        ldy col
        lda (src),y
        ldx col
        ldy row
        jsr plot
        dec col
        bpl rcloop
        lda src
        clc
        adc #cols
        sta src
        lda src+1
        adc #0
        sta src+1
        inc row
        lda row
        cmp #rows
        bcc rrloop
        lda gen
        sta $7d0
        inc gen
        ;jsr waitkey
        rts

plot:
        pha
        tya
        asl
        tay
        lda scrtbl,y
        sta ptr
        iny
        lda scrtbl,y
        sta ptr+1
        txa
        tay
        pla
        beq plzero
        lda #$80
plzero:
        clc
        adc #$a0
        sta (ptr),y
        rts

        set kbd = $c000
        set kbdreset = $c010

waitkey:
        bit kbd
        bpl waitkey
        lda kbdreset
        rts

scrtbl: dw      $400,$480,$500,$580,$600,$680,$700,$780
        dw      $428,$4a8,$528,$5a8,$628,$6a8,$728,$7a8
        dw      $450,$4d0,$550,$5d0,$650,$6d0,$750,$7d0

        org $4000

grid0:  dat 960 ;cells
grid1:  dat 960 ;cells
