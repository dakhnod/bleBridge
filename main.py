#!/usr/bin/python3 -u

import ConnectionHandler
import HomieHandler
import yaml
import time
import logging

logging.basicConfig(level=logging.ERROR)

# import pydevd_pycharm
# pydevd_pycharm.settrace('192.168.0.146', port=12345, stdoutToServer=True, stderrToServer=True, suspend=False)

def main():
    homie_handler = HomieHandler.HomieHandler()

    connection_handler = ConnectionHandler.ConnectionHandler()

    def discovery_handler(device):
        homie_handler.handle_device_discovery(device, connection_handler)
    connection_handler.start_discovery(get_addresses(), discovery_handler)
    connection_handler.loop_reconnects()
    while True:
        time.sleep(10)


def get_addresses():
    with open('targets.yaml', 'r') as targets:
        return yaml.safe_load(targets)


if __name__ == '__main__':
    main()
