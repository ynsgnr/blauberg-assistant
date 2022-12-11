# Blauberg Devices

This module includes specific details for a common integration along all devices making use of blauberg protocol.

It is especially designed for home assistant integration.

## Usage
Since this module is not published yet it only works with relative import, so python console needs to run on the same level as this module's folder

```python
from blauberg_protocol import BlaubergProtocol
from devices import Purpose, devices

discovered = BlaubergProtocol.discover()
my_device = discovered[0]

my_device_details = devices[my_device.device_type()]
power = my_device_details.parameter_map[Purpose.POWER]

response = my_device.read_params(power.params)
parsed_response = power.response_parser(response)

power_off_input = 0
request = power.request_parser(power_off_input)
my_device.write_params(request)
```

## Adding a new device
- Create a new file with basic device name, for example `ecovent.py`
- Create a device object
    ```python
    ecovent = BlaubergDevice(
        name="Blauberg Ecovent",
        # ...
    )
    ```
  - For parameters that require no specific parsing you can make use of single point actions (`SinglePointAction`)
    ```python
    from .blauberg_device import BlaubergDevice, SinglePointAction, Purpose

    ecovent = BlaubergDevice(
        name="Blauberg Ecovent",
        parameter_map={
            Purpose.POWER: SinglePointAction(0x01),
            # TODO add other existing purposes as well
        },
        optional_entity_map=[],
        attribute_map={},
    )
    ```
  - For more complex actions that might require converting data from responses or writing into multiple parameters you can make use of complex actions (`SinglePointAction`):
    ```python
    from .blauberg_device import BlaubergDevice, SinglePointAction, Purpose, ComplexAction

    ecovent = BlaubergDevice(
        name="Blauberg Ecovent",
        parameter_map={
            Purpose.POWER: SinglePointAction(0x01),
            Purpose.FAN_SPEED: ComplexAction(
                parameters=[0x04,0x05],
                response_parser=lambda response: response[0x04],
                request_parser=lambda input: {
                    0x04: 1,
                    0x05: 2,
                },
            ),
            # TODO add other existing purposes as well
        },
        optional_entity_map=[],
        attribute_map={},
    )
    ```
  - Since write request can come from many sources, you can parse input with type checking:
    ```python
                request_parser=lambda input: {
                    0x04: int(input),
                    0x05: int(input),
                },
    ```
    - To make parsing easy you can make use of variable_to_bytes function which parses string to bytes, then int and float to directly to int:
        ```python
        from .blauberg_device import BlaubergDevice, SinglePointAction, Purpose, ComplexAction, variable_to_bytes
        # ....
                    request_parser=lambda input: {
                        0x04: variable_to_bytes(input),
                        0x05: variable_to_bytes(input),
                    },
        ```
- Add optional actions which can be other functions of the device other than given purposes and define their control mechanism
   ```python
    from .blauberg_device import BlaubergDevice, SinglePointAction, Purpose, OptionalAction

    ecovent = BlaubergDevice(
        # ...
        optional_entity_map=[
            OptionalAction(
                name="Humidity Sensor Trigger Point",
                component=Component.SLIDER,
                action=SinglePointAction(0x14),
            ),
        ],
        # ...
    )
    ```
    - You can also define complex actions with parsing logic as an optional parameter
        ```python
                # ...
                    OptionalAction(
                        name="Humidity Sensor Trigger Point",
                        component=Component.SLIDER,
                        action=ComplexAction(
                            parameters=[0x04,0x05],
                            response_parser=lambda response: response[0x04],
                            request_parser=lambda slider_input: {
                                0x04: min(int(slider_input),30),
                                0x05: max(int(slider_input),40),
                            },
                    ),
                # ...
            ```
- Add attribute map which is the read only parameters that can not be controlled and has other purposes than whats defined
   ```python
    from .blauberg_device import BlaubergDevice, SinglePointAction, Purpose, OptionalAction

    ecovent = BlaubergDevice(
        # ...
        attribute_map={
            "operating_mode": SinglePointAction(0x14),
        },
        # ...
    )
    ```
- Add the new device into `devices.py` with device type id. Device type id is the response returned from device for `0xB9` parameter. This parameter address can be different for different devices so check user or integration manual
  ```python
    devices: Mapping[int, BlaubergDevice] = {
        # other devices ...
        0x500: eco_vent,
    }
  ```
  - You can add multiple device type ids if the integration works for multiple device types:
    ```python
        devices: Mapping[int, BlaubergDevice] = {
            # other devices ...
            0x300: eco_vent,
            0x400: eco_vent,
            0x500: eco_vent
        }
    ```