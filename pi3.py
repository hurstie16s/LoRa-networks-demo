#!/usr/bin/python

import sys
import sx126x
import threading
import time
import select
import termios
import tty
from threading import Timer
import paho.mqtt.client as mqtt

global offset_frequence

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


def ack_join(node, address):
    global nodes
    print("Sending ACK to address ", address)

    new_address = len(nodes) + 2
    nodes.append(new_address)

    message = "ACK-JOIN:" + str(new_address)

    data = get_data(address, offset_frequence, node, message)

    node.send(data)


def request_water_level(node, address):
    global nodes

    data = get_data(address, offset_frequence, node, "WATER")

    node.send(data)


def listen(node, client, topic):
    while True:
        address, content, flag = node.receive_gateway()
        if flag:
            print("Message received")
            print(content)
            if "JOIN" in content:
                print("Device joining")
                ack_join(node, address)
            if "WATER:" in content:
                print("Device water level received")
                content = content[1:]
                prefix, water = content.replace("'", "").split(":")
                water = str(address) + ":" + str(float(water))
                print(water)
                client.publish(topic, water)


def get_water_level(node):
    while True:
        for node_address in nodes:
            print("Getting water level for", node_address)
            request_water_level(node, node_address)
        time.sleep(15)


def main():

    client = mqtt.Client()
    topic = "adv_net"

    tty.setcbreak(sys.stdin.fileno())
    # node = sx126x.sx126x(serial_num = "/dev/ttyS0",freq=433,addr=0,power=22,rssi=False,air_speed=2400,relay=False)
    node = sx126x.sx126x(serial_num="/dev/ttyS0", freq=868, addr=0, power=22, rssi=True, air_speed=2400, relay=False)

    listen_thread = threading.Thread(target=listen, args=(node, client, topic,))
    temp_thread = threading.Thread(target=get_water_level, args=(node,))

    listen_thread.start()
    temp_thread.start()

    listen_thread.join()
    temp_thread.join()


if __name__ == "__main__":
    main()
