import board
import time
import digitalio

switch2 = digitalio.DigitalInOut(board.GP25)  # change for the final product
switch2.direction = digitalio.Direction.INPUT
switch2.pull = digitalio.Pull.UP

switch3 = digitalio.DigitalInOut(board.GP24)
switch3.direction = digitalio.Direction.INPUT
switch3.pull = digitalio.Pull.UP

switchA = digitalio.DigitalInOut(board.GP9)
switchA.direction = digitalio.Direction.INPUT
switchA.pull = digitalio.Pull.UP

switchB = digitalio.DigitalInOut(board.GP10)
switchB.direction = digitalio.Direction.INPUT
switchB.pull = digitalio.Pull.UP

switchC = digitalio.DigitalInOut(board.GP11)
switchC.direction = digitalio.Direction.INPUT
switchC.pull = digitalio.Pull.UP


print("Press Switch 2 to enter PaintAudio Firmware")
time.sleep(0.05)

firmware_ID = 1

if switch2.value is False:
    switch2.deinit()
    switch3.deinit()
    switchA.deinit()
    switchB.deinit()
    switchC.deinit()

    firmware_ID = 2

    try:
        with open('/res/firmwareid.dat', "r+") as fp4:
            for line2 in fp4:
                if line2.find('FIRMWARE_ID') != (-1):
                    value_bytes = line2[line2.find('['):line2.find(']') + 1]
                    temp_str = '[' + str(firmware_ID) + ']'
                    line3 = line2.replace(value_bytes, temp_str)
                    line4 = line3[0:105]
                    fp4.seek(-len(line2), 1)
                    fp4.write(line4)
    except OSError:
        print('error write files')
        pass

elif switch3.value is False:

    switch2.deinit()
    switch3.deinit()
    switchA.deinit()
    switchB.deinit()
    switchC.deinit()

    firmware_ID = 3

    try:
        with open('/res/firmwareid.dat', "r+") as fp4:
            for line2 in fp4:
                if line2.find('FIRMWARE_ID') != (-1):
                    value_bytes = line2[line2.find('['):line2.find(']') + 1]
                    temp_str = '[' + str(firmware_ID) + ']'
                    line3 = line2.replace(value_bytes, temp_str)
                    line4 = line3[0:105]
                    fp4.seek(-len(line2), 1)
                    fp4.write(line4)
    except OSError:
        print('error write file for ID 3')
        pass

elif switchA.value is False:

    switch2.deinit()
    switch3.deinit()
    switchA.deinit()
    switchB.deinit()
    switchC.deinit()

    firmware_ID = 4

    try:
        with open('/res/firmwareid.dat', "r+") as fp4:
            print('open file')
            for line2 in fp4:
                if line2.find('FIRMWARE_ID') != (-1):
                    value_bytes = line2[line2.find('['):line2.find(']') + 1]
                    temp_str = '[' + str(firmware_ID) + ']'
                    line3 = line2.replace(value_bytes, temp_str)
                    line4 = line3[0:105]
                    fp4.seek(-len(line2), 1)
                    fp4.write(line4)
    except OSError:
        print('error write frimwareID4 files')
        pass

elif switchB.value is False:

    switch2.deinit()
    switch3.deinit()
    switchA.deinit()
    switchB.deinit()
    switchC.deinit()

    firmware_ID = 5

    try:
        with open('/res/firmwareid.dat', "r+") as fp4:
            for line2 in fp4:
                if line2.find('FIRMWARE_ID') != (-1):
                    value_bytes = line2[line2.find('['):line2.find(']') + 1]
                    temp_str = '[' + str(firmware_ID) + ']'
                    line3 = line2.replace(value_bytes, temp_str)
                    line4 = line3[0:105]
                    fp4.seek(-len(line2), 1)
                    fp4.write(line4)
    except OSError:
        print('error write files')
        pass

elif switchC.value is False:

    switch2.deinit()
    switch3.deinit()
    switchA.deinit()
    switchB.deinit()
    switchC.deinit()

    firmware_ID = 6

    try:
        with open('/res/firmwareid.dat', "r+") as fp4:
            for line2 in fp4:
                if line2.find('FIRMWARE_ID') != (-1):
                    value_bytes = line2[line2.find('['):line2.find(']') + 1]
                    temp_str = '[' + str(firmware_ID) + ']'
                    line3 = line2.replace(value_bytes, temp_str)
                    line4 = line3[0:105]
                    fp4.seek(-len(line2), 1)
                    fp4.write(line4)
    except OSError:
        print('error write files')
        pass

else:
    switch2.deinit()
    switch3.deinit()
    switchA.deinit()
    switchB.deinit()
    switchC.deinit()

try:
    with open('/res/firmwareid.dat', 'r') as fp:
        fm_id = fp.read()
        for line in fm_id.split('\n'):
            linedata = line.replace(' ', '')
            itemdata = linedata[0:linedata.find('=')]
            valuedata = linedata[linedata.find('[') + 1:linedata.find(']')]
            if itemdata == 'FIRMWARE_ID':
                firmware_ID = int(valuedata)
                if firmware_ID < 1 or firmware_ID > 10:
                    firmware_ID = 1

except OSError:
    print('error open')
    firmware_ID = 1
    pass

del switch2
del switch3
del switchA
del switchB
del switchC

if firmware_ID == 1:
   import kemperstomp
elif firmware_ID == 2:
   import midicaptain6s_kpp
elif firmware_ID == 3:
   import kemperstomp
elif firmware_ID == 4:
   import kemper_bidirect
elif firmware_ID == 5:
   import kemperstomp
elif firmware_ID == 6:
   import display_test
else:
    import kemperstomp
