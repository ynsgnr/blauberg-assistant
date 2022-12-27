"""Config flow for Blauberg Fan Integration."""
from __future__ import annotations

from homeassistant.data_entry_flow import FlowResult
from .blauberg_protocol import BlaubergProtocol
from .blauberg_protocol.devices import devices as blauberg_devices
from typing import Any
from collections.abc import Mapping

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_entry_flow
from homeassistant import config_entries
from homeassistant.helpers.selector import (
    SelectSelectorConfig,
    SelectSelectorMode,
    SelectSelector,
)
from homeassistant.const import (
    CONF_DEVICES,
    CONF_HOST,
    CONF_PORT,
    CONF_DEVICE_ID,
    CONF_PASSWORD,
    CONF_TYPE,
    STATE_UNKNOWN,
)
import voluptuous as vol

from .const import DOMAIN

import logging

LOG = logging.getLogger(__name__)


def _device_ids_from_config(config: Mapping[str, Any]) -> list[str]:
    device_ids = []
    device_configs = config.get(CONF_DEVICES, [])
    for device in device_configs:
        device_id = device.get(CONF_DEVICE_ID)
        if device_id is not None:
            device_ids.append(device_id)
    return device_ids


def _devices_description(devices: list[Mapping[str, Any]]) -> dict:
    table = ""
    for device in devices:
        device_id = device[CONF_DEVICE_ID]
        blauberg_device = blauberg_devices.get(device[CONF_TYPE])
        device_type_name = None
        if blauberg_device:
            device_type_name = blauberg_device.name
        table += f"\n{device_id or STATE_UNKNOWN} | {device_type_name or STATE_UNKNOWN} | {device.get(CONF_HOST)}:{device.get(CONF_PORT)}"
    if len(devices) == 0:
        table = "No device found"
    return {"table": table}


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

    device_ids = _device_ids_from_config(config_data)
    if device_id in device_ids:
        pass
        # raise FlowException("already_configured")
    return {
        CONF_HOST: host,
        CONF_PORT: port,
        CONF_DEVICE_ID: device_id,
        CONF_PASSWORD: password,
        CONF_TYPE: device_type,
    }


def _remove_device_id_from_config(
    config_data: dict[str, Any], device_id: str
) -> dict[str, Any]:
    index = 0
    while config_data[CONF_DEVICES][index][CONF_DEVICE_ID] != device_id:
        index += 1
    del config_data[CONF_DEVICES][index]
    return config_data


def _remove_device_form(config_data) -> vol.Schema:
    return vol.Schema(
        {
            vol.Optional(CONF_DEVICE_ID): SelectSelector(
                SelectSelectorConfig(
                    mode=SelectSelectorMode.DROPDOWN,
                    options=_device_ids_from_config(config_data),
                )
            ),
        }
    )


async def _async_has_devices(hass: HomeAssistant) -> bool:
    devices = BlaubergProtocol.discover()
    config = hass.config_entries.async_get_entry(DOMAIN)
    if config is None:
        return False
    device_ids = _device_ids_from_config(config.data)
    devices = list(
        filter(
            lambda device: device.device_id in device_ids,
            devices,
        )
    )
    return len(devices) > 0


