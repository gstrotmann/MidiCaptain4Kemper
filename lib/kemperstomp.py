# v 1.3
# Changes
# use black text color for effect name
# changing dark green color
#
# v 1.2
# Changes
# Detect Rig changes via rig date
# change color for Compressor/Noise Gate to turquoise

# Bopard Infos
# Raspberry Pi Pico with rp2040
#
# GP0
# GP1  - FootSwitch 0
# GP2
# GP3
# GP4 bat_chg_led
# GP5
# GP6 charging
# GP7  - NeoPixel Pin
# GP8 asyncio PWMOut GP8 frequency
# GP9  - FootSwitch 3
# GP10 - FootSwitch 4
# GP11 - FootSwitch 5
# GP12 tft_dc (SPI1 RX)
# GP13 - SPI Display ft_cs (Chip Select)
# GP14 spi_clk  (SPI1SCK)
# GP15 spi_mosi (SPI1 TX)
# GP16 Midi GP16GP17 baudrate
# GP17 Midi GP16GP17 baudrate
# GP18
# GP19
# GP20
# GP21
# GP22
# GP23
# GP24 - FootSwitch 2
# GP25 - FootSwitch 1
# GP26
# GP27
# GP28


import board
import digitalio
import busio
import displayio
from adafruit_display_text import label, wrap_text_to_pixels
from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes.rect import Rect
import usb_midi
import adafruit_midi  # MIDI protocol encoder/decoder library
from adafruit_midi.control_change import ControlChange
from adafruit_midi.system_exclusive import SystemExclusive
from adafruit_midi.midi_message import MIDIUnknownEvent

try:
    from fourwire import FourWire
except ImportError:
    from displayio import FourWire

from adafruit_st7789 import ST7789
import neopixel


# use neopixel for first status messages while initial sequence of this script
# neopixel documentation
# https://docs.circuitpython.org/projects/neopixel/en/latest/
# https://learn.adafruit.com/adafruit-neopixel-uberguide/python-circuitpython
pixel_pin = board.GP7
LED_amount = 18
LED = neopixel.NeoPixel(pixel_pin, LED_amount, brightness=0.3)

LED.fill(0xff0000)  # set boot status: red

# Set Constants and initial values
# Kemper colors
darkgreen = (73, 110, 41)
green = (0, 255, 0)
white = (255, 255, 255)
red = (255, 0, 0)
yellow = (255, 255, 0)
purple = (30, 0, 20)
orange = (255, 165, 0)
blue = (0, 0, 255)
turquoise = (64, 242, 208)
gray = (190, 190, 190)

# set Bitmap Palette with Kemper Colors
palette = displayio.Palette(10)
palette[0] = white
palette[1] = yellow
palette[2] = orange
palette[3] = red
palette[4] = purple
palette[5] = turquoise
palette[6] = blue
palette[7] = green
palette[8] = darkgreen
palette[9] = gray

# palette[10] = 0x2F4538  # Kemper cover green


# Release any resources currently in use for the displays
displayio.release_displays()

disp_width = 240
disp_height = 240
CENTER_Y = int(disp_width/2)
CENTER_X = int(disp_height/2)

tft_res = board.GP8
tft_cs = board.GP13
tft_dc = board.GP12
spi_mosi = board.GP15
spi_clk = board.GP14

spi = busio.SPI(spi_clk, MOSI=spi_mosi)
while not spi.try_lock():
    pass
spi.configure(baudrate=24000000)  # Configure SPI for 24MHz
spi.unlock()

display_bus = FourWire(
    spi, command=tft_dc, chip_select=tft_cs, reset=None)

display = ST7789(display_bus,
                 width=disp_width, height=disp_height,
                 rowstart=80, rotation=180)


# Make display context
splash = displayio.Group()
display.rootgroup = splash


font = bitmap_font.load_font("/fonts/PTSans-NarrowBold-40.pcf")
# font = bitmap_font.load_font("/fonts/PT40.pcf")
font_H20 = bitmap_font.load_font("/fonts/H20.pcf")
wrap_with = 220  # in pixel


LED.fill(0xffff00)  # set boot status yellow

