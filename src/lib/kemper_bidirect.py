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

# Schalterzuweisung
switch_x = 99
switch_mod = 99
switch_dly = 0
switch_rev = 1
switch_a = 3
switch_b = 4
switch_c = 99
switch_d = 99

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

con_init = False
con_established = False

# ### Configure Software ###

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


# disp_width = 240
# disp_height = 240
# CENTER_Y = int(disp_width/2)
# CENTER_X = int(disp_height/2)


# Make display context
splash = displayio.Group()
display.rootgroup = splash


font = bitmap_font.load_font("/fonts/PTSans-NarrowBold-40.pcf")
# font = bitmap_font.load_font("/fonts/PT40.pcf")
font_H20 = bitmap_font.load_font("/fonts/H20.pcf")
wrap_with = 240  # in pixel


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

# show Rig Name
text_group_rig = displayio.Group(scale=1)
text1 = "MIDI Captain\nfor Kemper"
text_area_rig = label.Label(font, text="\n".join(wrap_text_to_pixels(text1, wrap_with, font)), color=0xFFFFFF, line_spacing=0.9)
text_area_rig.anchor_point = (0.5, 0.5)
text_area_rig.anchored_position = (120, 120)
text_group_rig.append(text_area_rig)  # Subgroup for text scaling
splash.append(text_group_rig)

# Draw Effect Module A
rect = Rect(1, 200, 120, 40, fill=palette[5], outline=0x0, stroke=1)
splash.append(rect)  # position splash[3] IMPORTANT!

text_group_A = displayio.Group(scale=1, x=1, y=200)
text_A = "Module A"
text_A_area = label.Label(font_H20, text=text_A, color=0x0, anchor_point=(0.5, 0.5), anchored_position=(60, 20))
text_group_A.append(text_A_area)  # Subgroup for text scaling

# Draw Effect Module A
rect = Rect(120, 200, 120, 40, fill=palette[6], outline=0x0, stroke=1)
splash.append(rect)  # position splash[4] IMPORTANT!

text_group_B = displayio.Group(scale=1, x=120, y=200)
text_B = "Module B"
text_B_area = label.Label(font_H20, text=text_B, color=0x0, anchor_point=(0.5, 0.5), anchored_position=(60, 20))
text_group_B.append(text_B_area)  # Subgroup for text scaling

text_group_Log = displayio.Group(scale=1, x=1, y=41)
text_Log = "Wait for connection"
text_Log_area = label.Label(font_H20, text=text_Log, color=0x808080, anchor_point=(1, 0.5), anchored_position=(240, 20))
text_group_Log.append(text_Log_area)


# add  text groups
splash.append(text_group_DLY)
splash.append(text_group_REV)
splash.append(text_group_A)
splash.append(text_group_B)
splash.append(text_group_Log)

# activate Display
display.show(splash)

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


# function to control neopixel segments - color in smaller brightness
def send_beacon():
    text_Log_area.text = 'connection established'
    # Parameter Set 2
    # use Sysex response
    # init off
    # echo off
    # NOFE off
    # NOCTOR on
    # TUNEMODE on
    # -> 0x18
    # send beacon
    midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                  [0x02, 0x7f, 0x7e, 0x00, 0x40, 0x02, 0x32, 0x7f]))
    return

def send_initbeacon():
    text_Log_area.text = 'connection initialization'
    # Parameter Set 2
    # use Sysex response
    # init on
    # echo off
    # NOFE off
    # NOCTOR on
    # TUNEMODE on
    # -> 0x19
    # send beacon
    midi_usb.send(SystemExclusive([0x00, 0x20, 0x33],
                                  [0x02, 0x7f, 0x7e, 0x00, 0x40, 0x02, 0x33, 0x04]))
    con_init = True
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


# set start values
LED.fill(0x000000)  # start using

