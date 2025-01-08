import board
import digitalio
import busio
import displayio
import time
from adafruit_display_text import label, wrap_text_to_pixels
from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes.rect import Rect
#from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.line import Line
import adafruit_imageload
import usb_midi
import adafruit_midi  # MIDI protocol encoder/decoder library
from adafruit_midi.control_change import ControlChange
from adafruit_midi.program_change import ProgramChange
from adafruit_midi.system_exclusive import SystemExclusive
from adafruit_midi.midi_message import MIDIUnknownEvent

# from adafruit_midi.active_sensing import ActiveSensing
from adafruit_midi.midi_message import MIDIMessage
class ActiveSensing(MIDIMessage):
    """Active Sensing MIDI message.

    Active Sensing message is a keepalive message sent every 300 milliseconds
    to tell the bus that the session is still good and alive.
    """

    _STATUS = 0xFE
    _STATUSMASK = 0xFF
    LENGTH = 1
    _slots = []

ActiveSensing.register_message_type()

try:
    from fourwire import FourWire
except ImportError:
    from displayio import FourWire

from adafruit_st7789 import ST7789
import neopixel

# ### Initialize User Preferences
LED_brightness = 0.4   # small values recommended

MIDI_USB_channel = 1   # pick your USB MIDI out channel here, 1-16

# Schalterzuweisung im SlotView
switch_x = 99
switch_mod = 99
switch_dly = 0
switch_rev = 1
switch_a = 3
switch_b = 4
switch_c = 99
switch_d = 99

# possible initial modes stomp, performance
mode ="performance"

# ### Configure Hardware ###

# use neopixel for first status messages while initial sequence of this script
# neopixel documentation
# https://docs.circuitpython.org/projects/neopixel/en/latest/
# https://learn.adafruit.com/adafruit-neopixel-uberguide/python-circuitpython
pixel_pin = board.GP7
LED_amount = 18
LED = neopixel.NeoPixel(pixel_pin, LED_amount, brightness=LED_brightness)

LED.fill(0xff0000)  # set boot status: red

# Release any resources currently in use for the displays
displayio.release_displays()
# hardware assignt for display
tft_pwm = board.GP8
tft_cs = board.GP13
tft_dc = board.GP12
spi_mosi = board.GP15
spi_clk = board.GP14

spi = busio.SPI(spi_clk, spi_mosi)
while not spi.try_lock():
    spi.configure(baudrate=24000000)  # Configure SPI for 24MHz
spi.unlock()

display_bus = displayio.FourWire(
    spi, command=tft_dc, chip_select=tft_cs, reset=None, baudrate=24000000)

display = ST7789(display_bus,
                 width=240, height=240,
                 rowstart=80, rotation=180)

midi_usb = adafruit_midi.MIDI(midi_out=usb_midi.ports[1],
                              out_channel=MIDI_USB_channel - 1,
                              midi_in=usb_midi.ports[0],
                              in_buf_size=60, debug=False)

# ### Configure Software ###########################################
# ### initial program values #######################################
con_init = False
con_established = False
tuningnote = 0
bankselect = 0
midi_pc_value = 5

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

# define fonts
font = bitmap_font.load_font("/fonts/PTSans-NarrowBold-40.pcf")
font_Note = bitmap_font.load_font("/fonts/RobotoCondensed-Regular-Notes-125.pcf")
font_H20 = bitmap_font.load_font("/fonts/H20.pcf")
wrap_with = 240  # in pixel


# Make display assingment
splash = displayio.Group()
display.rootgroup = splash

# ### set boot status yellow ###############################
LED.fill(0xffff00)

# ### Define Slot Mode Dsiplay Group #######################
view_slot = displayio.Group()
# Draw Effect Module DLY
rect = Rect(1, 1, 120, 40, fill=palette[7], outline=0x0, stroke=1)
view_slot.append(rect)  # position [0] IMPORTANT!

text_group_DLY = displayio.Group(scale=1, x=1, y=1)
text_DLY = "Delay"
text_DLY_area = label.Label(font_H20, text=text_DLY, color=0x0, anchor_point=(0.5, 0.5), anchored_position=(60, 20))
text_group_DLY.append(text_DLY_area)  # Subgroup for text scaling

