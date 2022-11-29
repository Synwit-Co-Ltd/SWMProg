import time
import struct

from .flash import Flash

FLASH_DR = 0x50028000
FLASH_AR = 0x50028004
FLASH_ER = 0x50028008       #Erase Request
FLASH_SR = 0x50028020

FLASH_SR_EIP  = (1 <<  0)   #Erase In Progress
FLASH_SR_PIP  = (1 <<  1)   #Program In Progress

FLASH_AR_BUSY = (1 << 16)   #Write Internal Busy


class SWM220(object):
    CHIP_CORE = 'Cortex-M0'

    PAGE_SIZE = 1024
    SECT_SIZE = 1024
    CHIP_SIZE = 0x10000     # 64K

    def __init__(self, xlink):
        super(SWM220, self).__init__()

        self.xlink = xlink

        self.xlink.reset()
        self.flash = Flash(self.xlink, SWM220_flash_algo)

        self.xlink.write_U32(0x5000C000, 1)     #HRC select 24MHz
        self.xlink.write_U32(0x40000000, 4)     #Core Clock select HRC
        
    def sect_erase(self, addr, size):        
        for i in range(0, size // self.SECT_SIZE):
            print(f'Erase @ 0x{addr + self.SECT_SIZE * i:08X}')
            self.xlink.write_U32(FLASH_ER, 0x80000000 | (addr + self.SECT_SIZE * i))
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



SWM220_flash_algo = {
    'load_address' : 0x20000000,
    'instructions' : [
        0xE00ABE00, 0x062D780D, 0x24084068, 0xD3000040, 0x1E644058, 0x1C49D1FA, 0x2A001E52, 0x4770D1F2,
        0x4770BA40, 0x4770BAC0, 0xD1062A01, 0x20004933, 0x05896008, 0x20046088, 0x20006008, 0x20004770,
        0x49304770, 0x6088482E, 0x1C402000, 0xDBFC280A, 0x22052000, 0x1C400412, 0xDBFC4290, 0x60882000,
        0x21014770, 0x430807C9, 0x60884926, 0x07C06A08, 0x6088D1FC, 0xB51F4770, 0x93002300, 0x91019302,
        0x1C499902, 0x290A9102, 0x2101DBFA, 0x430807C9, 0x6048491C, 0xE0199303, 0x93009302, 0x9C027810,
        0x00E41C52, 0x9C0040A0, 0x90004320, 0x1C409802, 0x28049002, 0x9800DBF2, 0x68486008, 0xD4FC03C0,
        0x1F009801, 0x98039001, 0x90031D00, 0x28009801, 0x6A08DCE2, 0xD4FC0780, 0x2000604B, 0xBD10B004,
        0x4604B570, 0xE0052300, 0x78265CD5, 0xD10342B5, 0x1C641C5B, 0xD3F7428B, 0xBD7018C0, 0xE000E100,
        0x80010000, 0x50028000, 0x00000000
    ],

    'pc_Init'            : 0x20000029,
    'pc_UnInit'          : 0x2000003F,
    'pc_EraseSector'     : 0x20000063,
    'pc_ProgramPage'     : 0x20000077,
    'pc_Verify'          : 0x200000E1,
    'pc_EraseChip'       : 0x20000043,
    'pc_BlankCheck'      : 0x12000001F,
    
    'static_base'        : 0x20000600,
    'begin_data'         : 0x20000800,
    'begin_stack'        : 0x20001000,

    'analyzer_supported' : False,

    # Relative region addresses and sizes
    'ro_start'           : 0x00000000,
    'ro_size'            : 0x000000E8,
    'rw_start'           : 0x000000E8,
    'rw_size'            : 0x00000004,
    'zi_start'           : 0x000000EC,
    'zi_size'            : 0x00000000,

    # Flash information
    'flash_start'        : 0x00000000,
    'flash_size'         : 0x00010000,
    'flash_page_size'    : 0x00000400,
}
