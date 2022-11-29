import time

from .flash import Flash

FLASH_DR = 0x4004A000
FLASH_AR = 0x4004A004
FLASH_ER = 0x4004A008       #Erase Request
FLASH_SR = 0x4004A020

FLASH_SR_EIP  = (1 <<  0)   #Erase In Progress
FLASH_SR_PIP  = (1 <<  1)   #Program In Progress

FLASH_AR_BUSY = (1 << 30)   #Write Internal Busy
FLASH_AR_WREN = (1 << 31)

FLASH_ER_SECT = 10
FLASH_ER_EREQ = (1 << 31)   #Erase Request


class SWM260(object):
    CHIP_CORE = 'Cortex-M0'

    PAGE_SIZE = 2048
    SECT_SIZE = 2048
    CHIP_SIZE = 0x20000     # 128K

    def __init__(self, xlink):
        super(SWM260, self).__init__()

        self.xlink = xlink

        self.xlink.reset()
        self.flash = Flash(self.xlink, SWM260_flash_algo)

        self.xlink.write_U32(0x400AA000, 1)     #HRC select 24MHz
        self.xlink.write_U32(0x40000000, 1)     #Core Clock select HRC

        self.xlink.write_U32(0x4004A00C, 0)     #将逻辑地址0x000-0x800映射到物理地址0x000-0x800

    def sect_erase(self, addr, size):        
        for i in range(0, size // self.SECT_SIZE):
            print(f'Erase @ 0x{addr + self.SECT_SIZE * i:08X}')
            self.xlink.write_U32(FLASH_ER, FLASH_ER_EREQ | (((addr + self.SECT_SIZE * i) >> 11) << FLASH_ER_SECT))
            while self.xlink.read_U32(FLASH_SR) & FLASH_SR_EIP: time.sleep(0.01)
        self.xlink.write_U32(FLASH_ER, 0)

    def chip_write(self, addr, data):
        self.flash.Init(0, 0, 1)
        for i in range(0, len(data) // self.SECT_SIZE):
            self.flash.EraseSector(addr + self.SECT_SIZE*i)
        self.flash.UnInit(1)

        self.flash.Init(0, 0, 2)
        for i in range(0, len(data) // self.PAGE_SIZE):
            self.flash.ProgramPage(addr + self.PAGE_SIZE*i, data[self.PAGE_SIZE*i : self.PAGE_SIZE*(i+1)])
        self.flash.UnInit(2)

        self.flash.Init(0, 0, 3)
        for i in range(0, len(data) // self.PAGE_SIZE):
            self.flash.Verify(addr + self.PAGE_SIZE*i, data[self.PAGE_SIZE*i : self.PAGE_SIZE*(i+1)])
        self.flash.UnInit(3)

    def chip_read(self, addr, size, buff):
        data = self.xlink.read_mem(addr, size)

        buff.extend(list(data))


SWM260_flash_algo = {
    'load_address' : 0x20000000,
    'instructions' : [
        0xE00ABE00, 0x062D780D, 0x24084068, 0xD3000040, 0x1E644058, 0x1C49D1FA, 0x2A001E52, 0x4770D1F2,
        0xD1112A01, 0x21004843, 0x618160C1, 0x1C402000, 0xD3FC280A, 0x8F5FF3BF, 0x4A3F2000, 0x601043C0,
        0x07802001, 0x60C16081, 0x47702000, 0x47702000, 0xD0010541, 0x47702001, 0x6A0A4936, 0xDAFC2A00,
        0x0840223F, 0x40100292, 0x18800552, 0x6A086088, 0xD5FC06C0, 0x22106A08, 0x62084310, 0x07C06A08,
        0x6088D1FC, 0xB5104770, 0xD0010543, 0xBD102001, 0x08891CC9, 0x4B270089, 0x2C006A1C, 0x03C4DAFC,
        0x0BE42001, 0x182007C0, 0xE0076058, 0x60186810, 0x0F806858, 0xD1FB07C0, 0x1F091D12, 0xD1F52900,
        0x07006A18, 0x6A18D5FC, 0x43082108, 0x6A186218, 0xD4FC0780, 0x60582000, 0x4816BD10, 0x29006A01,
        0x4916DAFC, 0x6A016081, 0xD5FC06C9, 0x22106A01, 0x62014311, 0x07C96A01, 0x6081D1FC, 0x47702000,
        0x47702001, 0x0543B510, 0x2001D001, 0x1CC9BD10, 0x00890889, 0x6A1C4B07, 0xDAFC2C00, 0x6813E006,
        0x42A36804, 0x1D00D1F2, 0x1F091D12, 0xD1F62900, 0x0000BD10, 0x4004A000, 0xE000E180, 0x80010000,
        0x00000000
    ],

    'pc_Init'            : 0x20000021,
    'pc_UnInit'          : 0x2000004D,
    'pc_EraseSector'     : 0x20000051,
    'pc_ProgramPage'     : 0x20000087,
    'pc_Verify'          : 0x20000105,
    'pc_EraseChip'       : 0x200000DB,
    'pc_BlankCheck'      : 0x20000101,
    'pc_Read'            : 0x12000001F,
    
    'static_base'        : 0x20000600,
    'begin_data'         : 0x20000800,
    'begin_stack'        : 0x20001400,

    'analyzer_supported' : False,

    # Relative region addresses and sizes
    'ro_start'           : 0x00000000,
    'ro_size'            : 0x00000120,
    'rw_start'           : 0x00000120,
    'rw_size'            : 0x00000004,
    'zi_start'           : 0x00000124,
    'zi_size'            : 0x00000000,

    # Flash information
    'flash_start'        : 0x00000000,
    'flash_size'         : 0x00020000,
    'flash_page_size'    : 0x00000800,
}
