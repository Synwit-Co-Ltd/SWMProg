import time

from .flash import Flash

FLASH_CR = 0x44000000
FLASH_GO = 0x44000004   #命令执行寄存器
FLASH_SR = 0x44000008
FLASH_AR = 0x44000014
FLASH_DR = 0x44000018

FLASH_CR_LEN         = lambda len: (len << 0)   # 0表示写256字节（1页）
FLASH_CR_CMD         = lambda cmd: (cmd << 8)
FLASH_CR_FIFO_CLR    = (1 <<23)

FLASH_CMD_READ_STATL = 0x02
FLASH_CMD_READ_STATH = 0x03
FLASH_CMD_READ_DATA  = 0x04
FLASH_CMD_WRITE_PAGE = 0x09
FLASH_CMD_ERASE_SECT = 0x0A
FLASH_CMD_ERASE_CHIP = 0x0D
FLASH_CMD_WRITE_EN   = 0x12
FLASH_CMD_WRITE_DIS  = 0x13

FLASH_SR_WRIP        = (1 << 0)
FLASH_SR_WREN        = (1 << 1)
FLASH_SR_BUSY        = (1 <<16)
FLASH_SR_FIFO_EMPTY  = (1 <<21)
FLASH_SR_FIFO_FULL   = (1 <<23)