# Draw Effect Module REV
rect = Rect(120, 1, 120, 40, fill=palette[8], outline=0x0, stroke=1)
view_slot.append(rect)  # position [1] IMPORTANT!

text_group_REV = displayio.Group(scale=1, x=120, y=1)
text_REV = "Reverb"
text_REV_area = label.Label(font_H20, text=text_REV, color=0x0, anchor_point=(0.5, 0.5), anchored_position=(60, 20))
text_group_REV.append(text_REV_area)  # Subgroup for text scaling

# placeholder for append position
text_group_rig = displayio.Group(scale=1)
view_slot.append(text_group_rig)

# Draw Effect Module A
rect = Rect(1, 200, 120, 40, fill=palette[5], outline=0x0, stroke=1)
view_slot.append(rect)  # position [3] IMPORTANT!

text_group_A = displayio.Group(scale=1, x=1, y=200)
text_A = "Module A"
text_A_area = label.Label(font_H20, text=text_A, color=0x0, anchor_point=(0.5, 0.5), anchored_position=(60, 20))
text_group_A.append(text_A_area)  # Subgroup for text scaling

# Draw Effect Module A
rect = Rect(120, 200, 120, 40, fill=palette[6], outline=0x0, stroke=1)
view_slot.append(rect)  # position [4] IMPORTANT!

text_group_B = displayio.Group(scale=1, x=120, y=200)
text_B = "Module B"
text_B_area = label.Label(font_H20, text=text_B, color=0x0, anchor_point=(0.5, 0.5), anchored_position=(60, 20))
text_group_B.append(text_B_area)  # Subgroup for text scaling

# add  text groups to view
view_slot.append(text_group_DLY)
view_slot.append(text_group_REV)
view_slot.append(text_group_A)
view_slot.append(text_group_B)

splash.append(view_slot)  # position 0
splash[0].hidden = True

# ### Define Performance Mode Dsiplay Group #######################
perf_view = displayio.Group()
# Draw Rig 1
rect = Rect(1, 1, 80, 30, fill=palette[0], outline=0x0, stroke=1)
perf_view.append(rect)

text_group_rig1 = displayio.Group(scale=1, x=1, y=1)
text_rig1 = "Rig 1"
text_rig1_area = label.Label(font_H20, text=text_rig1, color=0x0, anchor_point=(0.5, 0.5), anchored_position=(40, 15))
text_group_rig1.append(text_rig1_area)  # Subgroup for text scaling

# Draw Rig2
rect = Rect(80, 1, 80, 30, fill=palette[1], outline=0x0, stroke=1)
perf_view.append(rect)

text_group_rig2 = displayio.Group(scale=1, x=80, y=1)
text_rig2 = "Rig 2"
text_rig2_area = label.Label(font_H20, text=text_rig2, color=0x0, anchor_point=(0.5, 0.5), anchored_position=(40, 15))
text_group_rig2.append(text_rig2_area)  # Subgroup for text scaling

# Draw Rig3
rect = Rect(160, 1, 80, 30, fill=palette[2], outline=0x0, stroke=1)
perf_view.append(rect)

text_group_rig3 = displayio.Group(scale=1, x=160, y=1)
text_rig3 = "Rig 3"
text_rig3_area = label.Label(font_H20, text=text_rig3, color=0x0, anchor_point=(0.5, 0.5), anchored_position=(40, 15))
text_group_rig3.append(text_rig3_area)  # Subgroup for text scaling

# Draw Rig 4
rect = Rect(1, 200, 80, 30, fill=palette[0], outline=0x0, stroke=1)
perf_view.append(rect)
text_group_rig4 = displayio.Group(scale=1, x=1, y=200)
text_rig4 = "Rig 4"
text_rig4_area = label.Label(font_H20, text=text_rig4, color=0x0, anchor_point=(0.5, 0.5), anchored_position=(40, 15))
text_group_rig4.append(text_rig4_area)  # Subgroup for text scaling

