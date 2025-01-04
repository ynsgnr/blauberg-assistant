from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
    SensorEntityDescription,
)
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import CONF_DEVICE_ID, CONF_DEVICES, PERCENTAGE, UnitOfTemperature
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
        blauberg_coordinator: BlaubergProtocolCoordinator = device[COORDINATOR]
        await blauberg_coordinator.async_config_entry_first_refresh()
        if Purpose.MOISTURE_SENSOR in blauberg_device.parameter_map:
            desc = SensorEntityDescription(
                key="humidity",
                name=blauberg_device.name + " Humidity",
                native_unit_of_measurement=PERCENTAGE,
                device_class=SensorDeviceClass.HUMIDITY,
                state_class=SensorStateClass.MEASUREMENT,
            )
            entites.append(
                BlaubergSensor(
                    blauberg_coordinator, device_id, desc, Purpose.MOISTURE_SENSOR
                )
            )
        if Purpose.TEMPERATURE_SENSOR in blauberg_device.parameter_map:
            desc = SensorEntityDescription(
                key="temp",
                name=blauberg_device.name + " Temperature",
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
            )
            entites.append(
                BlaubergSensor(
                    blauberg_coordinator, device_id, desc, Purpose.TEMPERATURE_SENSOR
                )
            )
    async_add_entities(entites)


class BlaubergSensor(CoordinatorEntity[BlaubergProtocolCoordinator], SensorEntity):
    """Blauberg Fan entity"""

    def __init__(
        self,
        coordinator,
        idx,
        entity_description,
        coordinator_data_key,
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self._unique_id = "%s-%s" % (idx, coordinator_data_key)
        self._latest_value = None
        self.entity_description = entity_description
        self._coordinator_data_key = coordinator_data_key

    @property
    def unique_id(self) -> str:
        """Return the unique id."""
        return self._unique_id

    @property
    def native_value(self) -> int | None:
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
