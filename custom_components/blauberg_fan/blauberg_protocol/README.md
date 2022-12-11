# Blauberg Protocol

Implementation of Blauberg custom protocol to be used with fans and climate devices supporting the protocol.

Inspired by [pyEcovent](https://github.com/aglehmann/pyEcovent) and [midea_ac_lan](https://github.com/georgezhao2010/midea_ac_lan)

# Usage
Since this module is not published yet it only works with relative import, so python console needs to run on the same level as this module's folder

```python
from blauberg_protocol import BlaubergProtocol

devices = BlaubergProtocol.discover()

devices.read_param(0x01)

devices.read_params([0x01,0x02])

devices.write_param(0x01,1)

devices.write_params({0x01:1,0x02:2})
```

## Direct Usage

```python
device = BlaubergProtocol(host)

device = BlaubergProtocol(host,port,device_id,device_password,timeout)
```

## Advanced Discovery
```python
devices = BlaubergProtocol.discover(port,device_id,device_password,timeout)
```

## Features
- Discover devices in network (only if they still have the default password)
- Create devices with direct connection (requires the host, other values are optional)
- Write and read multiple parameters at once