
from __future__ import annotations
from typing import Mapping, Sequence, Callable, NamedTuple, Optional, cast
from enum import Enum

''' represents the purpose of a parameter'''


class Purpose(Enum):
    POWER = 1
    FAN_SPEED = 2
    MOISTURE_SENSOR = 3
    TEMPERATURE_SENSOR = 4
    BOOST = 5


''' represents an action that can be done in the fan, it will be used to communicate home assistant interactions to the fan
    int is used here instead of bytes since it is more practical, if needed int can be converted into bytes with int.to_bytes function
'''


class ComplexAction(NamedTuple):
    # parameter numbers to be read, the response will be parsed with the response parser
    parameters: Sequence[int]
    # parses the response returned from the fan, used for parsing the read and write responses
    response_parser: Callable[[Mapping[int, int]], float | str | int]
    # parses the home assistant input to fan request values
    request_parser: Callable[[float | str | int], Mapping[int, int]]


def variable_to_bytes(variable: float | str | int) -> int:
    if type(variable) == float:
        # since float is not supported by the blauberg fans, they are all converted to integers
        return int(variable)
    if type(variable) == str:
        variable = cast(str, variable)
        return int.from_bytes(bytes(variable, 'utf-8'), "big")
    return cast(int, variable)


''' represents an action that can be performed on a single parameter, if mapping between home assistant and fan is 1-1 this function should be used'''


@staticmethod
def SinglePointAction(param: int):
    return ComplexAction(
        parameters=[param],
        response_parser=lambda response: response[param],
        request_parser=lambda input: {param: variable_to_bytes(input)},
    )


''' represents optional entities that can be added to home assistant but not enabled by default'''


class Component(Enum):
    BUTTON = 1
    SWITCH = 2
    SLIDER = 3
    DROPDOWN = 4


class OptionalAction(NamedTuple):
    name: str
    component: Component
    action: ComplexAction
    options: Optional[Sequence[str]] = None  # only valid for dropdown


class BlaubergDevice(NamedTuple):
    name: str
    parameter_map: Mapping[Purpose, ComplexAction]
    optional_entity_map: Sequence[OptionalAction]
    attribute_map: Mapping[str, ComplexAction]
