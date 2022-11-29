import collections

from . import SWM181
from . import SWM190
from . import SWM201
from . import SWM211
from . import SWM220
from . import SWM260
from . import SWM320
from . import SWM320_NOR
from . import SWM341
from . import SWM341_SFC
from . import SRAM_SDRAM


Devices = collections.OrderedDict([
        ('SWM181xB',     SWM181.SWM181xB),
        ('SWM181xC',     SWM181.SWM181xC),
        ('SWM190xB',     SWM190.SWM190xB),
        ('SWM190xC',     SWM190.SWM190xC),
        ('SWM201',       SWM201.SWM201),
        ('SWM211',       SWM211.SWM211),
        ('SWM260',       SWM260.SWM260),
        ('SWM320',       SWM320.SWM320),
        ('SWM341',       SWM341.SWM341),
        ('SWM341_SFC',   SWM341_SFC.SWM341_SFC),
        ('SWM320-S29GL128P (16-bit)',   SWM320_NOR.SWM320_S29GL128P),
        ('SWM320-MX29LV128DB (16-bit)', SWM320_NOR.SWM320_MX29LV128DB),
        ('SWM320-MX29LV128DT (16-bit)', SWM320_NOR.SWM320_MX29LV128DT),
        ('SWM320_RAM',   SRAM_SDRAM.SWM320_SRAM),
        ('SWM320_SDRAM', SRAM_SDRAM.SWM320_SDRAM),
        ('SWM341_RAM',   SRAM_SDRAM.SWM341_SRAM),
        ('SWM341_SDRAM', SRAM_SDRAM.SWM341_SDRAM),
])