# Draw Effect Module DLY
rect = Rect(1, 1, 120, 40, fill=palette[7], outline=0x0, stroke=1)
splash.append(rect)  # position splash[0] IMPORTANT!

text_group_DLY = displayio.Group(scale=1, x=1, y=1)
text_DLY = "Delay"
text_DLY_area = label.Label(font_H20, text=text_DLY, color=0x0, anchor_point=(0.5, 0.5), anchored_position=(60, 20))
text_group_DLY.append(text_DLY_area)  # Subgroup for text scaling

# Draw Effect Module REV
rect = Rect(120, 1, 120, 40, fill=palette[8], outline=0x0, stroke=1)
splash.append(rect)  # position splash[1] IMPORTANT!

text_group_REV = displayio.Group(scale=1, x=120, y=1)
text_REV = "Reverb"
text_REV_area = label.Label(font_H20, text=text_REV, color=0x0, anchor_point=(0.5, 0.5), anchored_position=(60, 20))
text_group_REV.append(text_REV_area)  # Subgroup for text scaling

# Draw Effect Module A
rect = Rect(1, 200, 120, 40, fill=palette[5], outline=0x0, stroke=1)
splash.append(rect)  # position splash[2] IMPORTANT!

text_group_A = displayio.Group(scale=1, x=1, y=200)
text_A = "Module A"
text_A_area = label.Label(font_H20, text=text_A, color=0x0, anchor_point=(0.5, 0.5), anchored_position=(60, 20))
text_group_A.append(text_A_area)  # Subgroup for text scaling

# Draw Effect Module A
rect = Rect(120, 200, 120, 40, fill=palette[6], outline=0x0, stroke=1)
splash.append(rect)  # position splash[3] IMPORTANT!

text_group_B = displayio.Group(scale=1, x=120, y=200)
text_B = "Module B"
text_B_area = label.Label(font_H20, text=text_B, color=0x0, anchor_point=(0.5, 0.5), anchored_position=(60, 20))
text_group_B.append(text_B_area)  # Subgroup for text scaling

# show Rig Name
text_group_rig = displayio.Group(scale=1)
text1 = "Kemper\nEffects Slot Modus"
text_area_rig = label.Label(font, text="\n".join(wrap_text_to_pixels(text1, wrap_with, font)).center(14), color=0xFFFFFF, line_spacing=0.8)
text_area_rig.anchor_point = (0.5, 0.5)
text_area_rig.anchored_position = (CENTER_X, CENTER_Y)
text_group_rig.append(text_area_rig)  # Subgroup for text scaling

# add  text groups
splash.append(text_group_rig)
splash.append(text_group_DLY)
splash.append(text_group_REV)
splash.append(text_group_A)
splash.append(text_group_B)

# activate Display
display.show(splash)

# pick your USB MIDI out channel here, 1-16
MIDI_USB_channel = 1

midi_usb = adafruit_midi.MIDI(midi_out=usb_midi.ports[1],
                              out_channel=MIDI_USB_channel - 1,
                              midi_in=usb_midi.ports[0],
                              in_buf_size=60, debug=False)

