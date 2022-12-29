# Blaueberg Integration for Home Assistant
Home Assistant custom component for Blaueberg devices.

## Supported devices
- [Blauberg Smart Wi-Fi](https://blaubergventilatoren.de/en/product/smart-wifi)

## Untested Features
- You can use optional parameters for devices, but I haven't fully tested the dropdown, button and switch since the only device I have (Blauberg Smart Wi-Fi) only requires sliders to adjust its settings.

## Frequently Asked Questions:
 - Changing fan speed on Blauberg Smart Wi-Fi doesn't have any affect:
   - The fan speed only affects the maximum speed since this device doesn't support direct fan speed control, you can set the preset to temperature trigger and lower the trigger point to minimum to control the fan speed directly
## Development Requirements
- python >= 3.9 [link](https://www.python.org/downloads/release/python-390/)
- homeassistant - `pip install homeassistant` or `py -m pip install homeassistant`
- pytest -  `pip install -U pytest` or `py -m pip install -U pytest`