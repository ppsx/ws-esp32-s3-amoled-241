import rm690b0

display = rm690b0.RM690B0()
display.init_display()
display.swap_buffers()  # enable double-buffering
# -----
input("Press Enter to display 8x8 font...")
display.fill_color(rm690b0.BLACK)
display.set_font(rm690b0.FONT_8x8)  # 8x8 monospace font
display.text(10, 10, "Font Test: 8x8", rm690b0.WHITE)
display.text(10, 30, "RM690B0 native text", rm690b0.CYAN)
display.text(10, 40, "WHITE on RED", rm690b0.WHITE, rm690b0.RED)
display.text(10, 50, "GREEN on BLACK", rm690b0.GREEN)
display.text(10, 60, "ABCDEFGHIJKLMNOPQRSTUVWXYZ", rm690b0.YELLOW)
display.text(10, 70, "0123456789!@#$%^&*()", rm690b0.MAGENTA)
display.swap_buffers()
# -----
input("Press Enter to display 16x16 font...")
display.fill_color(rm690b0.BLACK)
display.set_font(rm690b0.FONT_16x16)  # 16x16 monospace font (Liberation Sans)
display.text(10, 10, "Font Test: 16x16", rm690b0.WHITE)
display.text(10, 30, "Liberation Sans!", rm690b0.CYAN)
display.text(10, 50, "ABCDEFGHIJKLM", rm690b0.YELLOW)
display.text(10, 70, "0123456789", rm690b0.GREEN)
display.text(10, 90, "Bigger & Better!", rm690b0.MAGENTA)
display.swap_buffers()
# -----
input("Press Enter to display weird things...")
display.rect(0, 0, 600, 450, rm690b0.WHITE)
display.line(0, 0, 600, 450, rm690b0.RED)
display.line(600, 0, 0, 450, rm690b0.GREEN)
display.line(0, 225, 600, 225, rm690b0.YELLOW)
display.line(150, 0, 150, 450, rm690b0.MAGENTA)
display.vline(300, 0, 450, rm690b0.CYAN)
display.hline(0, 300, 600, rm690b0.DARK_GRAY)
display.line(150, 0, 600, 450, rm690b0.SKY_BLUE)
display.circle(150, 225, 150, rm690b0.VIOLET)
display.fill_circle(500, 100, 50, rm690b0.BROWN)
display.fill_rect(400, 350, 100, 50, rm690b0.DARK_BROWN)
display.fill_rect(350, 50, 50, 100, rm690b0.BLUE)
display.swap_buffers()
# -----
input("Press Enter to check filling the screen...")
display.fill_color(rm690b0.WHITE)
display.swap_buffers()
input("Press Enter...")
display.fill_color(rm690b0.BLACK)
display.swap_buffers()
input("Press Enter...")
display.fill_rect(0, 0, 600, 450, rm690b0.WHITE)
display.swap_buffers()
# -----
input("Press Enter to check rotation...")
display.fill_color(rm690b0.BLACK)
display.fill_rect(10, 10, 10, 10, rm690b0.WHITE)
display.rotation = 90
display.fill_rect(10, 10, 10, 10, rm690b0.GREEN)
display.rotation = 180
display.fill_rect(10, 10, 10, 10, rm690b0.RED)
display.rotation = 270
display.fill_rect(10, 10, 10, 10, rm690b0.YELLOW)
display.rotation = 0
display.swap_buffers()
# -----
input("Press Enter to check circle...")
display.fill_color(rm690b0.WHITE)
display.fill_circle(300, 225, 200, rm690b0.BLACK)
display.circle(300, 225, 220, rm690b0.BLACK)
display.swap_buffers()
# -----
input("Press Enter to check patterns...")


def w():
    display.fill_color(rm690b0.WHITE)


def b():
    display.fill_color(rm690b0.BLACK)


def dv(d, c):
    w, h = display.width, display.height
    x = 0
    while x < w:
        display.vline(x, 0, h, c)
        x += d
    display.swap_buffers()


def dh(d, c):
    w, h = display.width, display.height
    for y in range(0, h, d):
        display.hline(0, y, w, c)
    display.swap_buffers()


input("Press Enter to check vertical lines...")
for a in range(1, 11):
    b()
    dv(a, rm690b0.GREEN)
    input("Press Enter...")
input("Press Enter to check horizontal lines...")
for a in range(1, 11):
    w()
    dh(a, rm690b0.RED)
    input("Press Enter...")
# -----
input("Press Enter to close...")
display.deinit()
