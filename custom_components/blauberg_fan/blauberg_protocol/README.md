# Blauberg Protocol

Implementation of Blauberg custom protocol to be used with fans and climate devices supporting the protocol.

Inspired by [pyEcovent](https://github.com/aglehmann/pyEcovent) and [midea_ac_lan](https://github.com/georgezhao2010/midea_ac_lan)

# Usage
Since this module is not published yet it only works with relative import, so python console needs to run on the same level as this module's folder

```python
from blauberg_protocol import BlaubergProtocol

devices = BlaubergProtocol.discover()

devices[0].read_param(0x01)

devices[0].read_params([0x01,0x02])

devices[0].write_param(0x01,1)

devices[0].write_params({0x01:1,0x02:2})
```

## Direct Usage

```python
device = BlaubergProtocol(host)

device = BlaubergProtocol(host,port,device_id,device_password,timeout)

devices.read_param(0x01)
```

## Advanced Discovery
```python
devices = BlaubergProtocol.discover(port,device_id,device_password,timeout)
```

## Features
- Discover devices in network
- Supports changed device settings, you can overwrite defaults for port, device id and password
- Create devices with direct connection (requires the host, other values are optional)
- Write and read multiple parameters at once