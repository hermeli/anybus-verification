#!/usr/bin/python3
# CRC32 pre-calculated from http://www.sunshine2k.de/coding/javascript/crc/crc_js.html (CRC32_BZIP2, POLY:0x4C11DB7, INIT=0xFFFFFFFF, FINAL=0xFFFFFFFF)
import logging,time,sys,gpio
from spi import *
spi = SPI("/dev/spidev2.0")

logging.basicConfig(format='%(asctime)s %(message)s',datefmt="%H:%M:%S",level=logging.INFO)

# Pins
nRESET_OUT = 128
nIRQ_ANY = 25

# Message byte indices
CMD=18
OBJ=15
INST=16
CMDE=20
DAT0=22
DAT1=23

""" function BytesToHex(Bytes) """
def BytesToHex(Bytes):
	return ''.join(["0x%02X " % x for x in Bytes]).strip()

# Setup GPIO ports
gpio.setup(nRESET_OUT,gpio.OUT)
gpio.setup(nIRQ_ANY,gpio.IN)

print("Performing AnyBus module reset...")
gpio.output(nRESET_OUT,0)
time.sleep(0.1)

nIRQ = gpio.input(nIRQ_ANY)
if nIRQ == 0: 
	logging.error("Error: nIRQ is already active!")

gpio.output(nRESET_OUT,1)

while True: 
	nIRQ = gpio.input(nIRQ_ANY)
	if nIRQ == 0: break

print("AnyBus module is ready (nIRQ active)...")
time.sleep(1.5)

# AnyBus Module Type Request
spi.mode=SPI.MODE_0
spi.bits_per_word = 8
spi.speed = 500000

print('SendData   :  CTRL|----|MLEN|MLEN|PLEN|PLEN|STAT|INTM|SIZE|SIZE|----|----|SRC |OBJ |INST|INST|CMD |----|CMDE|CMDE|----|----|----|----|CRC |CRC |CRC |CRC |----|----')
print('ReceiveData:  ----|----|LEDS|LEDS|ANBS|SPIS|TIME|TIME|TIME|TIME|SIZE|SIZE|----|----|SRC |OBJ |INST|INST|CMD |----|CMDE|CMDE|DAT0|DAT1|----|----|CRC |CRC |CRC |CRC')
print('')

# Query Module Type (expected: 0x03, 0x04)
# ==> CMD:0x41, CMDE:1, OBJ:1, INST:1
#    CTRL|----|MLEN|MLEN|PLEN|PLEN|STAT|INTM|SIZE|SIZE|----|----|SRC |OBJ |INST|INST|CMD |----|CMDE|CMDE|----|----|----|----|CRC |CRC |CRC |CRC |----|----
TX1=[0x1C,0x00,0x08,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x03,0x01,0x01,0x00,0x41,0x00,0x01,0x00,0x00,0x00,0x00,0x00,0x96,0xF2,0x16,0xE9,0x00,0x00]
TX2=[0x84,0x00,0x08,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x03,0x01,0x01,0x00,0x41,0x00,0x01,0x00,0x00,0x00,0x00,0x00,0xB3,0x96,0xD4,0xDD,0x00,0x00]

# Expected response
# ----|----|LEDS|LEDS|ANBS|SPIS|TIME|TIME|TIME|TIME|SIZE|SIZE|----|----|SRC |OBJ |INST|INST|CMD |----|CMDE|CMDE|DAT0|DAT1|----|----|CRC |CRC |CRC |CRC
# 0x00 0x00 0x00 0x00 0x00 0x1E 0x08 0x3B 0x49 0x73 0x02 0x00 0x00 0x00 0x03 0x01 0x01 0x00 0x01 0x00 0x01 0x00 0x03 0x04 0x00 0x00 0x8D 0xAB 0x03 0x95

# Query Module Revision (expected: 0x04)
# ==> CMD:0x41, CMDE:2, OBJ:1, INST:0
#    CTRL|----|MLEN|MLEN|PLEN|PLEN|STAT|INTM|SIZE|SIZE|----|----|SRC |OBJ |INST|INST|CMD |----|CMDE|CMDE|----|----|----|----|CRC |CRC |CRC |CRC |----|----
TX3=[0x1C,0x00,0x08,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x04,0x01,0x00,0x00,0x41,0x00,0x02,0x00,0x00,0x00,0x00,0x00,0x2C,0xDA,0x08,0x14,0x00,0x00]
TX4=[0x84,0x00,0x08,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x04,0x01,0x00,0x00,0x41,0x00,0x02,0x00,0x00,0x00,0x00,0x00,0x09,0xBE,0xCA,0x20,0x00,0x00]    

# First we have to issue dummy transmissions
RX = spi.transfer(TX1)
RX = spi.transfer(TX2)

RX = spi.transfer(TX1)
print('SendData   :  '+BytesToHex(TX1))

RX = spi.transfer(TX2)
print('ReceiveData:  '+BytesToHex(RX))
time.sleep(0.1)

if RX[CMD]==1 and RX[CMDE]==1 and RX[OBJ]==1 and RX[INST]==1 and RX[DAT0]==0x03 and RX[23]==0x04:
    print("==> AnyBus Module Type: ",hex(RX[DAT0]),hex(RX[DAT1]))
else:
    print("Error: No AnyBus module type found!")
print('')

RX = spi.transfer(TX3)
print('SendData   :  '+BytesToHex(TX2))
RX = spi.transfer(TX4)
print('ReceiveData:  '+BytesToHex(RX))
time.sleep(0.1)

if RX[CMD]==1 and RX[CMDE]==2 and RX[OBJ]==1 and RX[INST]==0:
    print("==> AnyBus Module Revision: ",hex(RX[DAT0]))
else:
    print("Error: No AnyBus module revision found!")

