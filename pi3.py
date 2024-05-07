#!/usr/bin/python

import sys
import sx126x
import threading
import time
import select
import termios
import tty
from threading import Timer

global offset_frequence
global nodes

nodes = []
offset_frequence = 18


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


def ack_join(node, address):
    new_address = len(nodes) + 2
    nodes.append(new_address)

    message = "ACK-JOIN:" + str(new_address)

    data = bytes(
        [address >> 8]
    ) + bytes(
        [address & 0xff]
    ) + bytes(
        [offset_frequence]
    ) + bytes(
        [node.addr >> 8]
    ) + bytes(
        [node.addr & 0xff]
    ) + bytes(
        [node.offset_freq]
    ) + message.encode()

    node.send(data)


def main():
    tty.setcbreak(sys.stdin.fileno())
    # node = sx126x.sx126x(serial_num = "/dev/ttyS0",freq=433,addr=0,power=22,rssi=False,air_speed=2400,relay=False)
    node = sx126x.sx126x(serial_num="/dev/ttyS0", freq=868, addr=0, power=22, rssi=True, air_speed=2400, relay=False)

    while True:
        address, message, flag = node.receive_gateway()
        if flag:
            print("Message received")
            print(message)
            if "JOIN" in message:
                ack_join(node, address)


if __name__ == "__main__":
    main()
