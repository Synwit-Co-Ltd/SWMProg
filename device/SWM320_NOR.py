from .flash import Flash


''' NOR控制器的实现中有：addrpara <= norbyteif ? (addrpara + 1) : (addrpara + 2)，
	因此在做总线读（只支持字模式）data = *((volatile uint32_t *)NORFLM_BASE + i)时，NOR是跳过一个地址读一个地址，即容量减半
	为了让通过寄存器写写入的数据，通过总线读依然能够正确读取，因此通过寄存器写时也要跳过一个地址写一个地址，即NORFL_Write(i*2, WrBuff[i]);
	在当前的算法中，寄存器写操作也是这样操作的：
	for(i=0; data_size>0; data_size-=2,i+=2) {
		NORFC->ADDR = FlashAddr+i;
		NORFC->CMD  = (0x3<<16) | ((*(buf+i+1))<<8) | (*(buf+i));
		... ...
	}
'''


class SWM320_S29GL128P(object):
    CHIP_CORE = 'Cortex-M4'

    PAGE_SIZE = 1024 * 4	# 4K字节，写入NOR后占用4K Word空间，因为是跳过一个字（NOR的字，16位）地址用一个字地址
    SECT_SIZE = 1024 * 64   # Uniform 64 Kword/128 Kbyte Sector Architecture；16位模式下，写入寄存器的是“Word Address”，而非“Byte Address”
    CHIP_SIZE = 0x0800000   # 128Mbit（16M x 8/8M x 16），8M字节，因为是跳过一个字（NOR的字，16位）地址用一个字地址

    def __init__(self, xlink):
        super(SWM320_S29GL128P, self).__init__()

        self.xlink = xlink

        self.xlink.reset()
        self.flash = Flash(self.xlink, SWM320_S29GL128P_flash_algo)

    def sect_erase(self, addr, size):
        self.flash.Init(0, 0, 1)
        for i in range(0, size // self.SECT_SIZE):
            self.flash.EraseSector(addr + self.SECT_SIZE*i)
        self.flash.UnInit(1)

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
        for i in range(0, (size + self.PAGE_SIZE -1) // self.PAGE_SIZE):
            self.flash.Read(addr + self.PAGE_SIZE * i, self.PAGE_SIZE)
            
            bytes = self.xlink.read_mem(self.flash.flash['begin_data'], self.PAGE_SIZE)

            buff.extend([ord(x) for x in bytes])
            

class SWM320_MX29LV128DB(SWM320_S29GL128P):
    SECT_SIZE = 1024 * 32   # 前8扇区为8KB(4KW)、后255扇区为64KB(32KW)

    @classmethod
    def addr2sect(cls, addr, size):
        if addr < 32*1024: sect = addr - (addr % ( 4*1024))
        else:              sect = addr - (addr % (32*1024))

        while sect < addr+size:
            yield sect

            if sect < 32*1024: sect +=  4*1024
            else:              sect += 32*1024

    def sect_erase(self, addr, size):
        self.flash.Init(0, 0, 1)
        for addr in self.addr2sect(addr, size):
            self.flash.EraseSector(addr)
        self.flash.UnInit(1)


class SWM320_MX29LV128DT(SWM320_S29GL128P):
    SECT_SIZE = 1024 * 32   # 前255扇区为64KB(32KW)、后8扇区为8KB(4KW)

    @classmethod
    def addr2sect(cls, addr, size):
        if addr < 32*1024 * 255: sect = addr - (addr % (32*1024))
        else:                    sect = addr - (addr % ( 4*1024))

        while sect < addr+size:
            yield sect

            if sect < 32*1024 * 255: sect += 32*1024
            else:                    sect +=  4*1024

    def sect_erase(self, addr, size):
        self.flash.Init(0, 0, 1)
        for addr in self.addr2sect(addr, size):
            self.flash.EraseSector(addr)
        self.flash.UnInit(1)



SWM320_S29GL128P_flash_algo = {
    'load_address' : 0x20000000,
    'instructions' : [
        0xE00ABE00, 0x062D780D, 0x24084068, 0xD3000040, 0x1E644058, 0x1C49D1FA, 0x2A001E52, 0x4770D1F2,
        0x4770BA40, 0x4770BAC0, 0xD1282A01, 0xF04F4844, 0x620131AA, 0x62420D0A, 0xF64F4B42, 0x601A72FF,
        0x0C096401, 0x03826441, 0xF0406890, 0x60906040, 0x40F0F04F, 0x29006941, 0x6881D0FC, 0x5180F421,
        0x20006081, 0x28641C40, 0x6890DBFC, 0x6080F020, 0xF04F6090, 0x214240C0, 0x210160C1, 0x20006001,
        0x20004770, 0xB5084770, 0x90002000, 0xF04FBD08, 0x610841C0, 0x20A0F44F, 0x68486148, 0xD0FC0780,
        0x07C06848, 0x2001D003, 0x20006048, 0x20024770, 0x20016048, 0xB53C4770, 0xF0202300, 0x9300407F,
        0x0300E9CD, 0x1C409801, 0x28329001, 0x2000DBFA, 0x43C0F04F, 0xE0102501, 0x44049C00, 0x1814611C,
        0xF4448824, 0x615C3440, 0x07A4685C, 0x685CD0FC, 0xD00607E4, 0x1E89605D, 0x29001C80, 0x2000DCEC,
        0x2002BD3C, 0x20016058, 0x2200BD3C, 0x1C52E000, 0xD3FC428A, 0x47704410, 0x2300B570, 0xF04F461E,
        0xE00744C0, 0x0543EB00, 0x61666125, 0xF8226965, 0x1C5B5013, 0x0F51EBB3, 0xEB00D3F4, 0xBD700043,
        0x40010000, 0x40010640, 0x00000000
    ],

    'pc_Init'            : 0x20000029,
    'pc_UnInit'          : 0x20000083,
    'pc_EraseSector'     : 0x2000008F,
    'pc_ProgramPage'     : 0x200000B7,
    'pc_Verify'          : 0x2000010B,
    'pc_EraseChip'       : 0x20000087,
    'pc_BlankCheck'      : 0x12000001F,
    'pc_Read'            : 0x20000119,
    
    'static_base'        : 0x20000800,
    'begin_data'         : 0x20000C00,
    'begin_stack'        : 0x20002000,

    'analyzer_supported' : False,

    # Relative region addresses and sizes
    'ro_start'           : 0x00000000,
    'ro_size'            : 0x00000128,
    'rw_start'           : 0x00000128,
    'rw_size'            : 0x00000004,
    'zi_start'           : 0x0000012C,
    'zi_size'            : 0x00000000,

    # Flash information
    'flash_start'        : 0x61000000,
    'flash_size'         : 0x01000000,
    'flash_page_size'    : 0x00001000,
}
