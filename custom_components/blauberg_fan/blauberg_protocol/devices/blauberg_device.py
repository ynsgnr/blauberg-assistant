from __future__ import annotations
from collections.abc import Mapping, Sequence, Callable
from typing import NamedTuple, Optional, cast
from enum import Enum


class Purpose(Enum):
    """represents the purpose of a parameter"""

    POWER = 1
    FAN_SPEED = 2
    MOISTURE_SENSOR = 3
    TEMPERATURE_SENSOR = 4
    BOOST = 5


class ComplexAction(NamedTuple):
    """represents an action that can be done on the fan, it is used to communicate home assistant interactions to the fan
    for parsing lambda function signatures int is used here instead of bytes since it is more practical for most purposes,
    if needed int can be converted into bytes with int.to_bytes function
    """

    # parameter numbers to be read, the response will be parsed with the response parser
    parameters: Sequence[int]
    # parses the response returned from the fan, used for parsing the read and write responses
    response_parser: Callable[[Mapping[int, int]], float | str | int]
    # parses the home assistant input to fan request values
    request_parser: Callable[[float | str | int], Mapping[int, int]]


class Component(Enum):
    BUTTON = 1
    SWITCH = 2
    SLIDER = 3
    DROPDOWN = 4


class OptionalAction(NamedTuple):
    """represents optional actions that can be added to home assistant but not enabled by default"""

    name: str
    component: Component
    action: ComplexAction
    options: Optional[Sequence[str]] = None  # only valid for dropdown


class BlaubergDevice(NamedTuple):
    """represents a blauberg device for home assistant
    it represents home assistant functions to device's parameters mapping
    and allows some custom logic to be implemented for mapping parameters with lambdas"""

    name: str
    parameter_map: Mapping[Purpose, ComplexAction]
    optional_entity_map: Sequence[OptionalAction]
    attribute_map: Mapping[str, ComplexAction]


def variable_to_bytes(variable: float | str | int) -> int:
    if type(variable) == float:
        # since float is not supported by the blauberg fans, they are all converted to integers
        return int(variable)
    if type(variable) == str:
        variable = cast(str, variable)
        return int.from_bytes(bytes(variable, "utf-8"), "big")
    return cast(int, variable)


def SinglePointAction(param: int):
    """represents an action that can be performed on a single parameter, if mapping between home assistant and fan is 1-1 this function should be used"""
    return ComplexAction(
        parameters=[param],
        response_parser=lambda response: response[param],
        request_parser=lambda input: {param: variable_to_bytes(input)},
    )
