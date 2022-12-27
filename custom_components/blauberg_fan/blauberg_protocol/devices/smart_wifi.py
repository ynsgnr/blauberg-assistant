from __future__ import annotations
from enum import Enum
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


def _operation_state_response_parser(response: Mapping[int, int | None]) -> str:
    if response.get(0x0F, None) == 1:
        return "humidity_trigger"
    if response.get(0x11, None) == 1:
        return "temp_trigger"
    if response.get(0x12, None) == 1:
        return "motion_trigger"
    if response.get(0x13, None) == 1:
        return "ext_switch_trigger"
    if response.get(0x1D, None) == 1:
        return "internal_ventilation"
    if response.get(0x1E, None) == 1:
        return "silent"
    if response.get(0x05, None) == 1:
        return "boost"
    return "unknown"


def _operation_state_request_parser(
    preset: float | str | int | bool | None,
) -> Mapping[int, int]:
    if isinstance(preset, str):
        return {}
    if preset == "humidity_trigger":
        return {0x0F: 1}
    if preset == "temp_trigger":
        return {0x11: 1}
    if preset == "motion_trigger":
        return {0x12: 1}
    if preset == "ext_switch_trigger":
        return {0x13: 1}
    if preset == "internal_ventilation":
        return {0x1D: 1}
    if preset == "silent":
        return {0x1E: 1}
    if preset == "boost":
        return {0x05: 1}
    return {}


preset_action = ComplexAction(
    parameters=_operation_state_params,
    response_parser=_operation_state_response_parser,
    request_parser=_operation_state_request_parser,
)


smart_wifi = BlaubergDevice(
    name="Blauberg Smart-WIFI",
    parameter_map={
        Purpose.POWER: SinglePointAction(0x01),
        Purpose.FAN_SPEED: ComplexAction(
            parameters=[0x18],
            response_parser=lambda response: response[0x18],
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
        "operating_mode": preset_action,
        "rpm": SinglePointAction(0x04),
    },
)
