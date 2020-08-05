import bluepy.btle as bt
import uuid
import time
import threading


class ConnectionHandler:
    def __init__(self, connection_state_callback=None):
        self.devices = []
        self.connection_state_callback = connection_state_callback
        self.reconnect_condition = threading.Condition()
        self.write_mutex = threading.Lock()

    def start_discovery(self, targets, discover_callback=None):
        for target in targets:
            try:
                address_type = bt.ADDR_TYPE_PUBLIC
                try:
                    if target['address_type'] == 'random':
                        address_type = bt.ADDR_TYPE_RANDOM
                except KeyError:
                    pass

                device = self.connect_discover_device(target['address'], address_type)
                try:
                    device['auto_reconnect'] = target['auto_reconnect']
                except KeyError:
                    device['auto_reconnect'] = False

                try:
                    device['name'] = target['name']
                except KeyError:
                    device['name'] = None

                self.devices.append(device)

                if discover_callback is not None:
                    discover_callback(device)
            except bt.BTLEDisconnectError:
                print('skipping device' + target['address'])

    def start_loop(self):
        threading.Thread(target=self.loop_reconnects).start()

    def loop_reconnects(self):
        while True:
            for device in self.devices:
                status = device['device'].getState()

                if device['connecting']:
                    print('device ' + device['address'] + ' already connecting')
                    continue

                if status != 'conn':
                    has_value = False
                    try:
                        has_value = device['value'] is not None
                    except KeyError:
                        pass

                    if not has_value and not device['auto_reconnect']:
                        continue

                    device['connecting'] = True

                    for i in range(10):
                        print('connecting to ' + device['address'])
                        try:
                            dev = device['device']
                            dev.connect(dev.addr, device['address_type'])
                            print('connected to ' + device['address'])
                            break
                        except bt.BTLEDisconnectError:
                            print('failed connecting to ' + device['address'] + ', attempt ' + str(i))
                            if i == 9:
                                print('whatever, resetting saved value')
                                device['value'] = None
                    device['connecting'] = False

                try:
                    value = device['value']
                    if device['value'] is not None:
                        print('writing queued value')
                        value['characteristic'].write(value['value'], withResponse=True)
                        device['value'] = None
                except KeyError:
                    pass
                except bt.BTLEDisconnectError:
                    print("device disconnected")

            self.reconnect_condition.acquire()
            self.reconnect_condition.wait(1)

    def write_value(self, device, characteristic, value):
        with self.write_mutex:
            print('queueing value to ' + device['address'])
            device['value'] = {
                'characteristic': characteristic,
                'value': value
            }
            self.reconnect_condition.acquire()
            self.reconnect_condition.notify(1)
            self.reconnect_condition.release()

    def connect_discover_device(self, address, address_type):
        connection_tries = 20
        while True:
            try:
                print("connecting to ", address)
                device = bt.Peripheral(address, addrType=address_type)
                print("connected to ", address)
                device.getState()
                services = device.getServices()
                services_map = {}
                for service in services:
                    uuid_string_service = str(uuid.UUID(bytes=service.uuid.binVal))
                    # print("discovered service ", uuid_string_service)
                    characteristics = service.getCharacteristics()

                    characteristics_map = {}

                    for characteristic in characteristics:
                        uuid_string = str(uuid.UUID(bytes=characteristic.uuid.binVal))
                        # print("   discovered cahracteristic ", uuid_string)
                        characteristics_map[uuid_string] = characteristic

                    services_map[uuid_string_service] = {
                        'service': service,
                        'characteristics': characteristics_map
                    }
                device = {
                    'address': device.addr,
                    'address_type': address_type,
                    'device': device,
                    'connecting': False,
                    'services': services_map
                }
                return device
            except bt.BTLEDisconnectError:
                print('failed to connect to ', address)
                connection_tries = connection_tries - 1
                if connection_tries <= 0:
                    print('connection retries exceeded, stopping')
                    raise