# Draw Rig 5
rect = Rect(80, 200, 80, 30, fill=palette[1], outline=0x0, stroke=1)
perf_view.append(rect)

text_group_rig5 = displayio.Group(scale=1, x=80, y=200)
text_rig5 = "Rig 5"
text_rig5_area = label.Label(font_H20, text=text_rig5, color=0x0, anchor_point=(0.5, 0.5), anchored_position=(40, 15))
text_group_rig5.append(text_rig5_area)  # Subgroup for text scaling

# Draw Tuner
rect = Rect(160, 200, 80, 30, fill=palette[2], outline=0x0, stroke=1)
perf_view.append(rect)

text_group_tuner = displayio.Group(scale=1, x=160, y=200)
text_tuner = "Tuner"
text_tuner_area = label.Label(font_H20, text=text_tuner, color=0x0, anchor_point=(0.5, 0.5), anchored_position=(40, 15))
text_group_tuner.append(text_tuner_area)  # Subgroup for text scaling
# add  text groups to performance view+
perf_view.append(text_group_rig1)
perf_view.append(text_group_rig2)
perf_view.append(text_group_rig3)
perf_view.append(text_group_rig4)
perf_view.append(text_group_rig5)
perf_view.append(text_group_tuner)

splash.append(perf_view)
splash[1].hidden = True

# ### Define Rig Info Dsiplay Group #######################
rig_view = displayio.Group()
#  Rig Name Field
text_group_rig = displayio.Group(scale=1)
text = "MIDI Captain\nfor Kemper"
text_area_rig = label.Label(font, text="\n".join(wrap_text_to_pixels(text, wrap_with, font)), color=0xFFFFFF, line_spacing=0.9)
text_area_rig.anchor_point = (0.5, 0.5)
text_area_rig.anchored_position = (120, 90)
text_group_rig.append(text_area_rig)  # Subgroup for text scaling

#text_group_Log = displayio.Group(scale=1, x=1, y=41)
#text_Log = "Wait for connection"
#text_Log_area = label.Label(font_H20, text=text_Log, color=0x808080, anchor_point=(1, 0.5), anchored_position=(240, 20))
#text_group_Log.append(text_Log_area)

line1 = Line(1, 150, 240, 150, color=0xbebebe)
line2 = Line(60, 150, 60, 200, color=0xbebebe)
rig_view.append(line1)
rig_view.append(line2)

text_group_bank = displayio.Group(scale=1)
#circle = Circle(20, 60, 20, fill=0x618da8, outline=0x0594ec)
#text_group_rig.append(circle)
text_group_Bank = displayio.Group(scale=1, x=1, y=150)
text_Bank = "-"
text_Bank_area = label.Label(font, text=text_Bank, color=0xFFFFFF, anchor_point=(0.5, 0.5), anchored_position=(30, 25))
#text_Bank_area.anchor_point = (0.5, 0.5)
#text_Bank_area.anchored_position = (30, 150)
text_group_Bank.append(text_Bank_area)

text_group_songpart = displayio.Group(scale=1)
#circle = Circle(20, 60, 20, fill=0x618da8, outline=0x0594ec)
#text_group_rig.append(circle)
text_group_songpart = displayio.Group(scale=1, x=60, y=150)
text_songpart = "wait for KPP"
text_area_songpart = label.Label(font, text=text_songpart, color=0xFFFFFF, anchor_point=(0.5, 0.5), anchored_position=(90, 25))
#text_Bank_area.anchor_point = (0.5, 0.5)
#text_Bank_area.anchored_position = (30, 150)
text_group_songpart.append(text_area_songpart)

rig_view.append(text_group_rig)
#rig_view.append(text_group_Log)
rig_view.append(text_group_Bank)
rig_view.append(text_group_songpart)


splash.append(rig_view)

# activate Display
display.show(splash)
if mode == "stomp":
    # activate Slot/Effect View
    splash[0].hidden = False
else:
    # activate Performance View
    splash[1].hidden = False


# ### Prepare display context for Tuner presentation ###
TunerSplash = displayio.Group()
# Setup the file as the bitmap data source
bitmap = displayio.OnDiskBitmap("/images/TunerDisplay.bmp")

