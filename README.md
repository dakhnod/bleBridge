# bleBridge
MQTT to BLE Bridge


This bridge allows writing to BLE devices through MQTT/Homie.
I developed it to be able to communicate with my Eqiva cc-rt-ble-eq thermostats from Openhab.
It runs on a Raspberry Pi zero W.

As seen in targets.yaml, each device has to be configured.
After that, it be discovered and presented as a Homie device (Openhab inbox),
exposing all services as nodes and characteristics as properties.

Currently, characteristics can only be written to, reading is not supported.

Also, installation is not optimized, since currently I am the only one using it.

If anyone is interested in using the bridge just open an issue.