class SWM181(object):
    CHIP_CORE = 'Cortex-M0'

    PAGE_SIZE = 256
    SECT_SIZE = 4096
    CHIP_SIZE = 0x1E000     # 120K

    def __init__(self, xlink):
        super(SWM181, self).__init__()

        self.xlink = xlink

        self.xlink.reset()
        self.flash = Flash(self.xlink, SWM181_flash_algo)

        self.xlink.write_U32(0x50009008, 0)     # close WDT

    def wait_ready(self):       #等待准备好
        while self.xlink.read_U32(FLASH_SR) & FLASH_SR_BUSY:
            time.sleep(0.01)

    def wait_cmd_send(self):    #等待写入CR的命令发送到SPI Flash
        self.xlink.write_U32(FLASH_GO, 1)
        while self.xlink.read_U32(FLASH_GO):
            time.sleep(0.001)

    def wait_cmd_done(self):    #等待发送到SPI Flash的命令执行完
        self.xlink.write_U32(FLASH_CR, FLASH_CR_CMD(FLASH_CMD_READ_STATL))
        while True:
            self.wait_cmd_send()
            if not self.xlink.read_U32(FLASH_SR) & (FLASH_SR_WRIP | FLASH_SR_WREN):
                break

    def sect_erase(self, addr, size):
        for i in range(0, size // self.SECT_SIZE):
            print(f'Erase @ 0x{addr + self.SECT_SIZE * i:08X}')
            self.wait_ready()
            self.xlink.write_U32(FLASH_CR, FLASH_CR_CMD(FLASH_CMD_WRITE_EN))
            self.wait_cmd_send()
            self.xlink.write_U32(FLASH_CR, FLASH_CR_CMD(FLASH_CMD_ERASE_SECT))
            self.xlink.write_U32(FLASH_AR, addr + self.SECT_SIZE * i)
            self.wait_cmd_send()
            self.wait_cmd_done()

        self.xlink.write_mem(0x00, [0xFF] * 1024)   # 非Cache模式下：SPI Flash虽已擦除，RAM中的代码依然还在、还会执行

    def chip_write(self, addr, data):
        word2byte = lambda word: [word&0xFF, (word>>8)&0xFF, (word>>16)&0xFF, (word>>24)&0xFF]

        # 'bytes' object does not support item assignment
        data = list(data)
        data[0x20:0x24] = word2byte(0x0B11FFAC)     #标志
        data[0x24:0x28] = word2byte((len(data)+self.SECT_SIZE-1)//self.SECT_SIZE * 4096)
        data = bytes(data)
        
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
        self.wait_ready()
        self.xlink.write_U32(FLASH_CR, FLASH_CR_FIFO_CLR)
        self.xlink.write_U32(FLASH_CR, FLASH_CR_CMD(FLASH_CMD_READ_DATA) | FLASH_CR_LEN(0))     # 连续读
        self.xlink.write_U32(FLASH_AR, addr)
        self.xlink.write_U32(FLASH_GO, 1)
        for i in range((size+3)//4):
            while self.xlink.read_U32(FLASH_SR) & FLASH_SR_FIFO_EMPTY: pass
            word = self.xlink.read_U32(FLASH_DR)
            buff.extend([word&0xFF, (word>>8)&0xFF, (word>>16)&0xFF, (word>>24)&0xFF])

        self.xlink.write_U32(FLASH_CR, FLASH_CR_FIFO_CLR)
        self.xlink.write_U32(FLASH_GO, 0)


class SWM181xB(SWM181):
    CHIP_SIZE = 0x1E000     # 120K


class SWM181xC(SWM181):
    CHIP_SIZE = 0x3E000     # 248K



SWM181_flash_algo = {
    'load_address' : 0x20000000,
    'instructions' : [
        0xE00ABE00, 0x062D780D, 0x24084068, 0xD3000040, 0x1E644058, 0x1C49D1FA, 0x2A001E52, 0x4770D1F2,
        0xD1132A01, 0x200149B4, 0x20006008, 0x280A1C40, 0xF3BFD3FC, 0x49B18F5F, 0x60882000, 0x1E414AB0,
        0x21016011, 0x60880789, 0x600849AE, 0x47702000, 0x2801B5F0, 0x2802D071, 0x2803D07F, 0x4BAAD17D,
        0x24436819, 0x06242501, 0x48A6270E, 0x29034EA7, 0x6819D00C, 0xD0092901, 0x29016841, 0x6025D95E,
        0x6A306065, 0xD0FC07C0, 0xE0626237, 0x6840489D, 0xD92E2801, 0x60982002, 0x6800489A, 0x20410B04,
        0x60050600, 0x25112100, 0xE01906AD, 0x220169C3, 0x43930412, 0x030B61C3, 0x62436203, 0x0B1B69C3,
        0x61C3031B, 0x4E9269C3, 0x61C34333, 0x431369C3, 0x69C261C3, 0xD4FC03D2, 0x03D268AA, 0x1C49D4FC,
        0xD3E342A1, 0x60012100, 0x05C02001, 0x60296028, 0x2000E02F, 0x00812201, 0x188A0752, 0x600A6812,
        0x21011C40, 0x42880289, 0x2000D3F4, 0x281E1C40, 0x487CD3FC, 0x28016840, 0x2002D00C, 0x20006018,
        0x281E1C40, 0x6025D3FC, 0x6A306065, 0xD0FC07C0, 0xE00E6237, 0x60182000, 0xE00EE7F1, 0x28016840,
        0x2002D00D, 0x60256018, 0x6A306065, 0xD0FC07C0, 0x20006237, 0x281E1C40, 0x2000D3FC, 0x2000BDF0,
        0xE7F06018, 0xD0010501, 0x47702001, 0x06892111, 0x03D2688A, 0x2209D4FC, 0x600A0252, 0x604A2201,
        0x07DB684B, 0x2305D1FC, 0x600B025B, 0x604A6148, 0x07C06848, 0x2001D1FC, 0x60080240, 0x6848604A,
        0xD1FC07C0, 0x07806888, 0x4856D1F8, 0x14826801, 0x60011889, 0x47702000, 0x0603B570, 0xD0010E1B,
        0xBD702001, 0x08891CC9, 0x28000089, 0x4B51D106, 0x4B4C6213, 0x6254681C, 0x605C6A94, 0x05ED2501,
        0x069B2311, 0x689C601D, 0xD4FC03E4, 0x02642409, 0x2401601C, 0x685E605C, 0xD1FC07F6, 0x02362609,
        0x601E430E, 0x605C6158, 0x6898E005, 0xD4FC0200, 0x6198CA01, 0x29001F09, 0x6858D1F7, 0xD1FC07C0,
        0x02402001, 0x605C6018, 0x07C06858, 0x6898D1FC, 0xD1F80780, 0x6018601D, 0x2000BD70, 0x21112301,
        0x688A0689, 0xD4FC03D2, 0x02522209, 0x604B600A, 0x07D2684A, 0x2205D1FC, 0x600A0252, 0x614A0302,
        0x684A604B, 0xD1FC07D2, 0x02522201, 0x604B600A, 0x07D2684A, 0x688AD1FC, 0xD1F80792, 0x281F1C40,
        0x2003D3DF, 0x0340491F, 0x20006008, 0x20014770, 0xB5F04770, 0x0E1B0603, 0x2001D001, 0x1CC9BDF0,
        0x00890889, 0xD1042800, 0x62134B1A, 0x681B4B15, 0x23116253, 0x689C069B, 0xD4FC03E4, 0x05ED2501,
        0x136C601D, 0x6158601C, 0x605C2401, 0xE00D2600, 0x02A4689C, 0x6814D4FC, 0x42BC699F, 0x605ED003,
        0x601E601D, 0x1D00BDF0, 0x1F091D12, 0xD1EF2900, 0x601D605E, 0xBDF0601E, 0x40000900, 0x50009000,
        0xE000E180, 0x40000500, 0x40000400, 0x43000040, 0x00000FFF, 0x0B11FFAC, 0x00000000
    ],

    'pc_Init'            : 0x20000021,
    'pc_UnInit'          : 0x20000051,
    'pc_EraseSector'     : 0x20000165,
    'pc_ProgramPage'     : 0x200001B9,
    'pc_Verify'          : 0x20000293,
    'pc_EraseChip'       : 0x2000023B,
    'pc_BlankCheck'      : 0x2000028F,
    'pc_Read'            : 0x12000001F,
    
    'static_base'        : 0x20000600,
    'begin_data'         : 0x20000800,
    'begin_stack'        : 0x20000D00,

    'analyzer_supported' : False,

    # Relative region addresses and sizes
    'ro_start'           : 0x00000000,
    'ro_size'            : 0x000002F8,
    'rw_start'           : 0x000002F8,
    'rw_size'            : 0x00000004,
    'zi_start'           : 0x000002FC,
    'zi_size'            : 0x00000000,

    # Flash information
    'flash_start'        : 0x00000000,
    'flash_size'         : 0x0003E000,
    'flash_page_size'    : 0x00000100,
}