# Create a TileGrid to hold the bitmap
wp_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)

# Load the sprite sheet (bitmap)
sprite_sheet, tunerpalette = adafruit_imageload.load("/images/TunerSprite.bmp",
                                                bitmap=displayio.Bitmap,
                                                palette=displayio.Palette)
tunerpalette.make_transparent(0)

pointergroup = displayio.Group(scale=1)
pointer = Line(1, 20, 1, 70, color=0xffffee)
pointergroup.append(pointer)

text_group_tuner = displayio.Group(scale=1)
# Add the Wallpaer TileGrid to the Group
text_group_tuner.append(wp_grid)

text_area_tuner = label.Label(font_Note, text="--", color=0xFFFFFF, scale=1)
text_area_tuner.anchor_point = (0.5, 0.5)
text_area_tuner.anchored_position = (123, 153)
text_group_tuner.append(text_area_tuner)  # Subgroup for text scaling
TunerSplash.append(text_group_tuner)
TunerSplash.append(pointergroup)


# function to control neopixel segments - color in full brightness
def light_active(x, c):
    switch[x].state = "on"

    if mode == "stomp":
        pixelpin = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11],
                    [12, 13, 14], [15, 16, 17]]

        for i in pixelpin[x]:
            LED[i] = c[0]

    return


# function to control neopixel segments - color in smaller brightness
def light_dim(x, c):
    switch[x].state = "off"

    if mode == "stomp":
        pixelpin = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11],
                    [12, 13, 14], [15, 16, 17]]
        dimcolor = (c[0][0]//10, c[0][1]//10, c[0][2]//10)

        for i in pixelpin[x]:
            LED[i] = dimcolor

    return


# function to control neopixel segments - deactivate light
def light_off(x):
    # deactivate switch
    switch[x].state = "na"

    if mode == "stomp":
        pixelpin = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11],
                   [12, 13, 14], [15, 16, 17]]

        for i in pixelpin[x]:
            LED[i] = (0, 0, 0)

    return


def light_slots():
    for i in [0,1,3,4]:
        if switch[i].state == 'on':
            light_active(i, switch[i].color)
        elif switch[i].state == 'off':
            light_dim(i, switch[i].color)
        else:
            light_off(i)

    return


# function to control neopixel segments - Rig switch in full brightness
def light_rig(x):
    # print(str(x) + ' : ' + str(c[0]))
    pixelpin = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11],
                [12, 13, 14]]

    iterate = 0
    for i in pixelpin:
        if iterate == x:
            for a in i:
                if LED[a] == (255, 0, 0):
                    LED[a] = (0, 0, 255)
                else:
                    LED[a] = (255, 0, 0)
        else:
            for a in i:
                LED[a] = (0, 25, 0)
        iterate += 1
    return

def light_rig_init(x):
    # print(str(x) + ' : ' + str(c[0]))
    pixelpin = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11],
                [12, 13, 14], [15, 16, 17]]

    iterate = 0
    for i in pixelpin:
        if iterate == x:
            for a in i:
                LED[a] = (255, 0, 0)
        elif iterate == 5:
            for a in i:
                LED[a] = (25, 16, 0)
        else:
            for a in i:
                LED[a] = (0, 25, 0)
        iterate += 1
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

