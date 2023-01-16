import time

from .flash import Flash

FLASH_DR = 0x4004A000
FLASH_AR = 0x4004A004
FLASH_ER = 0x4004A008       # Erase Request
FLASH_PE = 0x4004A00C       # Program Enable
FLASH_SR = 0x4004A018

FLASH_SR_EIP  = (1 <<  0)   # Erase In Progress
FLASH_SR_PIP  = (1 <<  1)   # Program In Progress

FLASH_ER_EREQ = (0xFF<<24)  # Erase Request


class SWM241(object):
    CHIP_CORE = 'Cortex-M0'

    PAGE_SIZE = 1024
    SECT_SIZE = 1024
    CHIP_SIZE = 0x20000     # 128K

    def __init__(self, xlink):
        super(SWM241, self).__init__()

        self.xlink = xlink

        self.xlink.reset()
        self.flash = Flash(self.xlink, SWM241_flash_algo)

        self.xlink.write_U32(0x400AA000, 1)     #HRC select 48MHz
        self.xlink.write_U32(0x40000000, 1)     #Core Clock select HRC

    def sect_erase(self, addr, size):
        for i in range(0, size // self.SECT_SIZE):
            print(f'Erase @ 0x{addr + self.SECT_SIZE * i:08X}')
            self.xlink.write_U32(FLASH_ER, FLASH_ER_EREQ | (addr + self.SECT_SIZE * i))
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



SWM241_flash_algo = {
    'load_address' : 0x20000000,
    'instructions' : [
        0xE00ABE00, 0x062D780D, 0x24084068, 0xD3000040, 0x1E644058, 0x1C49D1FA, 0x2A001E52, 0x4770D1F2,
        0x4770BA40, 0x4770BA40, 0x4770BA40, 0x4770BA40, 0x4770BA40, 0x4770BAC0, 0x4770BAC0, 0x4770BAC0,
        0x4770BAC0, 0x4770BAC0, 0x2A01B510, 0xB672D11E, 0x48202100, 0x600143C9, 0x2255481F, 0x4A1F6202,
        0x62816242, 0x8F4FF3BF, 0x8F6FF3BF, 0xBF00BF00, 0x62412100, 0x62016281, 0x61414819, 0x04406281,
        0x11426881, 0x60814311, 0xF980F000, 0xBD102000, 0x47702000, 0x48134912, 0x20006088, 0xBF004A12,
        0x42901C40, 0xE000DBFB, 0x6988BF00, 0xD1FB07C0, 0x47706088, 0xF000B510, 0x2000F91B, 0xB510BD10,
        0x1DC94613, 0x004A08C9, 0xF0004619, 0x2000F91C, 0x0000BD10, 0xE000E180, 0x40000700, 0xFDFFFFFF,
        0x4004A000, 0xFF01FFFF, 0x00002EE0, 0x250FB570, 0xD2092908, 0x008C6806, 0x43AE40A5, 0x68056006,
        0x431540A2, 0xE00A6005, 0x460C6846, 0x00A43C08, 0x43AE40A5, 0x68456046, 0x431540A2, 0x22036045,
        0x18800212, 0x22016804, 0x4394408A, 0x68026004, 0x431A408B, 0xBD706002, 0xB081B5FF, 0x460E4605,
        0x4C684617, 0x03614868, 0x22011828, 0xD0352800, 0x1A8014CA, 0x1A80D036, 0x4290D03B, 0x6888D105,
        0x43102208, 0x4C5F6088, 0x23013430, 0x46312200, 0xF7FF4620, 0x2001FFBB, 0x2F0140B0, 0x6869D030,
        0x60694381, 0x29019904, 0x1DE1D02E, 0x680A31F9, 0x600A4382, 0x2901990A, 0x1DE1D02C, 0x31FA31FF,
        0x4382680A, 0x2101600A, 0x02899A0B, 0xD0282A01, 0x680A1861, 0x600A4382, 0xBDF0B005, 0x43106888,
        0xE7D26088, 0x22026888, 0x60884310, 0x34104C45, 0x6888E7CB, 0x43102204, 0x4C426088, 0xE7C43420,
        0x43016869, 0xE7CD6069, 0x31F91DE1, 0x4302680A, 0xE7CF600A, 0x31FF1DE1, 0x680A31FA, 0x600A4302,
        0x1861E7D1, 0x4302680A, 0xE7D5600A, 0x23016802, 0x431A408B, 0x47706002, 0x23016802, 0x439A408B,
        0x47706002, 0x23016802, 0x405A408B, 0x47706002, 0x40C86B00, 0x0FC007C0, 0x23104770, 0x4A2B1A9B,
        0x680340DA, 0x4313408A, 0x47706003, 0x1A9B2310, 0x40DA4A26, 0x408A6803, 0x60034393, 0x23104770,
        0x4A221A9B, 0x680340DA, 0x4053408A, 0x47706003, 0x1A9B2310, 0x40DA4A1D, 0x40C86B00, 0x47704010,
        0x00892201, 0x64021808, 0x22004770, 0x18080089, 0x47706402, 0x18080089, 0x22016C01, 0x64011A51,
        0x23104770, 0x4A111A9B, 0xB67240DA, 0x408A6803, 0x60034313, 0x4770B662, 0x1A9B2310, 0x40DA4A0B,
        0x6803B672, 0x4393408A, 0xB6626003, 0x23104770, 0x4A061A9B, 0xB67240DA, 0x408A6803, 0x60034053,
        0x4770B662, 0x400A0000, 0xBFFC0000, 0x0000FFFF, 0xB672B510, 0x4A090A80, 0x444A4907, 0x47906812,
        0x2000B662, 0xB510BD10, 0x4B04B672, 0x685B444B, 0xB6624798, 0xBD102000, 0x0B11FFAC, 0x00000008,
        0x2101B570, 0x68080789, 0x4A774C7A, 0x4D784B77, 0x444C07C0, 0x6810D006, 0xD5010780, 0xE01F6023,
        0xE01D6025, 0x4E746808, 0x0F4006C0, 0x2802D006, 0x2803D006, 0x2804D006, 0xE006D10C, 0xE0096026,
        0xE0076026, 0x6020486D, 0x6025E004, 0x07806810, 0x6023D500, 0x07806808, 0x6820D502, 0x602008C0,
        0x68204967, 0xF8D2F000, 0xBD706060, 0x2001495E, 0x07816008, 0x4302680A, 0x4770600A, 0xF7FFB500,
        0x4859FFF5, 0x22FF6A01, 0x43113202, 0x20006201, 0x00C9217D, 0x1C40BF00, 0xD3FB4288, 0x07882101,
        0x68016041, 0x4391221C, 0x68016001, 0x43112208, 0x68016001, 0x43912202, 0x68016001, 0x00490849,
        0xBD006001, 0xF7FFB500, 0x4847FFD1, 0x30402101, 0x06006101, 0x68016041, 0x4391221C, 0x68016001,
        0x68016001, 0x43912202, 0x68016001, 0x00490849, 0xBD006001, 0x4604B570, 0xFFB8F7FF, 0x23004D41,
        0x2102220F, 0xF7FF4628, 0x2300FE61, 0x2103220F, 0xF7FF4628, 0x4834FE5B, 0x4A3B6A01, 0x62014311,
        0x207D2100, 0xBF0000C0, 0x42811C49, 0x2101D3FB, 0x60410788, 0x221C6801, 0x60014391, 0x220C6801,
        0x60014311, 0x2C002102, 0x6802D003, 0x6002430A, 0x6802E002, 0x6002438A, 0x08496801, 0x60010049,
        0x4921BD70, 0x60082003, 0x68010448, 0x43112201, 0x47706001, 0xF7FFB500, 0x2101FFF4, 0x60410788,
        0x221C6801, 0x60014391, 0x22106801, 0x60014311, 0x22026801, 0x60014311, 0x08496801, 0x60010049,
        0xB500BD00, 0xFF62F7FF, 0x07882101, 0x68016041, 0x4391221C, 0x68016001, 0x43112210, 0x68016001,
        0x43112202, 0x68016001, 0x00490849, 0xBD006001, 0x2001B510, 0x68810780, 0x43111142, 0xF7FF6081,
        0xF7FFFF45, 0xBD10FF0D, 0x400AA000, 0x03197500, 0x018CBA80, 0x00000010, 0x00007D00, 0x016E3600,
        0x000F4240, 0x400A0030, 0x00070002, 0x460BB530, 0x20004601, 0x24012220, 0x460DE009, 0x429D40D5,
        0x461DD305, 0x1B494095, 0x40954625, 0x46151940, 0x2D001E52, 0xBD30DCF1, 0x00000000, 0x110004C1,
        0x11000401, 0x11000451, 0x018CBA80, 0x0000001A
    ],

    'pc_Init'            : 0x20000049,
    'pc_UnInit'          : 0x20000091,
    'pc_EraseSector'     : 0x200000B5,
    'pc_ProgramPage'     : 0x200000BF,
    'pc_Verify'          : 0x12000001F,
    'pc_EraseChip'       : 0x20000095,
    'pc_BlankCheck'      : 0x12000001F,
    'pc_Read'            : 0x12000001F,
    
    'static_base'        : 0x20000558,
    'begin_data'         : 0x20000570,
    'begin_stack'        : 0x20000D70,

    'analyzer_supported' : False,

    # Relative region addresses and sizes
    'ro_start'           : 0x00000000,
    'ro_size'            : 0x00000538,
    'rw_start'           : 0x00000538,
    'rw_size'            : 0x00000018,
    'zi_start'           : 0x00000550,
    'zi_size'            : 0x00000000,

    # Flash information
    'flash_start'        : 0x00000000,
    'flash_size'         : 0x00020000,
    'flash_page_size'    : 0x00000400,
    'sector_sizes': (
        (0x00000, 0x00400),
    )
}