# Define Footswitch Class
class FootSwitch:
    def __init__(self, pin, color):
        self.switch = digitalio.DigitalInOut(pin)          # hardware assingment
        self.switch.direction = digitalio.Direction.INPUT
        self.switch.pull = digitalio.Pull.UP
        self.color = [color]                               # color of assingment
    state = "off"                                          # initial state
    effecttype = -1
    bitmap_palette_index = 0

    def setcolor(self):
        # print('new color for ' + str(self.effecttype))

        if (0 < self.effecttype and self.effecttype < 14):
            # Wah -> orange
            self.color = [orange]
            self.bitmap_palette_index = 2
        elif (16 < self.effecttype and self.effecttype < 45):
            # Booster -> red
            self.color = [red]
            self.bitmap_palette_index = 3
        elif (47 < self.effecttype and self.effecttype < 60):
            # Compressor -> blue
            self.color = [turquoise]
            self.bitmap_palette_index = 5
        elif (60 < self.effecttype and self.effecttype < 64):
            # Space -> green
            self.color = [green]
            self.bitmap_palette_index = 8
        elif (64 < self.effecttype and self.effecttype < 80):
            # Chorus -> blue
            self.color = [blue]
            self.bitmap_palette_index = 6
        elif (80 < self.effecttype and self.effecttype < 95):
            # Phaser/Flanger -> purple
            self.color = [purple]
            self.bitmap_palette_index = 4
        elif (90 < self.effecttype and self.effecttype < 110):
            # Equalizer -> yellow
            self.color = [yellow]
            self.bitmap_palette_index = 1
        elif (110 < self.effecttype and self.effecttype < 120):
            # Booster -> red
            self.color = [red]
            self.bitmap_palette_index = 3
        elif (120 < self.effecttype and self.effecttype < 125):
            # Looper -> purple
            self.color = [turquoise]
            self.bitmap_palette_index = 5
        elif (125 < self.effecttype and self.effecttype < 135):
            # Pitch -> white
            self.color = [white]
            self.bitmap_palette_index = 0
        elif (135 < self.effecttype and self.effecttype < 140):
            # Dual -> green
            self.color = [green]
            self.bitmap_palette_index = 7
        elif (140 < self.effecttype and self.effecttype < 170):
            # Delay -> green
            self.color = [green]
            self.bitmap_palette_index = 7
        else:
            # Reverb -> green
            self.color = [darkgreen]
            self.bitmap_palette_index = 8

        return

# function to control neopixel segments - color in full brightness
def light_active(x, c):
    # print(str(x) + ' : ' + str(c[0]))
    pixelpin = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11],
                [12, 13, 14], [15, 16, 17]]

    for i in pixelpin[x]:
        LED[i] = c[0]

    switch[x].state = "on"
    return


# function to control neopixel segments - color in smaller brightness
def light_dim(x, c):
    # print(str(x) + ' : ' + str(c[0]))
    pixelpin = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11],
                [12, 13, 14], [15, 16, 17]]
    dimcolor = (c[0][0]//10, c[0][1]//10, c[0][2]//10)

    for i in pixelpin[x]:
        LED[i] = dimcolor

    switch[x].state = "off"
    return

# function to control neopixel segments - deactivate light
def light_off(x):
    pixelpin = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11],
                [12, 13, 14], [15, 16, 17]]

    for i in pixelpin[x]:
        LED[i] = (0, 0, 0)

    # deactivate switch
    switch[x].state = "na"
    return

# function to get Kemper Player Rig Name
def request_kpp_rig_name():
    # request rig name
    midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                  [0x02, 0x7f, 0x43, 0x00, 0x00, 0x01]))

# function to get Kemper Player Rig Creation Date
def request_kpp_rig_date():
    # request rig date
    midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                  [0x02, 0x7f, 0x43, 0x00, 0x00, 0x03]))


# function to get Kemper Player Rig Infos
def request_kpp_rig_details():

    # KPP Effect Module DLY
    # Stomp Type
    midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                  [0x02, 0x7f, 0x41, 0x00, 0x3c, 0x00]))
    # KPP Effekt Module REV
    # Stomp Type
    midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                  [0x02, 0x7f, 0x41, 0x00, 0x3d, 0x00]))
    # KPP Effect Module A
    # Stomp Type (Integer)
    midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                  [0x02, 0x7f, 0x41, 0x00, 0x32, 0x00]))
    # KPP Effect Module+ B
    # Stomp Type
    midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                  [0x02, 0x7f, 0x41, 0x00, 0x33, 0x00]))
    return

# function to get Kemper Effect Status Infos
def get_kpp_effect_status():
    # KPP Effect Module DLY
    # Stomp DLY Status
    if switch[0].state != 'na':
        midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                      [0x02, 0x7f, 0x41, 0x00, 0x3c, 0x03]))

    # KPP Effekt Module REV
    # Stomp Status
    if switch[1].state != 'na':
        midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                      [0x02, 0x7f, 0x41, 0x00, 0x3d, 0x03]))
    # KPP Effect Module A
    # Stomp Status
    if switch[3].state != 'na':
        midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                      [0x02, 0x7f, 0x41, 0x00, 0x32, 0x03]))
    # KPP Effect Module+ B
    # Stomp Status
    if switch[4].state != 'na':
        midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                      [0x02, 0x7f, 0x41, 0x00, 0x33, 0x03]))
    return