# function to react on MIDI SysEx Messages
def parse_MidiSysExMsg(MidiMessage):
    if MidiMessage[:-1] == [0x00, 0x00, 0x01, 0x00, 0x7c, 0x00, 0x00]:
        # TAP Message
        # message changing between 0 and 1 on last digit
        # not used yet
        return

    if MidiMessage[0] == 0x02:
        # Slot Enabled Messages
        # not used yet
        return

    # actual Rig Name
    if MidiMessage[:6] == [0x00, 0x00, 0x03, 0x00, 0x00, 0x01]:

        ascii_string = ''.join(chr(int(c)) for c in MidiMessage[6:-1])

        if ascii_string.find('(') + ascii_string.find(')') > 0:
            # extract optional Song Part between '(' and ')'
            songpart = ascii_string[ascii_string.index('(')+1:ascii_string.index(')')]
            rigname = ascii_string[:ascii_string.find('(')-1]
        else:
            # shorten Rig Name
            songpart = ""
            rigname = ascii_string
        text_area_rig.text = "\n".join(wrap_text_to_pixels(rigname, wrap_with, font))
        text_area_songpart.text = songpart

    # get the 5 Rig Names of the active bank
    elif MidiMessage[:8] == [0x00, 0x00, 0x07, 0x00, 0x00, 0x00, 0x01, 0x00]:
        ascii_string = ''.join(chr(int(c)) for c in MidiMessage[9:-1])
        if ascii_string.find('(') + ascii_string.find(')') > 0:
            # extract optional Song Part between '(' and ')'
            songpart = ascii_string[ascii_string.index('(')+1:ascii_string.index(')')]
        else:
            # shorten Rig Name
            songpart =ascii_string[:6]

        rignames[MidiMessage[8] - 1].text = songpart
    #    if MidiMessage[8] == 0x01:
     #       text_rig1_area.text = songpart
      #  elif MidiMessage[8] == 0x02:
       #     text_rig2_area.text = songpart
        #elif MidiMessage[8] == 0x03:
         #   text_rig3_area.text = songpart
     #   elif MidiMessage[8] == 0x04:
      #      text_rig4_area.text = songpart
       # else:
        #    text_rig5_area.text = songpart


    # get effects slots status and type
    elif MidiMessage[:-4] == [0x00, 0x00, 0x01, 0x00] and len(MidiMessage) == 8:
        switch_number = 99
        if (MidiMessage[4] >= 0x32) and (MidiMessage[4] <= 0x4b):
            if MidiMessage[4] == 0x32:
                switch_number = switch_a
            elif MidiMessage[4] == 0x33:
                switch_number = switch_b
            elif MidiMessage[4] == 0x34:
                switch_number = switch_c
            elif MidiMessage[4] == 0x35:
                switch_number = switch_d
            elif MidiMessage[4] == 0x38:
                switch_number = switch_x
            elif MidiMessage[4] == 0x3a:
                switch_number = switch_mod
            elif MidiMessage[4] == 0x3c:
                switch_number = switch_dly
            elif MidiMessage[4] == 0x3d:
                switch_number = switch_rev
            elif MidiMessage[4] == 0x4a:
                switch_number = switch_dly
            else:
                switch_number = switch_rev


        # Effect Type Response
        if (MidiMessage[5] == 0x00) and (switch_number != 99):

            # Effect Type in last 2 list elements
            effecttype = MidiMessage[-2] * 128 + MidiMessage[-1]
            # update Effect Type in Object
            switch[switch_number].effecttype = effecttype

            # is Effectslot empty?
            if effecttype == 0:
                light_off(switch_number)
                if switch_number == 0:
                    text_DLY_area.text = '-'
                    view_slot[switch_number] = Rect(1, 1, 120, 40, fill=palette[9], outline=0x0, stroke=1)
                elif switch_number == 1:
                    text_REV_area.text = '-'
                    view_slot[switch_number] = Rect(120, 1, 120, 40, fill=palette[9], outline=0x0, stroke=1)
                elif switch_number == 3:
                    view_slot[switch_number] = Rect(1, 200, 120, 40, fill=palette[9], outline=0x0, stroke=1)
                    text_A_area.text = '-'
                else:
                    text_B_area.text = '-'
                    view_slot[switch_number] = Rect(120, 200, 120, 40, fill=palette[9], outline=0x0, stroke=1)

            else:
                # update new color in object
                switch[switch_number].setcolor()

                if switch_number == 0:
                    text_DLY_area.text = get_module_name(effecttype)
                    view_slot[switch_number] = Rect(1, 1, 120, 40, fill=palette[switch[switch_number].bitmap_palette_index], outline=0x0, stroke=1)
                elif switch_number == 1:
                    text_REV_area.text = get_module_name(effecttype)
                    view_slot[switch_number] = Rect(120, 1, 120, 40, fill=palette[switch[switch_number].bitmap_palette_index], outline=0x0, stroke=1)
                elif switch_number == 3:
                    view_slot[switch_number] = Rect(1, 200, 120, 40, fill=palette[switch[switch_number].bitmap_palette_index], outline=0x0, stroke=1)
                    text_A_area.text = get_module_name(effecttype)
                else:
                    text_B_area.text = get_module_name(effecttype)
                    view_slot[switch_number] = Rect(120, 200, 120, 40, fill=palette[switch[switch_number].bitmap_palette_index], outline=0x0, stroke=1)

                # prepare for setting state over SysEx
                if (switch[switch_number].state == 'na') or (switch[switch_number].state == 'off'):
                    light_dim(switch_number, switch[switch_number].color)
                else:
                    light_active(switch_number, switch[switch_number].color)

        elif ((MidiMessage[5] == 0x02) or (MidiMessage[5] == 0x03)) and (switch_number != 99):   # Effect State Response
            if  (switch[switch_number].effecttype != 0):
                if (MidiMessage[-1] == 0x01):
                    light_active(switch_number, switch[switch_number].color)
                elif (MidiMessage[-1] == 0x00):
                    light_dim(switch_number, switch[switch_number].color)

        # activate tuner view
        elif MidiMessage[4:-2] == [0x7f, 0x7e] and len(MidiMessage) == 8:
            if MidiMessage[-1] == 0x01:   # show tuner
                display.show(TunerSplash)
            else:                      # deactivate tuner
                display.show(splash)

        # tuner notes infos
        elif MidiMessage[4:-2] == [0x7d, 0x54]:
            text_area_tuner.text = integer_to_note(MidiMessage[-1])

        # tuner tuning
        elif MidiMessage[4:-2] == [0x7c, 0x0f]:
            tuniningrate = MidiMessage[-2] * 128 + MidiMessage[-1]
            xposition = int(tuniningrate / 8192 * 120)
            if xposition <= 25:
                xposition = 26
            elif xposition >=215:
                xposition = 215
            pointergroup.x = xposition
            if abs(tuniningrate - 8192) < 300:
                text_area_tuner.color=0xFFFFFF
                pointer.color=0xffffff
            else:
                text_area_tuner.color=0xbbbbbb
                if abs(tuniningrate - 8192) < 2000:
                    pointer.color=0xFFDE00
                else:
                    pointer.color=0xFF0000


        else:
            #nothing to do
            #text_Log_area.text = 'MIDI Info ' + str(response)
            string_msg = ''

    else:
        # every other SysEx mesage
        print('not yet assignt: ' + str(MidiMessage))
        text_area_rig.text = "\n".join(wrap_text_to_pixels(str(MidiMessage), wrap_with, font))
        #text_Log_area.text = 'MIDI event ' + str(response)

    return

