from .blauberg_device import BlaubergDevice, Purpose, SinglePointAction, ComplexAction, Component, OptionalAction, variable_to_bytes

smart_wifi = BlaubergDevice(
    name="Blauberg Smart-WIFI",
    parameter_map={
        Purpose.POWER: SinglePointAction(0x01),
        Purpose.FAN_SPEED: ComplexAction(
            parameters=[0x04],
            response_parser=lambda response: response[0x04],
            # Since this fan model doesn't have support for direct fan control
            # we can set the minimum and maximum fan speeds instead
            # and enable 24 hour mode, disable silent mode
            request_parser=lambda input: {0x18: variable_to_bytes(
                input), 0x1A: variable_to_bytes(input), 0x03: 0x01, 0x1E: 0x00},
        ),
        Purpose.MOISTURE_SENSOR: SinglePointAction(0x2e),
        Purpose.TEMPERATURE_SENSOR: SinglePointAction(0x31),
        Purpose.BOOST: SinglePointAction(0x05),
    },
    optional_entity_map=[
        OptionalAction(
            name="Humidity Sensor Trigger Point",
            component=Component.SLIDER,
            action=SinglePointAction(0x14),
        ),
        OptionalAction(
            name="Temperature Sensor Trigger Point",
            component=Component.SLIDER,
            action=SinglePointAction(0x22),
        )
    ],
    attribute_map={},
)
