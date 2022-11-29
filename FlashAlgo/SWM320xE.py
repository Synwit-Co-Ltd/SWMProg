"""
 Flash OS Routines (Automagically Generated)
 Copyright (c) 2017-2017 ARM Limited
"""

flash_algo = {
    'load_address' : 0x20000000,
    'instructions' : [
        0xE00ABE00, 0x062D780D, 0x24084068, 0xD3000040, 0x1E644058, 0x1C49D1FA, 0x2A001E52, 0x4770D1F2,
        0x4770BA40, 0x4770BAC0, 0x47702000, 0x47702000, 0x482DB508, 0x492B2200, 0x60819200, 0x07C96A01,
        0x6A01D0FC, 0xD1FC07C9, 0x20006082, 0xF040BD08, 0x48254100, 0x6A016081, 0xD0FC07C9, 0x07C96A01,
        0x6081D1FC, 0x47704608, 0x2300B51F, 0x3102E9CD, 0x2404491D, 0x604860CC, 0xE01C9803, 0x93019300,
        0x9C019302, 0x0B01F812, 0x40A000E4, 0x43209C02, 0x98019002, 0x90011C40, 0xDBF22804, 0x60089802,
        0x1D009800, 0x28109000, 0x6A08DBE9, 0xD5FC0700, 0x38109803, 0x28009003, 0x60CBDCE0, 0x60C82008,
        0xB00460CB, 0xBD102000, 0x4604B570, 0xE0052300, 0x78265CD5, 0xD10342B5, 0x1C641C5B, 0xD3F7428B,
        0xBD704418, 0x8007FFFF, 0x4001F000, 0x00000000
    ],

    'pc_Init'            : 0x20000029,
    'pc_UnInit'          : 0x2000002D,
    'pc_EraseSector'     : 0x2000004F,
    'pc_ProgramPage'     : 0x20000069,
    'pc_Verify'          : 0x200000C9,
    'pc_EraseChip'       : 0x20000031,
    'pc_BlankCheck'      : 0x12000001F,
    'pc_Read'            : 0x12000001F,
    
    'static_base'        : 0x20000600,
    'begin_data'         : 0x20000800,
    'begin_stack'        : 0x20001C00,

    'analyzer_supported' : False,

    # Relative region addresses and sizes
    'ro_start'           : 0x00000000,
    'ro_size'            : 0x000000CC,
    'rw_start'           : 0x000000CC,
    'rw_size'            : 0x00000004,
    'zi_start'           : 0x000000D0,
    'zi_size'            : 0x00000000,

    # Flash information
    'flash_start'        : 0x00000000,
    'flash_size'         : 0x00080000,
    'flash_page_size'    : 0x00001000,
}