# function to control neopixel segments - color in smaller brightness
def send_beacon():
#    text_Log_area.text = 'connection established'
    # I use Parameter Set 2

    # init off
    # use Sysex response (on)
    # echo off
    # NOFE off
    # NOCTOR on
    # TUNEMODE on
    # -> 0x32

    # init off
    # use Sysex response (on)
    # echo off
    # NOFE on
    # NOCTOR on
    # TUNEMODE on
    # -> 0x3A


    # init off
    # use Sysex response
    # echo on
    # NOFE off
    # NOCTOR on
    # TUNEMODE on
    # -> 0x36

    # send beacon
    midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                  [0x02, 0x7f, 0x7e, 0x00, 0x40, 0x02, 0x3A, 0x7f]))
    return

def send_initbeacon():
    #text_Log_area.text = 'connection initialization'
    # Parameter Set 2
    # use Sysex response
    # init on
    # echo off
    # NOFE off
    # NOCTOR on
    # TUNEMODE on
    # -> 0x33
    # send beacon
    midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                  [0x02, 0x7f, 0x7e, 0x00, 0x40, 0x02, 0x33, 0x04]))
    con_init = True
    get_kpp_effect_status() # workaround while Kemper is sending false status
    return

# function to get Kemper Effect Status Infos
def get_kpp_effect_status():
    # after connection initialization Kemper sends two times effects slot status for DLY and REF
    # but second message told status is off, altough status is on :-/
    # so I trigger it here again as workaround
    # KPP Effect Module DLY
    # Stomp DLY Status
    midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                  [0x02, 0x7f, 0x41, 0x00, 0x3c, 0x03]))

    # KPP Effekt Module REV
    # Stomp Status
    midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                  [0x02, 0x7f, 0x41, 0x00, 0x3d, 0x03]))

    return