# Kemper Rig Name
rig_name = ''

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
            else:
                midi_usb.send(ControlChange(27, 0))

    elif switch[1].switch.value is False:
        if pushed is False:
            # [1][SE][0x002033][0x027f41003d03]

            pushed = True
            if switch[1].state == "off":
                midi_usb.send(ControlChange(28, 1))
            else:
                midi_usb.send(ControlChange(28, 0))

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
            else:
                midi_usb.send(ControlChange(17, 0))

    elif switch[4].switch.value is False:
        if pushed is False:
            # [1][SE][0x002033][0x027f41003303]

            pushed = True
            if switch[4].state == "off":
                midi_usb.send(ControlChange(18, 1))
            else:
                midi_usb.send(ControlChange(18, 0))

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
            #text_Log_area.text = '*'
            if isinstance(midimsg, ActiveSensing):
                # use Kemper Midi Active Sensing Message as trigger
                if con_init and not con_established:
                    send_beacon()
                    con_established = True
                if not con_init:
                    send_initbeacon()
                    con_init = True


            if isinstance(midimsg, ControlChange):
                string_msg = 'ControlChange'
                string_val = str(midimsg.control)

            if isinstance(midimsg, ProgramChange):
                string_msg = 'ProgramChange'
                string_val = str(midimsg.patch)
                text_Log_area.text = ''
                                        
                # reset activated 'Booster' on Switch 5
                if switch[5].state == "on":
                    light_dim(5, switch[5].color)
                    switch[5].state = "off"
                    midi_usb.send(ControlChange(7, 1))


            elif isinstance(midimsg, SystemExclusive):
                string_msg = 'SystemExclusive'
                string_val = str(midimsg.data)
                response = list(midimsg.data)

                if response[:-1] == [0x00, 0x00, 0x01, 0x00, 0x7c, 0x00, 0x00]:
                    # TAP Meldung
                    # mit Wechsel von 0 auf 1 an letzter Stelle
                    string_msg = ''
                
                # Rig Name
                elif response[:6] == [0x00, 0x00, 0x03, 0x00, 0x00, 0x01]:

                    ascii_string = ''.join(chr(int(c)) for c in response[6:-1])
                    text_area_rig.text = "\n".join(wrap_text_to_pixels(ascii_string, wrap_with, font))


                elif response[:-4] == [0x00, 0x00, 0x01, 0x00] and len(response) == 8:
                    if response[4] == 0x32:
                        switch_number = switch_a
                    elif response[4] == 0x33:
                        switch_number = switch_b
                    elif response[4] == 0x34:
                        switch_number = switch_c
                    elif response[4] == 0x35:
                        switch_number = switch_d
                    elif response[4] == 0x38:
                        switch_number = switch_x
                    elif response[4] == 0x3a:
                        switch_number = switch_mod
                    elif response[4] == 0x3c:
                        switch_number = switch_dly
                    elif response[4] == 0x3d:
                        switch_number = switch_rev
                    elif response[4] == 0x4a:
                        switch_number = switch_dly
                    elif response[4] == 0x4b:
                        switch_number = switch_rev
                    else:
                        switch_number = 99
                    
                    if (response[5] == 0x00) and (switch_number != 99):   # Effect Type Response

                        # Effect Type in last 2 list elements
                        effecttype = response[-2] * 128 + response[-1]

                        # update Effect Type in Object
                        switch[switch_number].effecttype = effecttype

                        # is Effectslot is empty?
                        if effecttype == 0:
                            light_off(switch_number)
                            if switch_number == 0:
                                text_DLY_area.text = 'Empty'
                                splash[switch_number] = Rect(1, 1, 120, 40, fill=palette[9], outline=0x0, stroke=1)
                            elif switch_number == 1:
                                text_REV_area.text = 'Empty'
                                splash[switch_number] = Rect(120, 1, 120, 40, fill=palette[9], outline=0x0, stroke=1)
                            elif switch_number == 3:
                                splash[switch_number] = Rect(1, 200, 120, 40, fill=palette[9], outline=0x0, stroke=1)
                                text_A_area.text = 'Empty'
                            else:
                                text_B_area.text = 'Empty'
                                splash[switch_number] = Rect(120, 200, 120, 40, fill=palette[9], outline=0x0, stroke=1)

                        else:
                            # update new color in object
                            switch[switch_number].setcolor()
                            
                            if switch_number == 0:
                                text_DLY_area.text = get_module_name(effecttype)
                                splash[switch_number] = Rect(1, 1, 120, 40, fill=palette[switch[switch_number].bitmap_palette_index], outline=0x0, stroke=1)
                            elif switch_number == 1:
                                text_REV_area.text = get_module_name(effecttype)
                                splash[switch_number] = Rect(120, 1, 120, 40, fill=palette[switch[switch_number].bitmap_palette_index], outline=0x0, stroke=1)
                            elif switch_number == 3:
                                splash[switch_number] = Rect(1, 200, 120, 40, fill=palette[switch[switch_number].bitmap_palette_index], outline=0x0, stroke=1)
                                text_A_area.text = get_module_name(effecttype)
                            else:
                                text_B_area.text = get_module_name(effecttype)
                                splash[switch_number] = Rect(120, 200, 120, 40, fill=palette[switch[switch_number].bitmap_palette_index], outline=0x0, stroke=1)

                            # prepare for setting state over SysEx
                            if (switch[switch_number].state == 'na') or (switch[switch_number].state == 'off'):
                                switch[switch_number].state = 'off'
                                light_dim(switch_number, switch[switch_number].color)
                            else:
                                light_active(switch_number, switch[switch_number].color)

                    elif ((response[5] == 0x02) or (response[5] == 0x03)) and (switch_number != 99):   # Effect State Response
                        if  (switch[switch_number].effecttype != 0):
                            if (response[-1] == 0x01):
                                light_active(switch_number, switch[switch_number].color)
                            elif (response[-1] == 0x00):
                                light_dim(switch_number, switch[switch_number].color)
                    else:
                        #nothing to do
                        #text_Log_area.text = 'MIDI Info ' + str(response)
                        string_msg = ''

                else:
                    # every other SysEx mesage
                    print('not yet assignt: ' + str(response))
                    #text_Log_area.text = 'MIDI event ' + str(response)


            elif isinstance(midimsg, MIDIUnknownEvent):
                #text_Log_area.text = 'unkown MIDI event'
                string_msg = ''


            else:
                # not yet assignt midi messages
                string_msg = ''

