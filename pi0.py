#!/usr/bin/python
# -*- coding: UTF-8 -*-

#
#    this is an UART-LoRa device and thers is an firmware on Module
#    users can transfer or receive the data directly by UART and dont
#    need to set parameters like coderate,spread factor,etc.
#    |============================================ |
#    |   It does not suport LoRaWAN protocol !!!   |
#    | ============================================|
#
#    This script is mainly for Raspberry Pi 3B+, 4B, and Zero series
#    Since PC/Laptop does not have GPIO to control HAT, it should be configured by
#    GUI and while setting the jumpers,
#    Please refer to another script pc_main.py
#

import sys
import sx126x
import threading
import time
import select
import termios
import tty
from gpiozero import MCP3008
import uuid
from threading import Timer

global offset_frequence
offset_frequence = 18
identifier = uuid.uuid4().hex


def send_deal(node):
    get_rec = ""
    print("")
    print(
        "input a string such as \033[1;32m0,868,Hello World\033[0m,it will send `Hello World` to lora node device of "
        "address 0 with 868M ")
    print("please input and press Enter key:", end='', flush=True)

    while True:
        rec = sys.stdin.read(1)
        if rec is not None:
            if rec == '\x0a': break
            get_rec += rec
            sys.stdout.write(rec)
            sys.stdout.flush()
    print("")
    get_t = get_rec.split(",")

    offset_frequence = int(get_t[1]) - (850 if int(get_t[1]) > 850 else 410)
    #
    # the sending message format
    #
    #         receiving node              receiving node                   receiving node           own high 8bit           own low 8bit                 own
    #         high 8bit address           low 8bit address                    frequency                address                 address                  frequency             message payload
    data = bytes([int(get_t[0]) >> 8]) + bytes([int(get_t[0]) & 0xff]) + bytes([offset_frequence]) + bytes(
        [node.addr >> 8]) + bytes([node.addr & 0xff]) + bytes([node.offset_freq]) + get_t[2].encode()
    print(data)
    node.send(data)
    print('\x1b[2A', end='\r')
    print(" " * 200)
    print(" " * 200)
    print(" " * 200)
    print('\x1b[3A', end='\r')


def get_data(dest, offset, node, data):
    return bytes(
        [dest >> 8]
    ) + bytes(
        [dest & 0xff]
    ) + bytes(
        [offset]
    ) + bytes(
        [node.addr >> 8]
    ) + bytes(
        [node.addr & 0xff]
    ) + bytes(
        [node.offset_freq]
    ) + data.encode()


def join(node):
    content = "JOIN:"+str(identifier)
    data = get_data(0, offset_frequence, node, content)
    node.send(data)


def send_water_level(node, address, water_level):
    content = "WATER:" + str(water_level.value)
    data = get_data(address, offset_frequence, node, content)
    node.send(data)


def main():

    device_address = 1

    tty.setcbreak(sys.stdin.fileno())
    # node = sx126x.sx126x(serial_num = "/dev/ttyS0",freq=433,addr=0,power=22,rssi=False,air_speed=2400,relay=False)
    node = sx126x.sx126x(serial_num="/dev/ttyS0", freq=868, addr=device_address, power=22, rssi=True, air_speed=2400, relay=False)

    time.sleep(0.3)

    # show join
    join(node)

    water_level = MCP3008(0)

    while True:

        address, message, flag = node.receive_gateway()
        if flag:
            message = message[1:]
            message = message.replace("'", "")
            print(message)
            if "ACK-JOIN:" in message:
                # Acknowledge join, change address
                print("Join Acknowledgment")
                prefix, device_id, address = message.split(":")
                if device_id == identifier:
                    device_address = int(address)
                    node.set(
                        node.freq,
                        device_address,
                        node.power,
                        node.rssi
                    )
            elif "WATER" in message:
                print("Getting water level")
                send_water_level(node, address, water_level)


if __name__ == "__main__":
    main()
