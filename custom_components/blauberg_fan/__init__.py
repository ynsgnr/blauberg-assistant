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
    STATE_UNKNOWN,
)


from .blauberg_protocol import BlaubergProtocol
from .blauberg_protocol.devices import devices as blauberg_devices

from .const import DOMAIN

import logging

LOG = logging.getLogger(__name__)


# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.FAN]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up blauberg_fan from a config entry."""

    LOG.info("Blauberg config: %s", str(entry.data))

    hass.data.setdefault(DOMAIN, {})

    for device in entry.data[CONF_DEVICES]:
        hass.data[DOMAIN][device[CONF_DEVICE_ID]] = BlaubergProtocol(
            device[CONF_HOST],
            device[CONF_PORT],
            device[CONF_PASSWORD],
            device[CONF_DEVICE_ID],
        )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        for device in entry.data[CONF_DEVICES]:
            hass.data[DOMAIN].pop(device[CONF_DEVICE_ID])
    return unload_ok