# function to control neopixel segments - color in full brightness
def get_module_name(x):
    name = ''
    if (0 < x and x < 14):
        # Wah -> orange
        name = 'Wah Wah'
    elif (16 < x and x < 45):
        # Booster -> red
        name = 'Distortion'
    elif (47 < x and x < 55):
        # Compressor -> blue
        name = 'Compress'
    elif (55 < x and x < 60):
        # Compressor -> blue
        name = 'Noise Gate'
    elif (60 < x and x < 64):
        # Space -> green
        name = 'Space'
    elif (64 < x and x < 80):
        # Chorus -> blue
        name = 'Chorus'
    elif (80 < x and x < 95):
        # Phaser/Flanger -> purple
        name = 'Phaser'
    elif (90 < x and x < 110):
        # Equalizer -> yellow
        name = 'Equalizer'
    elif (110 < x and x < 120):
        # Booster -> red
        name = 'Booster'
    elif (120 < x and x < 125):
        # Phaser/Flanger -> purple
        name = 'Loop'
    elif (125 < x and x < 135):
        # Pitch -> white
        name = 'Transpose '
    elif (135 < x and x < 142):
        # Dual -> green
        name = 'Dual'
    elif (140 < x and x < 170):
        # Dual -> green
        name = 'Delay'
    else:
        name = 'Reverb'

    return name

print("Kemper Stomp Box Modus")

# Define Switch Objects to hold data
switch = []
# with hardware assingment and color+
switch.append(FootSwitch(board.GP1, list(darkgreen)))
switch.append(FootSwitch(board.GP25, list(green)))
switch.append(FootSwitch(board.GP24, list(white)))
switch.append(FootSwitch(board.GP9, list(red)))
switch.append(FootSwitch(board.GP10, list(yellow)))
switch.append(FootSwitch(board.GP11, list(orange)))


# set start values
LED.fill(0x000000)  # start using

# Kemper Rig Name
rig_name = ''
rig_date = ''

pushed = False

# Dim Light on for special switches
light_dim(2, switch[2].color)
light_dim(5, switch[5].color)


