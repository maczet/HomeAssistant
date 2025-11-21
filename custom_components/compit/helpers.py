# helpers.py
import logging
from dataclasses import dataclass
from typing import Callable, Iterable, List, TypeVar

from homeassistant.const import Platform

from .coordinator import CompitDataUpdateCoordinator
from .sensor_matcher import SensorMatcher
from .types.DeviceDefinitions import Parameter
from .types.SystemInfo import Device

_LOGGER: logging.Logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class EntityContext:
    """Lightweight description for a device/parameter on a specific platform."""

    device: Device
    parameter: Parameter
    device_name: str


def iter_entity_contexts_for_platform(
    coordinator: CompitDataUpdateCoordinator,
    platform: Platform,
) -> Iterable[EntityContext]:
    """Yield EntityContext objects for all devices/parameters matching a platform."""
    for gate in coordinator.gates:
        for device in gate.devices:
            device_definition = next(
                (
                    definition
                    for definition in coordinator.device_definitions.devices
                    if definition.code == device.type
                ),
                None,
            )
            if device_definition is None:
                _LOGGER.debug(
                    "No definition found for device id=%s, type=%s",
                    device.id,
                    device.type,
                )
                continue

            for parameter in device_definition.parameters:
                state_param = coordinator.data[device.id].state.get_parameter_value(
                    parameter
                )
                if SensorMatcher.get_platform(parameter, state_param) == platform:
                    yield EntityContext(
                        device=device,
                        parameter=parameter,
                        device_name=device_definition.name,
                    )


def build_entities_for_platform(
    coordinator: CompitDataUpdateCoordinator,
    platform: Platform,
    factory: Callable[[CompitDataUpdateCoordinator, EntityContext], T],
) -> List[T]:
    """Create entity instances for the given platform using a factory callback."""
    return [
        factory(coordinator, ctx)
        for ctx in iter_entity_contexts_for_platform(coordinator, platform)
    ]
