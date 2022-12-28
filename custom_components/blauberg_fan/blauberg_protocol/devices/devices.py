from collections.abc import Mapping
from .blauberg_device import BlaubergDevice
from .smart_wifi import smart_wifi

devices: Mapping[int, BlaubergDevice] = {0x600: smart_wifi}
