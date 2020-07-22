#!/usr/bin/python3.7 -u

import paho.mqtt.client as mqtt
import time

client = mqtt.Client('test')
client.connect('192.168.0.4')

client.publish('homie_test/123/$status', time.asctime(), retain=True)