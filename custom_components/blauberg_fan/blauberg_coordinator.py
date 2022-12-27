"""Polling data update coordinator"""
from __future__ import annotations
from datetime import timedelta
import logging
from collections.abc import Mapping, Sequence
from typing import Any

import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .blauberg_protocol import BlaubergProtocol
from .blauberg_protocol.devices import (
    devices as blauberg_devices,
    Purpose,
    ComplexAction,
)

LOG = logging.getLogger(__name__)


SCAN_INTERVAL = timedelta(seconds=5)


class BlaubergProtocolCoordinator(DataUpdateCoordinator):
    """Blauber Protocol coordinator."""

    def __init__(
        self, hass: HomeAssistant, blauberg_protocol: BlaubergProtocol, device_type: int
    ) -> None:
        super().__init__(
            hass,
            LOG,
            name=blauberg_protocol.device_id,
            update_interval=SCAN_INTERVAL,
        )
        self._blauberg_protocol = blauberg_protocol

        self._device = blauberg_devices.get(device_type)
        self._batched_params = []
        if self._device is not None:
            actions = []
            for action in self._device.parameter_map.values():
                actions.append(action)
            for optional_action in self._device.optional_entity_map:
                actions.append(optional_action.action)
            for attribute_action in self._device.attribute_map.values():
                actions.append(attribute_action)

            params_to_read = {}
            for action in actions:
                for param in action.parameters:
                    params_to_read[param] = True

            self._batched_params = list(params_to_read.keys())

    def _filter_response_by_params(
        self, response: dict[int, int | None], params: Sequence[int]
    ) -> Mapping[int, int | None] | None:
        result = {}
        for param in params:
            if param in response:
                result[param] = response[param]
            else:
                return None
        return result

    def _parse_data(self, response: dict[int, int | None]) -> dict[Any, Any]:
        if self._device is None:
            raise UpdateFailed("Device is not recognized")
        result = {}
        for attribute in self._device.attribute_map:
            action = self._device.attribute_map[attribute]
            filtered_response = self._filter_response_by_params(
                response, action.parameters
            )
            if filtered_response is not None:
                result[attribute] = action.response_parser(filtered_response)
        for optional_action in self._device.optional_entity_map:
            action = optional_action.action
            filtered_response = self._filter_response_by_params(
                response, action.parameters
            )
            if filtered_response is not None:
                result[optional_action.name] = action.response_parser(filtered_response)
        for purpose in self._device.parameter_map:
            action = self._device.parameter_map[purpose]
            filtered_response = self._filter_response_by_params(
                response, action.parameters
            )
            if filtered_response is not None:
                result[purpose] = action.response_parser(filtered_response)
        return result

    async def _async_update_data(self):
        async with async_timeout.timeout(BlaubergProtocol.DEFAULT_TIMEOUT):
            response = self._blauberg_protocol.read_params(self._batched_params)
            if response is None:
                raise UpdateFailed("Timeout or wrong auth")
            new_data = self._parse_data(response)
            return new_data

    def _get_device_action(self, purpose: Purpose) -> ComplexAction:
        if self._device is None:
            raise UpdateFailed("Device is not recognized")
        action = self._device.parameter_map.get(purpose)
        if action is None:
            raise UpdateFailed("{purpose} is not found in blauberg device config")
        return action

    async def async_update_data(self, new_data: dict[Any, Any]) -> None:
        """merges existing data with given data, resets intervals and calls listeners"""
        update_data = self.data
        if update_data is None:
            update_data = {}
        update_data = update_data.copy()
        update_data.update(new_data)
        self.async_set_updated_data(update_data)

    async def set_power(self, power: bool):
        """Turns the fan off or on"""
        param_action = self._get_device_action(Purpose.POWER)
        request = param_action.request_parser(power)
        if len(request) > 0:
            response = self._blauberg_protocol.write_params(request)
            await self.async_update_data(self._parse_data(response))

    async def set_speed(self, percentage: int):
        """Sets the fans speed by percentage"""
        param_action = self._get_device_action(Purpose.FAN_SPEED)
        request = param_action.request_parser(percentage)
        if len(request) > 0:
            response = self._blauberg_protocol.write_params(request)
            await self.async_update_data(self._parse_data(response))

    async def set_preset(self, preset: str):
        """Sets the fan preset"""
        param_action = self._get_device_action(Purpose.PRESET_SPEED)
        request = param_action.request_parser(preset)
        if len(request) > 0:
            response = self._blauberg_protocol.write_params(request)
            await self.async_update_data(self._parse_data(response))
