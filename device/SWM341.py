import time

from .flash import Flash


FLASH_ER = 0x4004A008       # Erase Request
FLASH_CA = 0x4004A00C       # Cache Control
FLASH_SR = 0x4004A024

FLASH_ER_REQ = (0x1F<<27)

FLASH_CA_CLR = (1 <<18)     # D-Cache Clear

FLASH_SR_EIP = (1 << 0)     # Erase In Progress
FLASH_SR_PIP = (1 << 1)     # Program In Progress


class SWM341(object):
    CHIP_CORE = 'Cortex-M4'

    PAGE_SIZE = 1024
    SECT_SIZE = 4096
    CHIP_SIZE = 0x80000     # 512K

    def __init__(self, xlink):
        super(SWM341, self).__init__()

        self.xlink = xlink

        self.xlink.reset()

        self.xlink.write_U32(0x400A0808, 0)     # Close WDT
        
        self.xlink.write_U32(0x400AA000, 5)     # HRC select 20MHz
        self.xlink.write_U32(0x40000000, 1)     # Core Clock select HRC

        self.flash = Flash(self.xlink, SWM341_flash_algo)

    def chip_erase(self):
        self.flash.Init(0, 0, 1)
        self.flash.EraseChip()
        self.flash.UnInit(1)
    
    def sect_erase(self, addr, size):
        for i in range(0, size // self.SECT_SIZE):
            print(f'Erase @ 0x{addr + self.SECT_SIZE * i:08X}')
            self.xlink.write_U32(FLASH_ER, FLASH_ER_REQ | (addr + self.SECT_SIZE * i))
            while self.xlink.read_U32(FLASH_SR) & FLASH_SR_EIP: time.sleep(0.001)
        self.xlink.write_U32(FLASH_ER, 0)

        self.xlink.write_U32(FLASH_CA, self.xlink.read_U32(FLASH_CA) | FLASH_CA_CLR)

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
        self.xlink.write_U32(FLASH_CA, self.xlink.read_U32(FLASH_CA) | FLASH_CA_CLR)
        
        data = self.xlink.read_mem(addr, size)

        buff.extend(list(data))



SWM341_flash_algo = {
    'load_address' : 0x20000000,
    'instructions' : [
        0xE00ABE00, 0x062D780D, 0x24084068, 0xD3000040, 0x1E644058, 0x1C49D1FA, 0x2A001E52, 0x4770D1F2,
        0xD13D2A01, 0x1080F24E, 0x8210F3EF, 0xF2CEB672, 0xF04F0000, 0x600131FF, 0x60816041, 0xF2C42008,
        0x22550000, 0x2718F8C0, 0x7224F240, 0x0200F2C4, 0x60516011, 0x8F4FF3BF, 0x8F6FF3BF, 0x2100BF00,
        0x6011BF00, 0xF8C06051, 0xF24A1718, 0xF2C40120, 0x680A0104, 0x0201F022, 0x6801600A, 0x7100F041,
        0xF24A6001, 0xF2C40000, 0x6801000A, 0x0102F041, 0xF2406001, 0xF2C00004, 0x21280000, 0x1000F849,
        0x47702000, 0x47702000, 0x0124F24A, 0x0104F2C4, 0x28006808, 0xBF00D405, 0x6808BF00, 0x3FFFF1B0,
        0xF06FDCFA, 0xF84160FF, 0xF2400C1C, 0xF2C00004, 0xF8590000, 0xB13A2000, 0xBF002200, 0xF859BF00,
        0x32013000, 0xD3F9429A, 0x07C06808, 0xBF00D004, 0x6808BF00, 0xD1FB07C0, 0x0C18F851, 0x2280F440,
        0xF8412000, 0x47702C18, 0xF000B580, 0x2000F97B, 0xBF00BD80, 0x4613B580, 0xF06F310F, 0xEA020203,
        0x46190291, 0xF9A4F000, 0xBD802000, 0xF06FB570, 0xEB0C0C1F, 0x46040C81, 0xBF382908, 0x0C81EA4F,
        0x0E0FF04F, 0x3404BF28, 0xFA0E6826, 0x43AEF50C, 0x68266026, 0xF20CFA02, 0x60224332, 0xFA022201,
        0x2B00F101, 0x2300F8D0, 0xEA22BF0C, 0x43110101, 0x1300F8C0, 0x0000BD70, 0x45F0E92D, 0x4607B081,
        0x70FFF240, 0x0004F2C4, 0x46982400, 0x42874692, 0xF2C4460D, 0xDD1A040A, 0x70FFF241, 0x0004F2C4,
        0xDC2A4287, 0x0000F640, 0x0004F2C4, 0xD0394287, 0x0000F241, 0x0004F2C4, 0xD1564287, 0xF2C42008,
        0x68010000, 0xF0413420, 0x60010104, 0xF1B7E04D, 0xD0302F40, 0x0000F644, 0x0000F2C4, 0xD03C4287,
        0xF2C42000, 0x42870004, 0x2008D13F, 0x0000F2C4, 0xF0416801, 0x60010101, 0xF641E037, 0xF2C40000,
        0x42870004, 0xF241D020, 0xF2C40000, 0x4287000A, 0x2008D12B, 0x0000F2C4, 0x34406841, 0x0101F041,
        0xE0226041, 0xF2C42008, 0x68010000, 0xF0413410, 0x60010102, 0x2008E019, 0x0000F2C4, 0x34806801,
        0x0110F041, 0xE0106001, 0xF2C42008, 0x68010000, 0xF0413430, 0x60010108, 0x2008E007, 0x0000F2C4,
        0x34906801, 0x0120F041, 0x46206001, 0x22004629, 0x26012301, 0xFF5AF7FF, 0xF005FA06, 0xF1BA6879,
        0xBF140F01, 0x0000EA21, 0x60784308, 0x98082101, 0xF8D440A9, 0xF1B82100, 0xBF140F01, 0x0101EA22,
        0x22014311, 0x1100F8C4, 0xFA022801, 0xF8D4F005, 0xBF142200, 0x0000EA22, 0x99094310, 0x0200F8C4,
        0x40A82001, 0xF8D42901, 0xBF0C1400, 0xEA214308, 0xF8C40000, 0xB0010400, 0x85F0E8BD, 0x68032201,
        0xF101FA02, 0x60014319, 0xBF004770, 0x68032201, 0xF101FA02, 0x0101EA23, 0x47706001, 0x68032201,
        0xF101FA02, 0x60014059, 0xBF004770, 0x40C86B00, 0x0001F000, 0xBF004770, 0x0210F1C2, 0x73FFF64F,
        0xF202FA23, 0xFA026803, 0x4319F101, 0x47706001, 0x0210F1C2, 0x73FFF64F, 0xF202FA23, 0xFA026803,
        0xEA23F101, 0x60010101, 0xBF004770, 0x0210F1C2, 0x73FFF64F, 0xF202FA23, 0xFA026803, 0x4059F101,
        0x47706001, 0xF1C26B00, 0xF64F0210, 0xFA2373FF, 0x40C8F202, 0x47704010, 0x0081EB00, 0x64012101,
        0xBF004770, 0x0081EB00, 0x64012100, 0xBF004770, 0x0081EB00, 0xF1C16C01, 0x64010101, 0xBF004770,
        0x0210F1C2, 0x73FFF64F, 0xF202FA23, 0x8310F3EF, 0x6803B672, 0xF101FA02, 0x60014319, 0x4770B662,
        0x0210F1C2, 0x73FFF64F, 0xF202FA23, 0x8310F3EF, 0x6803B672, 0xF101FA02, 0x0101EA23, 0xB6626001,
        0xBF004770, 0x0210F1C2, 0x73FFF64F, 0xF202FA23, 0x8310F3EF, 0x6803B672, 0xF101FA02, 0x60014059,
        0x4770B662, 0xBF1C0501, 0x47702002, 0x0124F24A, 0x8210F3EF, 0xF2C4B672, 0x680A0104, 0xD4042A00,
        0x680ABF00, 0x3FFFF1B2, 0xF040DCFA, 0xF8414078, 0xF2400C1C, 0xF2C00004, 0xF8590000, 0xB1522000,
        0xBF002200, 0xF859BF00, 0x32013000, 0xD3F9429A, 0xBF00E001, 0x6808BF00, 0xD1FB07C0, 0x0C18F851,
        0x2080F440, 0x0C18F841, 0x2000B662, 0xBF004770, 0x0C0FF000, 0x0303F002, 0x030CEA53, 0x2002BF1C,
        0xF24A4770, 0xF3EF0C0C, 0xB6728310, 0x0C04F2C4, 0x3018F8DC, 0xD4052B00, 0xF8DCBF00, 0xF1B33018,
        0xDCF93FFF, 0x3000F8DC, 0x0301F043, 0x3000F8CC, 0x0C08F84C, 0x2000B312, 0xBF00E003, 0x42903004,
        0xF851D21C, 0xF84C3020, 0xF0403C0C, 0xF8510301, 0xF84C3023, 0xF0403C0C, 0xF8510302, 0xF84C3023,
        0xF0403C0C, 0xF8510303, 0xF84C3023, 0xBF003C0C, 0x3018F8DC, 0xD4E1071B, 0xE7F9BF00, 0x0004F240,
        0x0000F2C0, 0x1000F859, 0x2100B149, 0xF859BF00, 0x31012000, 0xD3F94291, 0xBF00E001, 0xF8DCBF00,
        0x07800018, 0xF8DCD4FA, 0xF0200000, 0xF8CC0001, 0xF8DC0000, 0xF4400000, 0xF8CC2080, 0xB6620000,
        0x47702000, 0xF64FB580, 0xF3EF72AC, 0xB6728110, 0xF6C0284F, 0xDC103211, 0xD032281E, 0xD11F2828,
        0x0010F240, 0x0000F2C0, 0x3000F859, 0x2049F648, 0x41A9F241, 0xB6624798, 0x2850BD80, 0x2878D02E,
        0xF240D10E, 0xF2C00010, 0xF8590000, 0xF6413000, 0xF2C04089, 0xF6430001, 0x4798516B, 0xBD80B662,
        0x0010F240, 0x0000F2C0, 0x3000F859, 0x4089F641, 0x0001F2C0, 0x4092F500, 0x4174F644, 0xB6624798,
        0xF240BD80, 0xF2C00010, 0xF8590000, 0xF6483000, 0xF6401049, 0x479871A1, 0xBD80B662, 0x0010F240,
        0x0000F2C0, 0x3000F859, 0x3049F24D, 0x114AF642, 0xB6624798, 0x0000BD80, 0x4180F04F, 0x07C06808,
        0x0018F240, 0x0000F2C0, 0x6809D10C, 0x0182F3C1, 0xD8392904, 0xF001E8DF, 0x20031603, 0xF44F0025,
        0xE02F41FA, 0x0100F24A, 0x010AF2C4, 0x07896809, 0x2100F645, 0x2162F2C0, 0xF642BF5C, 0xF2C05100,
        0xE0291131, 0x0100F24A, 0x010AF2C4, 0xF6406C09, 0xF2C06100, 0xE0157127, 0x5100F642, 0x1131F2C0,
        0xF642E010, 0xF2C05100, 0xF8491131, 0xF24A1000, 0xF2C40100, 0x6809010A, 0xD5050789, 0x2100F645,
        0x2162F2C0, 0x1000F849, 0x4180F04F, 0x07896809, 0xF859D504, 0x08C91000, 0x1000F849, 0x0000F859,
        0x6183F64D, 0x311BF2C4, 0x0101FBA0, 0xF2400C88, 0xF2C00104, 0xF8490100, 0x47700001, 0x2008B510,
        0x0000F2C4, 0x24966801, 0x7100F041, 0x20966001, 0xFF38F7FF, 0xF82AF000, 0xFF8EF7FF, 0x0018F240,
        0x0000F2C0, 0x0000F859, 0x6100F640, 0x7127F2C0, 0xD8174288, 0x4100F24B, 0x41C4F2C0, 0xD9014288,
        0xE00F2478, 0x2100F645, 0x2162F2C0, 0xD9014288, 0xE0072450, 0x3180F24C, 0x11C9F2C0, 0x4288241E,
        0x2428BF88, 0xF7FF4620, 0xBD10FF0D, 0xF24AB580, 0xF2C40000, 0x2107000A, 0xF0006001, 0xF04FF817,
        0x68014080, 0x0101F041, 0xBD806001, 0xF24AB580, 0xF2C40000, 0x2105000A, 0xF0006001, 0xF04FF807,
        0x68014080, 0x0101F041, 0xBD806001, 0x4080F04F, 0x07C96801, 0x6800D110, 0x0F1CF010, 0xF04FD006,
        0x68004080, 0x001CF000, 0xD1052808, 0xBF002014, 0xBF003801, 0xE004D1FC, 0x6020F644, 0xBF003801,
        0x4770D1FC, 0xF7FFB510, 0x2004FFD1, 0x0000F2C4, 0x60012101, 0x4480F04F, 0xF0206820, 0x6020001C,
        0xF0406820, 0x60200010, 0xF0406820, 0x60200002, 0xFFCCF7FF, 0xF0206820, 0x60200001, 0xBF00BD10,
        0xF7FFB510, 0x2004FFA3, 0x0000F2C4, 0x60012101, 0x4480F04F, 0xF0206820, 0x6020001C, 0xF0406820,
        0x60200010, 0xF0406820, 0x60200002, 0xFFAEF7FF, 0xF0206820, 0x60200001, 0xBF00BD10, 0x4604B5B0,
        0xFF94F7FF, 0xF2C42500, 0x4628050A, 0x220F2103, 0xF7FF2300, 0x4628FC7B, 0x220F2104, 0xF7FF2300,
        0xF24AFC75, 0xF2C40020, 0x6801000A, 0x2170F441, 0x0102F041, 0xF7FF6001, 0xF7FFFF89, 0x2004FF87,
        0x0000F2C4, 0x60012101, 0x4080F04F, 0x2C006801, 0x011CF021, 0x68016001, 0x010CF041, 0x68016001,
        0x0102F021, 0x3102BF18, 0x68016001, 0x0101F021, 0xBDB06001, 0x4604B510, 0xFF58F7FF, 0xF81CF000,
        0xF2C42004, 0x21010000, 0xF04F6001, 0x68014080, 0xF0212C00, 0x6001011C, 0xF0416801, 0x60010104,
        0xF0216801, 0xBF180102, 0x60013102, 0xF0216801, 0x60010101, 0xBF00BD10, 0xF24AB510, 0xF2C40440,
        0x2005040A, 0x0C40F844, 0xFF40F7FF, 0xF64F6820, 0xF0406100, 0x60200002, 0xF6CF6860, 0x400841E0,
        0x68606060, 0x20A0F440, 0x003CF040, 0x68206060, 0x0004F020, 0xBF006020, 0x280068E0, 0x6820D0FC,
        0x0001F040, 0xBD106020, 0xF7FFB510, 0xF24AFF0F, 0xF2C40050, 0x2101000A, 0x20046001, 0x0000F2C4,
        0xF04F6001, 0x68204480, 0x001CF020, 0x68206020, 0x68206020, 0x0002F020, 0xF7FF6020, 0x6820FF07,
        0x0001F020, 0xBD106020, 0xF7FFB510, 0xF24AFEEF, 0xF2C40020, 0x6801000A, 0x7201F240, 0x60014311,
        0x707AF44F, 0xBF003801, 0x2004D1FC, 0x0000F2C4, 0x60012101, 0x4480F04F, 0xF0206820, 0x6020001C,
        0xF0406820, 0x60200008, 0xF0206820, 0x60200002, 0xFEDCF7FF, 0xF0206820, 0x60200001, 0x0000BD10,
        0x00000000, 0x00000014, 0x11000401, 0x11000471, 0x11000431, 0x110004C1, 0x01312D00
    ],

    'pc_Init'            : 0x20000021,
    'pc_UnInit'          : 0x200000A5,
    'pc_EraseSector'     : 0x20000109,
    'pc_ProgramPage'     : 0x20000115,
    'pc_Verify'          : 0x12000001F,
    'pc_EraseChip'       : 0x200000A9,
    'pc_BlankCheck'      : 0x12000001F,
    'pc_Read'            : 0x12000001F,
    
    'static_base'        : 0x20000600,
    'begin_data'         : 0x20000800,
    'begin_stack'        : 0x20001C00,

    'analyzer_supported' : False,

    # Relative region addresses and sizes
    'ro_start'           : 0x00000000,
    'ro_size'            : 0x000009A0,
    'rw_start'           : 0x000009A0,
    'rw_size'            : 0x0000001C,
    'zi_start'           : 0x000009BC,
    'zi_size'            : 0x00000000,

    # Flash information
    'flash_start'        : 0x00000000,
    'flash_size'         : 0x00080000,
    'flash_page_size'    : 0x00001000,
}

