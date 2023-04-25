import badger2040
import jpegdec
import os
import badger_os
import qrcode

PADDING = 8
WIDTH = badger2040.WIDTH
HEIGHT = badger2040.HEIGHT
QR_CODE_SIZE = 120
QR_CODE_LEFT = WIDTH - QR_CODE_SIZE
TEXT_CONTAINER_WIDTH = QR_CODE_LEFT - PADDING * 2

FONT_SIZE_FIRST_LINE = 4
FONT_SIZE_SECOND_LINE = 3

FOLDER = "/badgeio"
TOTAL_BADGES = 0
BADGES = []

# Load all available badges
try:
    BADGES = [f for f in os.listdir(FOLDER) if f.endswith(".txt")]
    TOTAL_BADGES = len(BADGES)
except OSError:
    print(f'Failed to get badges')
    pass

print(f'There are {TOTAL_BADGES} Badges available:')
for badge in BADGES:
    print(f'File: {badge}')


# ------------------------------
#      Utility functions
# ------------------------------


# Reduce the size of a string until it fits within a given width
def truncatestring(text, text_size, width):
    while True:
        length = display.measure_text(text, text_size)
        if length > 0 and length > width:
            text = text[:-1]
        else:
            text += ""
            return text


def measure_qr_code(size, qrCode):
    w, h = qrCode.get_size()
    module_size = int(size / w)
    return module_size * w, module_size


def draw_qr_code(ox, oy, size, qrCode):
    size, module_size = measure_qr_code(size, qrCode)
    display.set_pen(15)
    display.rectangle(ox, oy, size, size)
    display.set_pen(0)
    for x in range(size):
        for y in range(size):
            if qrCode.get_module(x, y):
                display.rectangle(ox + x * module_size, oy +
                                  y * module_size, module_size, module_size)

# Renders text and returns new top position


def renderText(top, text, scale):
    clippedText = truncatestring(text, scale, TEXT_CONTAINER_WIDTH)
    display.text(clippedText, PADDING, top, TEXT_CONTAINER_WIDTH, scale)

    return top + 8 * scale


def render(index, qrCode, jpeg):
    print(f'Rendering {index}')

    display.led(128)
    file = BADGES[index]

    contents = open("{}/{}".format(FOLDER, file), "r")
    lines = contents.read().strip().split("\n")

    # Clear the Display
    display.set_pen(15)
    display.clear()
    display.set_pen(0)

    # QR CODE
    url = lines[0]

    qrCode.set_text(url)

    qrCodeSize, _ = measure_qr_code(QR_CODE_SIZE, qrCode)

    QR_PADDING = int((HEIGHT / 2) - (qrCodeSize / 2))

    draw_qr_code(QR_CODE_LEFT + QR_PADDING, QR_PADDING, QR_CODE_SIZE, qrCode)

    # Text
    display.set_thickness(2)

    top = int(HEIGHT / 2) + PADDING

    # First line (bellow center of screen)
    if len(lines) > 1:
        top = renderText(top, lines[1], FONT_SIZE_FIRST_LINE)

    # Second line (smaller text at the bottom of screen)
    if len(lines) > 2:
        top = renderText(top, lines[2], FONT_SIZE_SECOND_LINE)

    # Image
    if len(lines) > 3:
        jpeg.open_file(lines[3])
        jpeg.decode(PADDING, PADDING)

    display.update()


# ------------------------------
#       Main program
# ------------------------------
display = badger2040.Badger2040()
qrCode = qrcode.QRCode()
jpeg = jpegdec.JPEG(display.display)

state = {
    "current": 0
}
badger_os.state_load("badgio", state)
rerender = True


while True:
    # Sometimes a button press or hold will keep the system
    # powered *through* HALT, so latch the power back on.
    display.keepalive()

    if TOTAL_BADGES > 1:
        if display.pressed(badger2040.BUTTON_UP):
            if state["current"] > 0:
                state["current"] -= 1
                rerender = True

        if display.pressed(badger2040.BUTTON_DOWN):
            if state["current"] < TOTAL_BADGES - 1:
                state["current"] += 1
                rerender = True

        if rerender:
            render(state["current"], qrCode, jpeg)
            badger_os.state_save("badgio", state)
            rerender = False

    # If on battery, halt the Badger to save power, it will wake up if any of the front buttons are pressed
    display.halt()