# function for tuner notes
def integer_to_note(x):
    # notes = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    notes = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']
    while x > 11:
        x = x -12

    return notes[x]

def KemperMidiVolumeBoost(x):
    if x == 'on':
        # set rig volume to +3dB
        midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                    [0x02, 0x7f, 0x01, 0x00, 0x04, 0x01, 0x50, 0x00]))
    else:
        # set rig volume to 0dB
        midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                    [0x02, 0x7f, 0x01, 0x00, 0x04, 0x01, 0x40, 0x00]))
    return

# Define Switch Objects to hold data
switch = []
# with hardware assingment and color+
switch.append(FootSwitch(board.GP1, list(darkgreen)))
switch.append(FootSwitch(board.GP25, list(green)))
switch.append(FootSwitch(board.GP24, list(white)))
switch.append(FootSwitch(board.GP9, list(red)))
switch.append(FootSwitch(board.GP10, list(yellow)))
switch.append(FootSwitch(board.GP11, list(orange)))


rignames = []
rignames.append(text_rig1_area)
rignames.append(text_rig2_area)
rignames.append(text_rig3_area)
rignames.append(text_rig4_area)
rignames.append(text_rig5_area)


# set start values
LED.fill(0x000000)  # start using

# Kemper Rig Name
rig_name = ''

pushed = False
active_switch = 99

# Dim Light on for special switches
# only in Stomp Modus
light_dim(2, switch[2].color)
light_dim(5, switch[5].color)

