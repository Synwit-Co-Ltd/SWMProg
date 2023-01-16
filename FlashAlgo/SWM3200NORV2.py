"""
 Flash OS Routines (Automagically Generated)
 Copyright (c) 2017-2017 ARM Limited
"""

flash_algo = {
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
    
    'static_base'        : 0x20000148,
    'begin_data'         : 0x2000014C,
    'begin_stack'        : 0x2000154C,

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
    'sector_sizes': (
        (0x00000, 0x10000),
    )
}
