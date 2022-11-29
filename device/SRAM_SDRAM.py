import ctypes


class SWMXYZ_XRAM(object):
    CHIP_CORE = 'Cortex-M4'

    XRAM_BASE = 0x20000000

    CHIP_SIZE = 0x10000
    PAGE_SIZE = 4096
    SECT_SIZE = 4096

    def __init__(self, xlink):
        super(SWMXYZ_XRAM, self).__init__()

        self.xlink = xlink

        #self.xlink.reset()     # 防止复位 SDRAM 配置
        self.xlink.halt()

    def sect_erase(self, addr, size):
        addr += self.XRAM_BASE

        for i in range(0, size, self.SECT_SIZE):
            print(f'Erase @ 0x{addr + i:08X}')

            for j in range(0, self.SECT_SIZE, 4):
                self.xlink.write_U32(addr + i + j, 0x00000000)

    def chip_write(self, addr, data):
        addr += self.XRAM_BASE

        for i in range(0, len(data), self.PAGE_SIZE):
            print(f'Write @ 0x{addr + i:08X}')

            for j in range(0, self.PAGE_SIZE, 4):
                self.xlink.write_U32(addr + i + j, data[i+j] | (data[i+j+1] << 8) | (data[i+j+2] << 16) | (data[i+j+3] << 24))

    def chip_read(self, addr, size, buff):
        addr += self.XRAM_BASE

        words = self.xlink.read_mem_U32(addr, size // 4)

        for word in words:
            buff.extend([word & 0xFF, (word >> 8) & 0xFF, (word >> 16) & 0xFF, (word >> 24) & 0xFF])



class SWM320_SRAM(SWMXYZ_XRAM):
    CHIP_SIZE = 0x20000


class SWM320_SDRAM(SWMXYZ_XRAM):
    XRAM_BASE = 0x70000000

    CHIP_SIZE = 0x02000000  # 32MB

    def __init__(self, xlink):
        super(SWM320_SDRAM, self).__init__(xlink)

        self.xlink.write_U32(0x40010040, 0xAAAAAAAA)
        self.xlink.write_U32(0x40010044, 0x0000AAAA)
        self.xlink.write_U32(0x40010020, 0xAAAAAAAA)
        self.xlink.write_U32(0x40010640, 0x0000FFFF)
        self.xlink.write_U32(0x40010024, 0x00000AAA)

        self.xlink.write_U32(0x40000008, self.xlink.read_U32(0x40000008) | (1 << 26))

        self.xlink.write_U32(0x78000004, 0x0049DA1B)
        self.xlink.write_U32(0x78000010, 0x00000002)
        self.xlink.write_U32(0x78000008, 0x0000109C)
        while self.xlink.read_U32(0x78000014) == 0: pass


class SWM341_SRAM(SWMXYZ_XRAM):
    CHIP_CORE = 'Cortex-M33'

    CHIP_SIZE = 0x10000


class SWM341_SDRAM(SWMXYZ_XRAM):
    CHIP_CORE = 'Cortex-M33'
    
    XRAM_BASE = 0x80000000

    CHIP_SIZE = 0x02000000  # 32MB