while True:
    if switch[0].switch.value is False:
        if pushed is False:

            pushed = True
            if mode == "stomp":
                if switch[0].state == "off":
                    midi_usb.send(ControlChange(27, 1))
                else:
                    midi_usb.send(ControlChange(27, 0))
            elif mode == "performance":
                midi_usb.send(ControlChange(50, 1))
                light_rig(0)
                midi_usb.send(ControlChange(50, 0))

    elif switch[1].switch.value is False:
        if pushed is False:

            pushed = True
            if mode == "stomp":
                if switch[1].state == "off":
                    midi_usb.send(ControlChange(28, 1))
                else:
                    midi_usb.send(ControlChange(28, 0))
            elif mode == "performance":
                midi_usb.send(ControlChange(51, 1))
                light_rig(1)
                midi_usb.send(ControlChange(51, 0))

    elif switch[2].switch.value is False:
        if pushed is False:
            start_press_time = time.monotonic()
            active_switch = 2

            pushed = True



    #        if switch[2].state == "off":
     #           light_active(2, switch[2].color)
                # switch[2].state = "on"
      #          midi_usb.send(ControlChange(31, 127))
       #     else:
        #        light_dim(2, switch[2].color)
                # switch[2].state = "off"
         #       midi_usb.send(ControlChange(31, 0))

    elif switch[3].switch.value is False:
        if pushed is False:
            start_press_time = time.monotonic()
            active_switch = 3
            pushed = True


    elif switch[4].switch.value is False:
        if pushed is False:

            pushed = True
            if mode == "stomp":
                if switch[4].state == "off":
                    midi_usb.send(ControlChange(18, 1))
                else:
                    midi_usb.send(ControlChange(18, 0))
            elif mode == "performance":
                midi_usb.send(ControlChange(54, 1))
                light_rig(4)
                midi_usb.send(ControlChange(54, 0))


    elif switch[5].switch.value is False:
        if pushed is False:
            start_press_time = time.monotonic()
            active_switch = 5
            # Rig volume booster
            pushed = True

           # if mode == "stomp":
            #    midi_usb.send(ControlChange(49, 0))
            #if switch[5].state == "off":
             #   light_active(5, switch[5].color)
                # switch[5].state = "on"
                # midi_usb.send(ControlChange(7, 127))
                # set rig volume to +3dB
              #  midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                #                              [0x02, 0x7f, 0x01, 0x00, 0x04, 0x01, 0x50, 0x00]))
            #else:
             #   light_dim(5, switch[5].color)
                # switch[5].state = "off"
                # midi_usb.send(ControlChange(7, 1))
                # set rig volume to 0dB
              #  midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
               #                               [0x02, 0x7f, 0x01, 0x00, 0x04, 0x01, 0x40, 0x00]))

    else:
        pushed = False
        if active_switch != 99:
            stop_press_time = time.monotonic()
            if stop_press_time-start_press_time >= 0.60:
                # Long Press
                if active_switch == 2:
                    if mode == "stomp":
                        midi_usb.send(ControlChange(48, 0))
                    elif mode == "performance":
                        midi_usb.send(ControlChange(48, 0))

                elif active_switch == 3:
                    if mode == "stomp":
                        mode = "performance"
                        splash[0].hidden = True
                        splash[1].hidden = False
                        light_rig_init(int(bankselect*128 + midi_pc_value)%5)
                    else:
                        mode = "stomp"
                        splash[0].hidden = False
                        splash[1].hidden = True
                        light_slots()
                    display.refresh()

                elif active_switch == 5:
                    midi_usb.send(ControlChange(49, 0))
            else:
                # Short Press
                if active_switch == 2:
                    if mode == "stomp":
                        midi_usb.send(ControlChange(48, 0))
                    elif mode == "performance":
                        midi_usb.send(ControlChange(52, 1))
                        light_rig(2)
                        midi_usb.send(ControlChange(52, 0))

                elif active_switch == 3:
                    if mode == "stomp":
                       # if switch[3].state == "off":
                        midi_usb.send(ControlChange(17, 127))
                        #else:
                         #   midi_usb.send(ControlChange(17, 0))
                    elif mode == "performance":
                        midi_usb.send(ControlChange(53, 1))
                        light_rig(3)
                        midi_usb.send(ControlChange(53, 0))

                elif active_switch == 5:
                    if switch[5].state == "off":
                        midi_usb.send(ControlChange(31, 127))
                        switch[5].state = "on"
                        light_active(5, switch[5].color)
                    else:
                        midi_usb.send(ControlChange(31, 0))
                        switch[5].state = "off"
                        light_dim(5, switch[5].color)

            active_switch = 99

        # ### read Midi incomming data ###################################################
        midimsg = midi_usb.receive()

        if midimsg is not None:

            # KPP Active Sensing
            if isinstance(midimsg, ActiveSensing):
                # use Kemper Midi Active Sensing Message as trigger
                # Reconnect to KPP
                if con_init and con_established:
                    send_initbeacon()
                    text_area_songpart.text = "connecting"
                    con_established = False
                # establish connection after initialization
                if con_init and not con_established:
                    send_beacon()
                    con_established = True
                # Initialize connection
                if not con_init:
                    send_initbeacon()
                    text_area_songpart.text = "connecting"
                    con_init = True


            elif isinstance(midimsg, ControlChange):
                # string_msg = 'ControlChange'
                midicc_control = midimsg.control
                midicc_val = midimsg.value
                # used to evalate bank changes above program changeges 127
                if midicc_control == 32:
                    bankselect = midicc_val


            elif isinstance(midimsg, ProgramChange):
                # string_msg = 'ProgramChange'
                midi_pc_value = midimsg.patch

                bank = int((bankselect*128 + midi_pc_value+5)/5)
                text_Bank_area.text = str(bank)
                if mode == "performance":
                    light_rig_init(int(bankselect*128 + midi_pc_value)%5)


            elif isinstance(midimsg, SystemExclusive):
                parse_MidiSysExMsg(list(midimsg.data))

            else:
                # not yet assignt or unknown midi messages
                string_msg = ''

