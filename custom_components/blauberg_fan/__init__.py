"""The blauberg_fan integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    CONF_DEVICES,
    CONF_HOST,
    CONF_PORT,
    CONF_DEVICE_ID,
    CONF_PASSWORD,
    CONF_TYPE,
)


from .blauberg_protocol import BlaubergProtocol
from .blauberg_protocol.devices import devices as blauberg_devices
from .blauberg_coordinator import BlaubergProtocolCoordinator
from .const import DOMAIN, DEVICES, DEVICE_CONFIG, COORDINATOR

import logging

LOG = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.FAN]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up blauberg_fan from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    if DEVICES not in hass.data[DOMAIN]:
        hass.data[DOMAIN][DEVICES] = {}

    for device in entry.data[CONF_DEVICES]:
        blauberg_protocol = BlaubergProtocol(
            device[CONF_HOST],
            device[CONF_PORT],
            device[CONF_DEVICE_ID],
            device[CONF_PASSWORD],
        )
        coordinator = BlaubergProtocolCoordinator(
            hass, blauberg_protocol, device[CONF_TYPE]
        )
        await coordinator.async_config_entry_first_refresh()
        device_config = blauberg_devices.get(device[CONF_TYPE])
        if device_config is not None:
            hass.data[DOMAIN][DEVICES][device[CONF_DEVICE_ID]] = {
                DEVICE_CONFIG: device_config,
                COORDINATOR: coordinator,
            }
            for platform in PLATFORMS:
                hass.async_create_task(
                    hass.config_entries.async_forward_entry_setup(entry, platform)
                )
        else:
            LOG.info("Unkown device type: %s", device[CONF_TYPE])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        if DEVICES in hass.data[DOMAIN]:
            for device in entry.data[CONF_DEVICES]:
                hass.data[DOMAIN][DEVICES].pop(device[CONF_DEVICE_ID])
    return unload_ok
