import logging

from homeassistant.components.number import NumberEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANURFACER_NAME
from .coordinator import CompitDataUpdateCoordinator
from .helpers import build_entities_for_platform, EntityContext
from .types.DeviceDefinitions import Parameter
from .types.SystemInfo import Device

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    """
    Set up number entities for the Compit integration from a configuration entry.

    This function initializes and adds number entities to Home Assistant based
    on the provided configuration entry and data from the
    CompitDataUpdateCoordinator. It delegates discovery of eligible
    device/parameter combinations to helpers.py for better reuse.
    """
    coordinator: CompitDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    def factory(
            coordinator: CompitDataUpdateCoordinator,
            ctx: EntityContext,
    ) -> "CompitNumber":
        return CompitNumber(
            coordinator=coordinator,
            device=ctx.device,
            parameter=ctx.parameter,
            device_name=ctx.device_name,
        )

    entities = build_entities_for_platform(
        coordinator=coordinator,
        platform=Platform.NUMBER,
        factory=factory,
    )
    async_add_devices(entities)


class CompitNumber(CoordinatorEntity, NumberEntity):

    def __init__(
            self,
            coordinator: CompitDataUpdateCoordinator,
            device: Device,
            parameter: Parameter,
            device_name: str,
    ):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.unique_id = f"number_{device.label}{parameter.parameter_code}"
        self.label = f"{device.label} {parameter.label}"
        self.parameter = parameter
        self.device = device
        self._attr_unit_of_measurement = parameter.unit
        self.device_name = device_name
        self._value = (
            self.coordinator.data[self.device.id]
            .state.get_parameter_value(self.parameter)
            .value
        )

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device.id)},
            "name": self.device.label,
            "manufacturer": MANURFACER_NAME,
            "model": self.device_name,
            "sw_version": "1.0",
        }

    @property
    def name(self):
        return f"{self.label}"

    @property
    def native_value(self):
        return self._value

    @property
    def native_min_value(self):
        if isinstance(self.parameter.min_value, (int, float)):
            return self.parameter.min_value
        return (
            self.coordinator.data[self.device.id]
            .state.get_parameter_value(self.parameter)
            .min
        )

    @property
    def native_max_value(self):
        if isinstance(self.parameter.max_value, (int, float)):
            return self.parameter.max_value
        return (
            self.coordinator.data[self.device.id]
            .state.get_parameter_value(self.parameter)
            .max
        )

    @property
    def native_unit_of_measurement(self):
        return self._attr_unit_of_measurement

    @property
    def extra_state_attributes(self):
        items = []

        items.append(
            {
                "device": self.device.label,
                "device_id": self.device.id,
                "device_class": self.device.class_,
                "device_type": self.device.type,
            }
        )

        return {
            "details": items,
        }

    async def async_set_native_value(self, value: int) -> None:
        try:
            if (
                    await self.coordinator.api.update_device_parameter(
                        self.device.id, self.parameter.parameter_code, value
                    )
                    != False
            ):
                self._value = value
                self.async_write_ha_state()
                await self.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.error(e)
