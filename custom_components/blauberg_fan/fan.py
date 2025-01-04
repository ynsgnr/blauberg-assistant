from __future__ import annotations
from typing import Any
from collections.abc import Mapping

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import CONF_DEVICE_ID, CONF_DEVICES
from .const import DOMAIN, DEVICES, COORDINATOR, DEVICE_CONFIG

from .blauberg_protocol.devices import Purpose, BlaubergDevice
from .blauberg_coordinator import BlaubergProtocolCoordinator

import logging

LOG = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entites = []
    for device in config_entry.data.get(CONF_DEVICES, []):
        device_id = device.get(CONF_DEVICE_ID)
        device = hass.data[DOMAIN][DEVICES].get(device_id)
        blauberg_device: BlaubergDevice = device[DEVICE_CONFIG]
        if (
            Purpose.FAN_SPEED in blauberg_device.parameter_map
            or Purpose.PRESET in blauberg_device.parameter_map
        ):
            blauberg_coordinator: BlaubergProtocolCoordinator = device[COORDINATOR]
            await blauberg_coordinator.async_config_entry_first_refresh()
            entites.append(
                BlaubergFan(blauberg_coordinator, device_id, blauberg_device)
            )
    async_add_entities(entites)


class BlaubergFan(CoordinatorEntity[BlaubergProtocolCoordinator], FanEntity):
    """Blauberg Fan entity"""

    def __init__(
        self,
        coordinator,
        idx,
        blauberg_device: BlaubergDevice,
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self._unique_id = str(idx) + "-fan"
        self._attr_is_on = None
        self._attr_percentage = None
        self._attr_preset_mode = None
        self._attr_preset_modes = []
        self._attr_supported_features = FanEntityFeature(0)
        self._device_name = blauberg_device.name + " Fan"
        self._attr_extra_state_attributes = {
            attr: None for attr in blauberg_device.attribute_map
        }

        self._attr_supported_features |= FanEntityFeature.TURN_ON
        self._attr_supported_features |= FanEntityFeature.TURN_OFF
        if Purpose.FAN_SPEED in blauberg_device.parameter_map:
            self._attr_supported_features |= FanEntityFeature.SET_SPEED

        if Purpose.PRESET in blauberg_device.parameter_map:
            self._attr_supported_features |= FanEntityFeature.PRESET_MODE
            self._attr_preset_modes = list(blauberg_device.presets)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.coordinator.data.get(Purpose.POWER)
        self._attr_percentage = self.coordinator.data.get(Purpose.FAN_SPEED)
        self._attr_preset_mode = self.coordinator.data.get(Purpose.PRESET)
        for key in self._attr_extra_state_attributes:
            self._attr_extra_state_attributes[key] = self.coordinator.data.get(key)
        self.async_write_ha_state()

    @property
    def name(self) -> str:
        return self._device_name

    @property
    def unique_id(self) -> str:
        """Return the unique id."""
        return self._unique_id

    @property
    def is_on(self) -> bool | None:
        return self._attr_is_on

    @property
    def percentage(self) -> int | None:
        return self._attr_percentage

    @property
    def supported_features(self) -> FanEntityFeature:
        return self._attr_supported_features

    @property
    def preset_mode(self) -> str | None:
        return self._attr_preset_mode

    @property
    def preset_modes(self) -> list[str] | None:
        return self._attr_preset_modes

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage == 0:
            await self.async_turn_off()
        elif not self._attr_is_on:
            await self.async_turn_on()
        await self.coordinator.set_speed(percentage)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        await self.coordinator.set_preset(preset_mode)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on fan."""
        if percentage is not None:
            await self.async_set_percentage(percentage)
            return
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
            return
        await self.coordinator.set_power(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off fan."""
        await self.coordinator.set_power(False)

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return the device info."""
        return self.coordinator.device_info

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        return self._attr_extra_state_attributes
