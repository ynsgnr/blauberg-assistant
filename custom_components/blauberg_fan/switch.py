from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import CONF_DEVICE_ID, CONF_DEVICES
from .const import DOMAIN, DEVICES, COORDINATOR, DEVICE_CONFIG

from .blauberg_protocol.devices import Component, BlaubergDevice
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
        blauberg_coordinator: BlaubergProtocolCoordinator = device[COORDINATOR]
        await blauberg_coordinator.async_config_entry_first_refresh()
        for extra_param in blauberg_device.extra_parameters:
            if extra_param.component == Component.SWITCH:
                entites.append(
                    BlaubergSwitch(
                        blauberg_coordinator,
                        device_id,
                        extra_param.name,
                        extra_param.identifier,
                    )
                )
    async_add_entities(entites)


class BlaubergSwitch(CoordinatorEntity[BlaubergProtocolCoordinator], SwitchEntity):
    """Blauberg Fan entity"""

    def __init__(
        self,
        coordinator,
        idx,
        name,
        identifier,
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self._unique_id = "%s-%s" % (idx, identifier)
        self._latest_value = None
        self._coordinator_data_key = name
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique id."""
        return self._unique_id

    @property
    def is_on(self) -> bool | None:
        return self._latest_value

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._latest_value = self.coordinator.data.get(self._coordinator_data_key)
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return the device info."""
        return self.coordinator.device_info

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        await self.coordinator.set_optional_param(self._name, True)

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        await self.coordinator.set_optional_param(self._name, False)
