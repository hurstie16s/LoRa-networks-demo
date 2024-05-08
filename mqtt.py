import paho.mqtt.client as mqtt
import time


def main():

    # Set up MQTT
    hostname = "<central_adv_net>"
    broker_port = 1883
    topic = "<adv_net>"

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(hostname, broker_port, 60)


if __name__ == '__main__':
    main()
