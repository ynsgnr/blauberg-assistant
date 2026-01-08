"""Config flow for Blauberg Fan Integration."""
from __future__ import annotations

from homeassistant.data_entry_flow import FlowResult
from .blauberg_protocol import BlaubergProtocol
from .blauberg_protocol.devices import devices as blauberg_devices
from typing import Any
from collections.abc import Mapping

from homeassistant.core import HomeAssistant, callback
from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_DEVICE_ID,
    CONF_PASSWORD,
    CONF_TYPE,
)
import voluptuous as vol

from .const import DOMAIN

import logging

LOG = logging.getLogger(__name__)


class FlowException(Exception):
    pass


def _device_from_user_input(
    user_input: Mapping[str, Any], config_data: Mapping[str, Any]
) -> Mapping[str, Any]:
    host = user_input.get(CONF_HOST)
    port = user_input.get(CONF_PORT, BlaubergProtocol.DEFAULT_PORT)
    password = user_input.get(CONF_PASSWORD, BlaubergProtocol.DEFAULT_PWD)
    device_id = user_input.get(CONF_DEVICE_ID)

    if host is None:
        raise FlowException("failed_connection")
    blauberg_device = None
    if device_id is None:
        blauberg_device = BlaubergProtocol.discover_device(host, port, password)
    else:
        blauberg_device = BlaubergProtocol(host, port, device_id, password)
    if blauberg_device is None:
        raise FlowException("failed_connection")

    device_id = blauberg_device.device_id
    device_type = blauberg_device.device_type()

    if device_type not in blauberg_devices:
        raise FlowException("unknown_device")

    return {
        CONF_HOST: host,
        CONF_PORT: port,
        CONF_DEVICE_ID: device_id,
        CONF_PASSWORD: password,
        CONF_TYPE: device_type,
    }


DEVICE_DATA = vol.Schema(
    {
        vol.Optional(
            CONF_HOST,
        ): str,
        vol.Optional(
            CONF_PORT,
        ): vol.All(int, vol.Range(min=1000, max=10000)),
        vol.Optional(
            CONF_DEVICE_ID,
        ): str,
        vol.Optional(
            CONF_PASSWORD,
        ): str,
    }
)


@config_entries.HANDLERS.register(DOMAIN)
class BlaubergConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Blauberg fan config flow"""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return flow options."""
        return BlaubergOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is not None:
            try:
                device_data = _device_from_user_input(user_input, {})
            except FlowException as flow_exception:
                return await self.async_step_user(error=str(flow_exception))
            
            device_id = device_data[CONF_DEVICE_ID]
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(
                title=f"Blauberg {device_id}",
                data=device_data
            )

        return self.async_show_form(
            step_id="user",
            data_schema=DEVICE_DATA,
            errors={"base": self.context.get("error")} if self.context.get("error") else None,
        )


class BlaubergOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        return await self.async_step_user()

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is not None:
            # Update the config entry
            self.hass.config_entries.async_update_entry(
                self._config_entry, data=user_input
            )
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(DEVICE_DATA, self._config_entry.data),
            last_step=True,
        )
