import homie

class HomieHandler:
    def handle_device_discovery(self, ble_device, connection_manager):
        device = homie.Device({
            'HOST': 'home',
            'DEVICE_ID': 'ble-' + ble_device['address'].replace(':', '').lower(),
            'DEVICE_NAME': ble_device['name'] if ble_device['name'] is not None else 'BLE ' + ble_device['address'],
            'TOPIC': 'homie_ble',
            'QOS': 0
        })
        for serviceUUID in ble_device['services']:
            service = ble_device['services'][serviceUUID]
            uuid = service['service'].uuid
            common_name = 'Service ' + serviceUUID
            if uuid.commonName is not None:
                common_name = uuid.commonName
            node = device.addNode(serviceUUID, common_name, 'service')

            for characteristic_uuid in service['characteristics']:
                characteristic = service['characteristics'][characteristic_uuid]
                uuid = characteristic.uuid
                common_name = 'Characteristic ' + characteristic_uuid
                if uuid.commonName is not None:
                    common_name = uuid.commonName
                property = node.addProperty(characteristic_uuid, common_name, None, None, None)

                def handle_publish(char):
                    def handle(p, value):
                        value_bytes = bytearray.fromhex(value)
                        connection_manager.write_value(ble_device, char, value_bytes)
                    return handle
                property.settable(handle_publish(characteristic))
        device.setup()