while True:
    if switch[0].switch.value is False:
        if pushed is False:

            pushed = True
            if switch[0].state == "off":
                midi_usb.send(ControlChange(27, 1))
                midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                              [0x02, 0x7f, 0x41, 0x00, 0x3c, 0x03]))
            else:
                midi_usb.send(ControlChange(27, 0))
                midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                              [0x02, 0x7f, 0x41, 0x00, 0x3c, 0x03]))

    elif switch[1].switch.value is False:
        if pushed is False:
            # [1][SE][0x002033][0x027f41003d03]

            pushed = True
            if switch[1].state == "off":
                midi_usb.send(ControlChange(28, 1))
                midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                              [0x02, 0x7f, 0x41, 0x00, 0x3d, 0x03]))
            else:
                midi_usb.send(ControlChange(28, 0))
                midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                              [0x02, 0x7f, 0x41, 0x00, 0x3d, 0x03]))

    elif switch[2].switch.value is False:
        if pushed is False:

            pushed = True
            if switch[2].state == "off":
                light_active(2, switch[2].color)
                # switch[2].state = "on"
                midi_usb.send(ControlChange(31, 127))
            else:
                light_dim(2, switch[2].color)
                # switch[2].state = "off"
                midi_usb.send(ControlChange(31, 0))

    elif switch[3].switch.value is False:
        # [1][SE][0x002033][0x027f41003203]
        if pushed is False:

            pushed = True
            if switch[3].state == "off":
                midi_usb.send(ControlChange(17, 1))
                midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                              [0x02, 0x7f, 0x41, 0x00, 0x32, 0x03]))
            else:
                midi_usb.send(ControlChange(17, 0))
                midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                              [0x02, 0x7f, 0x41, 0x00, 0x32, 0x03]))

    elif switch[4].switch.value is False:
        if pushed is False:
            # [1][SE][0x002033][0x027f41003303]

            pushed = True
            if switch[4].state == "off":
                midi_usb.send(ControlChange(18, 1))
                midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                              [0x02, 0x7f, 0x41, 0x00, 0x33, 0x03]))
            else:
                midi_usb.send(ControlChange(18, 0))
                midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                              [0x02, 0x7f, 0x41, 0x00, 0x33, 0x03]))

    elif switch[5].switch.value is False:
        if pushed is False:
            # ig volume booster
            pushed = True
            if switch[5].state == "off":
                light_active(5, switch[5].color)
                # switch[5].state = "on"
                # midi_usb.send(ControlChange(7, 127))
                # set rig volume to +3dB
                midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                              [0x02, 0x7f, 0x01, 0x00, 0x04, 0x01, 0x50, 0x00]))
            else:
                light_dim(5, switch[5].color)
                # switch[5].state = "off"
                # midi_usb.send(ControlChange(7, 1))
                # set rig volume to 0dB
                midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                              [0x02, 0x7f, 0x01, 0x00, 0x04, 0x01, 0x40, 0x00]))

    else:
        pushed = False

        # read Midi incomming data
        midimsg = midi_usb.receive()

        if midimsg is not None:
            if isinstance(midimsg, ControlChange):
                string_msg = 'ControlChange'
                string_val = str(midimsg.control)

            elif isinstance(midimsg, SystemExclusive):
                string_msg = 'SystemExclusive'
                string_val = str(midimsg.data)
                response = list(midimsg.data)

                # Stomp DLY Status
                if response[:-3] == [0x00, 0x00, 0x01, 0x00, 0x3c]:
                    if response[5] == 0x00:   # Effect Type Response

                        # Effect Type in last 2 list elements
                        effecttype = response[-2] * 128 + response[-1]

                        # is detected Effect Type new?
                        if switch[0].effecttype != effecttype:

                            # update Effect Type in Object
                            switch[0].effecttype = effecttype

                            # is Effectslot is empty?
                            if effecttype == 0:
                                light_off(0)
                                text_DLY_area.text = 'Empty'
                                splash[0] = Rect(1, 1, 120, 40, fill=palette[9], outline=0x0, stroke=1)

                            else:
                                # update new color in object
                                switch[0].setcolor()
                                text_DLY_area.text = get_module_name(effecttype)
                                splash[0] = Rect(1, 1, 120, 40, fill=palette[switch[0].bitmap_palette_index], outline=0x0, stroke=1)

                                # prepare for setting state over SysEx
                                if (switch[0].state == 'na'):
                                    switch[0].state = 'off'

                        get_kpp_effect_status()


                    elif (response[5] == 0x03) and (switch[0].effecttype != 0):   # Effect State Response
                        if (response[-1] == 0x01):
                            light_active(0, switch[0].color)
                        elif (response[-1] == 0x00):
                            light_dim(0, switch[0].color)

                # Stomp REV Status
                elif response[:-3] == [0x00, 0x00, 0x01, 0x00, 0x3d]:
                    if response[5] == 0x00:   # Effect Type Response

                        # Effect Type in last 2 list elements
                        received_typ = response[-2] * 128 + response[-1]

                        # is detected Effect Type new?
                        if switch[1].effecttype != received_typ:

                            # update Effect Type in Object
                            switch[1].effecttype = received_typ
                            # is Effectslot is empty?
                            if received_typ == 0:
                                light_off(1)
                                text_REV_area.text = 'Empty'
                                splash[1] = Rect(120, 1, 120, 40, fill=palette[9], outline=0x0, stroke=1)

                            else:
                                # update new color in object #### have to be deleted
                                switch[1].setcolor()
                                text_REV_area.text = get_module_name(received_typ)
                                splash[1] = Rect(120, 1, 120, 40, fill=palette[switch[1].bitmap_palette_index], outline=0x0, stroke=1)

                                # prepare for setting state over SysEx
                                if (switch[1].state == 'na'):
                                    switch[1].state = 'off'

                        get_kpp_effect_status()

                    elif (response[5] == 0x03) and (switch[1].effecttype != 0):   # Effect State Response
                        if (response[-1] == 0x01):
                            light_active(1, switch[1].color)
                        elif (response[-1] == 0x00):
                            light_dim(1, switch[1].color)

                # Stomp A Status
                elif response[:-3] == [0x00, 0x00, 0x01, 0x00, 0x32]:
                    if response[5] == 0x00:   # Effect Type Response

                        # Effect Type in last 2 list elements
                        received_typ = response[-2] * 128 + response[-1]

                        # is detected Effect Type new?
                        if switch[3].effecttype != received_typ:

                            # update Effect Type in Object
                            switch[3].effecttype = received_typ
                            # is Effectslot is empty?
                            if received_typ == 0:
                                light_off(3)
                                text_A_area.text = 'Empty'
                                splash[2] = Rect(1, 200, 120, 40, fill=palette[9], outline=0x0, stroke=1)
                            else:
                                # update new color in object
                                switch[3].setcolor()
                                splash[2] = Rect(1, 200, 120, 40, fill=palette[switch[3].bitmap_palette_index], outline=0x0, stroke=1)
                                text_A_area.text = get_module_name(received_typ)

                                # prepare for setting state over SysEx
                                if (switch[3].state == 'na'):
                                    switch[3].state = 'off'

                        get_kpp_effect_status()

                    elif (response[5] == 0x03) and (switch[3].effecttype != 0):   # Effect State Response
                        if (response[-1] == 0x01):
                            light_active(3, switch[3].color)
                        elif (response[-1] == 0x00):
                            light_dim(3, switch[3].color)

                # Stomp B Status
                elif response[:-3] == [0x00, 0x00, 0x01, 0x00, 0x33]:
                    if response[5] == 0x00:   # Effect Type Response

                        # Effect Type in last 2 list elements
                        received_typ = response[-2] * 128 + response[-1]

                        # is detected Effect Type new?
                        if switch[4].effecttype != received_typ:

                            # update Effect Type in Object
                            switch[4].effecttype = received_typ
                            # is Effectslot is empty?
                            if (received_typ) == 0:
                                light_off(4)
                                text_B_area.text = 'Empty'
                                splash[3] = Rect(120, 200, 120, 40, fill=palette[9], outline=0x0, stroke=1)
                            else:
                                # update new color in object #### have to be deleted
                                switch[4].setcolor()
                                text_B_area.text = get_module_name(received_typ)
                                splash[3] = Rect(120, 200, 120, 40, fill=palette[switch[4].bitmap_palette_index], outline=0x0, stroke=1)

                                # prepare for setting state over SysEx
                                if (switch[4].state == 'na'):
                                    switch[4].state = 'off'

                        get_kpp_effect_status()

                    elif (response[5] == 0x03) and (switch[4].effecttype != 0):   # Effect State Response
                        if (response[-1] == 0x01):
                            light_active(4, switch[4].color)
                        elif (response[-1] == 0x00):
                            light_dim(4, switch[4].color)

                # Rig Name
                elif response[:6] == [0x00, 0x00, 0x03, 0x00, 0x00, 0x01]:

                    ascii_string = ''.join(chr(int(c)) for c in response[6:-1])

                    if ascii_string != rig_name:
                        rig_name = ascii_string
                        # print(rig_name)
                        # rigtext = ''
                        if len(rig_name) > 22:
                            # rigtext = rig_name[:22]
                            rigtext = rig_name
                        else:
                            rigtext = rig_name

                        text_area_rig.text = "\n".join(wrap_text_to_pixels(rigtext, wrap_with, font))

                        # reset activated 'Booster' on Switch 5
                        if switch[5].state == "on":
                            light_dim(5, switch[5].color)
                            switch[5].state = "off"
                            midi_usb.send(ControlChange(7, 1))

                # Rig Creation Date
                elif response[:6] == [0x00, 0x00, 0x03, 0x00, 0x00, 0x03]:

                    ascii_string = ''.join(chr(int(c)) for c in response[6:-1])

                    if ascii_string != rig_date:
                        rig_date = ascii_string
                        request_kpp_rig_details()
                        request_kpp_rig_name()
                        get_kpp_effect_status()


                else:
                    # every other SysEx mesage
                    print('not yet assignt: ' + str(response))

            elif isinstance(midimsg, MIDIUnknownEvent):
                # use Midi keep alive Message as trigger
                # these statements dectects rig changes
                request_kpp_rig_date()
                string_msg = ''


            else:
                # not yet assignt midi messages
                string_msg = ''

