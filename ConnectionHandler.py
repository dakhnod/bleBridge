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
                if target.get('address_type', 'public') == 'random':
                    address_type = bt.ADDR_TYPE_RANDOM

                device = self.connect_discover_device(target['address'], address_type)

                device['auto_reconnect'] = target.get('auto_reconnect', False)
                device['name'] = target.get('name', 'Unkown')

                print('adding device %s (%s) to addressable devices' % (device['address'], device['name']))

                self.devices.append(device)

                if discover_callback is not None:
                    discover_callback(device)
            except bt.BTLEDisconnectError:
                print('skipping device %s (%s)' % (target['address'], target.get('name', 'Unknown')))

    def start_loop(self):
        threading.Thread(target=self.loop_reconnects).start()

    def loop_reconnects(self):
        while True:
            for device in self.devices:
                try:
                    try:
                        status = device['device'].getState()
                    except:
                        status = None

                    if status != 'conn':
                        has_value = False
                        try:
                            has_value = device['value'] is not None
                        except KeyError:
                            pass

                        if not has_value and not device['auto_reconnect']:
                            continue

                        if device['next_connect'] > time.time():
                            continue

                        print('connecting to %s %s' % (device['address'], device['name']))
                        try:
                            # raise bt.BTLEDisconnectError("test")
                            dev = device['device']
                            dev.connect(dev.addr, device['address_type'])
                            print('connected to %s (%s)' % (device['address'], device['name']))
                        except bt.BTLEDisconnectError:
                            print('failed connecting to %s (%s)' % (device['address'], device['name']))
                            last_pause = device['last_pause']
                            last_pause = min(60, last_pause + 1)
                            print('setting device pause to %i' % last_pause)
                            device['next_connect'] = time.time() + last_pause
                            device['last_pause'] = last_pause
                            continue

                    try:
                        value = device['value']
                        if device['value'] is not None:
                            print('writing queued value')
                            # raise bt.BTLEDisconnectError("test")
                            value['characteristic'].write(value['value'], withResponse=True)
                            device['value'] = None
                    except KeyError:
                        pass
                    except:
                        print('failed write to %s (%s)' % (device['address'], device['name']))
                        device['device'].disconnect()
                except:
                    print("device %s (%s) raised exception" % (device['address'], device['name']))

            self.reconnect_condition.acquire()
            self.reconnect_condition.wait(1)

    def write_value(self, device, characteristic, value):
        with self.write_mutex:
            print('queueing value to %s (%s)' % (device['address'], device['name']))
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
                print('connecting to %s' % (address))
                device = bt.Peripheral(address, addrType=address_type)
                print("connected to %s" % (address))
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
                    'services': services_map,
                    'next_connect': 0,
                    'last_pause': 0
                }
                return device
            except bt.BTLEDisconnectError:
                print('failed to connect to ', address)
                connection_tries = connection_tries - 1
                if connection_tries <= 0:
                    print('connection retries exceeded, stopping')
                    raise
