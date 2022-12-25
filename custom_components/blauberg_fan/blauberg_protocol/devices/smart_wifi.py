from .blauberg_device import (
    BlaubergDevice,
    Purpose,
    SinglePointAction,
    ComplexAction,
    Component,
    OptionalAction,
    variable_to_bytes,
)
from collections.abc import Mapping

_operation_state_params = [0x0F, 0x11, 0x12, 0x13, 0x1D, 0x1E, 0x05]


def _operation_state_parser(response: Mapping[int, int]) -> str:
    if response.get(0x0F, None) == 1:
        return "humidity_sensor_based"
    if response.get(0x11, None) == 1:
        return "temp_sensor_based"
    if response.get(0x12, None) == 1:
        return "motion_sensor_based"
    if response.get(0x13, None) == 1:
        return "ext_switch_based"
    if response.get(0x1D, None) == 1:
        return "internal_ventilation_based"
    if response.get(0x1E, None) == 1:
        return "silent"
    if response.get(0x05, None) == 1:
        return "boost"
    return "unknown"


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
            # try to write fan speed anyway to have it in the response so it can be
            # parsed, hopefully this will also make it future proof in case of updates
            request_parser=lambda input: {
                0x18: variable_to_bytes(input),
                0x1A: variable_to_bytes(input),
                0x03: 0x01,
                0x1E: 0x00,
                0x04: variable_to_bytes(input),
            },
        ),
        Purpose.MOISTURE_SENSOR: SinglePointAction(0x2E),
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
        ),
    ],
    attribute_map={
        "operating_mode": ComplexAction(
            parameters=_operation_state_params,
            response_parser=_operation_state_parser,
            request_parser=lambda input: {0: variable_to_bytes(input)},
        ),
    },
)