config_entry_flow.register_discovery_flow(
    DOMAIN, "Blauberg Fan Integration", _async_has_devices
)

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
    """Blauberg fan config flow, allows configuring multiple devices at once"""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    CONFIG_DATA = vol.Schema({vol.Required(CONF_DEVICES): [DEVICE_DATA]})

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return flow options."""
        return BlaubergOptionsFlow(config_entry)

    def __init__(self):
        self._config_data = self.CONFIG_DATA({CONF_DEVICES: []})
        devices = BlaubergProtocol.discover()
        for device in devices:
            self._config_data[CONF_DEVICES].append(
                {
                    CONF_HOST: device.host,
                    CONF_PORT: device.port,
                    CONF_DEVICE_ID: device.device_id,
                    CONF_PASSWORD: device.password,
                }
            )

    async def async_step_user(self, user_input=None) -> FlowResult:
        return self.async_show_menu(
            step_id="menu",
            description_placeholders=_devices_description(
                self._config_data[CONF_DEVICES]
            ),
            menu_options=["confirm", "add_device", "remove_device"],
        )

    async def async_step_confirm(self, _=None) -> FlowResult:
        if len(self._config_data[CONF_DEVICES]) == 0:
            return self.async_abort(reason="no_device")
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured(
            updates=self._config_data, error="changes_saved"
        )
        return self.async_create_entry(title="", data=self._config_data)

    async def async_step_add_device(
        self, user_input=None, error: str | None = None, previous_input=None
    ) -> FlowResult:
        """Config step to add manually configured device"""
        if user_input is not None:
            if user_input.get(CONF_HOST) is None:
                return await self.async_step_user()
            try:
                device_data = _device_from_user_input(user_input, self._config_data)
            except FlowException as flow_exception:
                return await self.async_step_add_device(
                    error=str(flow_exception), previous_input=user_input
                )
            self._config_data[CONF_DEVICES].append(device_data)
            return await self.async_step_user()

        form = DEVICE_DATA
        if previous_input:
            form = self.add_suggested_values_to_schema(form, previous_input)

        return self.async_show_form(
            step_id="add_device",
            data_schema=form,
            errors={"base": error} if error else None,
        )

    async def async_step_remove_device(self, user_input=None) -> FlowResult:
        """Config step to remove manually configured or automaticly configured device"""
        if user_input is not None:
            if user_input.get(CONF_DEVICE_ID) is not None:
                self._config_data = _remove_device_id_from_config(
                    self._config_data, user_input.get(CONF_DEVICE_ID)
                )
            return await self.async_step_user()

        return self.async_show_form(
            step_id="remove_device", data_schema=_remove_device_form(self._config_data)
        )


class BlaubergOptionsFlow(config_entries.OptionsFlow):
    """Handle a option flow for wiser hub."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self._config_entry = config_entry
        self._config_data = config_entry.data

    async def async_step_init(self, user_input=None) -> FlowResult:
        return self.async_show_menu(
            step_id="menu",
            description_placeholders=_devices_description(
                self._config_data[CONF_DEVICES]
            ),
            menu_options=["confirm", "add_device", "remove_device"],
        )

    async def async_step_confirm(
        self, user_input=None, error: str | None = None
    ) -> FlowResult:
        if len(self._config_data[CONF_DEVICES]) == 0:
            return self.async_abort(reason="no_device")
        self.hass.config_entries.async_update_entry(
            self._config_entry, data=self._config_data
        )
        return self.async_create_entry(title="", data=self._config_data)

    async def async_step_add_device(
        self, user_input=None, error: str | None = None, previous_input=None
    ) -> FlowResult:
        """Config step to add manually configured device"""
        if user_input is not None:
            if user_input.get(CONF_HOST) is None:
                return await self.async_step_init()
            try:
                device_data = _device_from_user_input(user_input, self._config_data)
            except FlowException as flow_exception:
                return await self.async_step_add_device(
                    error=str(flow_exception), previous_input=user_input
                )
            self._config_data[CONF_DEVICES].append(device_data)
            return await self.async_step_init()

        form = DEVICE_DATA
        if previous_input:
            form = self.add_suggested_values_to_schema(form, previous_input)

        return self.async_show_form(
            step_id="add_device",
            data_schema=form,
            errors={"base": error} if error else None,
        )

    async def async_step_remove_device(self, user_input=None) -> FlowResult:
        """Config step to remove manually configured or automaticly configured device"""
        if user_input is not None:
            if user_input.get(CONF_DEVICE_ID) is not None:
                self._config_data = _remove_device_id_from_config(
                    self._config_data, user_input.get(CONF_DEVICE_ID)  # type: ignore
                )
            return await self.async_step_init()

        return self.async_show_form(
            step_id="remove_device",
            data_schema=_remove_device_form(self._config_data),
        )
