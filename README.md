# Blaueberg Integration for Home Assistant
Home Assistant custom component for Blaueberg devices.

## Supported devices
- [Blauberg Smart Wi-Fi](https://blaubergventilatoren.de/en/product/smart-wifi)

## Installation
### HACS

The recommended way of installing this component is using the [Home Assistant Community Store](https://hacs.xyz).
To install the integration follow these steps:

1. Go to the HACS Settings and add the custom repository `ynsgnr/blauberg-assistant` with category "Integration".
2. Open the "Integrations" tab and search for "Blauberg".
3. Follow the instructions on the page to set the integration up.

### Manual installation

Copy the contents of the [custom_components](custom_components) folder to the `custom_components` folder in your Home Assistant config directory.
You may need to create the `custom_components` folder if this is the first integration you're installing.
It should look something like this:

```
├── custom_components
│   └── blauberg_fan
│       ├── __init__.py
│       ├── const.py
│       ├── fan.py
│       ├── manifest.json
.       .
.       .
.       .
```

## Untested Features
- You can use optional parameters for devices, but I haven't fully tested the dropdown, button and switch since the only device I have (Blauberg Smart Wi-Fi) only requires sliders to adjust its settings.
- Multiple devices at once, unfortunately I don't have multiple fans so I wasn't able to test it

## Frequently Asked Questions:
 - Changing fan speed on Blauberg Smart Wi-Fi doesn't have any affect:
   - The fan speed only affects the maximum speed since this device doesn't support direct fan speed control, you can set the preset to temperature trigger and lower the trigger point to minimum to control the fan speed directly
## Development Requirements
- python >= 3.9 [link](https://www.python.org/downloads/release/python-390/)
- homeassistant - `pip install homeassistant` or `py -m pip install homeassistant`
- pytest -  `pip install -U pytest` or `py -m pip install -U pytest`

## Inspired By:
- [Midea AC LAN](https://github.com/georgezhao2010/midea_ac_lan)
- [Wiser Home Assistant Integration](https://github.com/asantaga/wiserHomeAssistantPlatform)
- [EcoVent Home Assistant Integration](https://github.com/49jan/hass-ecovent)