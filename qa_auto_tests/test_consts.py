QA2_THEME_SAMPLE = """
Credit QA2_TEST_THEME

# The "Credit" line will be kept as the first line; if not credit is present, the credit line will default to "Geetansh Gautam, Coding Made Fun"
# Do not put a colon after 'Credit' or else the theme is considered invalid

# Comments can be written with a '#' in the leading a line
# Comments and empty lines will be ignored

# This comment header will remain
# All other comments will be overwritten

font TEST_ITEM::FONT<A1>
fsize_para 10
btn_fsize 13
sttl_base_fsize 18
min_fsize 10
bg #000000
fg #ffff00
ac #00ff00
hg #000000
border_color #ffffff
border 0
"""

QA3_THEME_ALPHA_ONE_SAMPLE = """
{
    "file_info": {
        "name": "TEST_ITEM::META.FINAME",
        "display_name": "TEST_ITEM::META.FDNAME",
        "avail_themes": {
            "num_themes": 1,
            "ugen_exp": "TEST_ITEM::META.TCODE"
        }
    },
    "TEST_ITEM::META.TCODE": {
        "display_name": "TEST_ITEM::META.TDNAME",
        "background": "#000000",
        "foreground": "#FFFFFF",
        "accent": "#F0F0F0",
        "error": "#FF0000",
        "warning": "#FFFF00",
        "ok": "#00FF00",
        "gray": "#DDDDDD",
        "font": {
            "title_font_face": "TEST_ITEM::FONT<A2>",
            "font_face": "TEST_ITEM::FONT<A1>",
            "alt_font_face": "TEST_ITEM::FONT<A3>",
            "size_small": 10,
            "size_main": 13,
            "size_subtitle": 15,
            "size_title": 28,
            "size_xl_title": 40
        },
        "border": {
            "size": 0,
            "colour": "#FFFFFF"
        }
    }
}
"""

QA3_THEME_ALPHA_TWO_SAMPLE = """
{
    "meta": {
        "app.ver": 3.0,
        "app.build": "bfe869e8a7757c8e1f298d7d9fea2b35",
        "db.dname": "TEST_ITEM::META.FDNAME",
        "db.iname": "TEST_ITEM::META.FINAME",
        "db.frmt": 2,
        "db.fver": "0.0.2 <A>",
        "db.gen_time": "TEST_ITEM::META.GEN_TIME",
        "db.themes": {
            "db.n": 1,
            "0": "TEST_ITEM::META.TCODE"
        }
    },
    "content": {
        "TEST_ITEM::META.TCODE": {
            "theme.dname": "TEST_ITEM::META.TDNAME",
            "theme.background": "#000000",
            "theme.foreground": "#FFFFFF",
            "theme.accent": "#F0F0F0",
            "theme.error": "#FF0000",
            "theme.warning": "#FFFF00",
            "theme.ok": "#00FF00",
            "theme.gray": "#dddddd",
            "theme.font": {
                "theme.font.face.title": "TEST_ITEM::FONT<A2>",
                "theme.font.face.main": "TEST_ITEM::FONT<A1>",
                "theme.font.face.alt": "TEST_ITEM::FONT<A3>",
                "theme.font.SZ1": 10,
                "theme.font.SZ2": 13,
                "theme.font.SZ3": 15,
                "theme.font.SZ4": 28,
                "theme.font.SZ5": 40
            },
            "theme.border": {
                "theme.border.CL": "#ffffff",
                "theme.border.SZ": 0
            },
            "ATTR.1": true,
            "ATTR.2": "TDB-R2<JSON>"
        }
    },
    "validity": {
        "meta": "d105fd734f23293627fac95514139161",
        "content": "7d5826763cd56afb9ea34a7f98f4e7c1"
    }
}
"""


QA_THEME_CHK = {
    '0x01': {'file_info': {'name': 'nullstr', 'display_name': 'nullstr', 'avail_themes': {'num_themes': 1, '0': '<COMP+QA2.THEME>:LOADED'}}, '<COMP+QA2.THEME>:LOADED': {'display_name': '.REP.', 'background': '#000000', 'foreground': '#FFFF00', 'accent': '#00FF00', 'error': '#FF0000', 'warning': '#FFFF00', 'ok': '#00FF00', 'gray': '#988998', 'font': {'title_font_face': 'TEST_ITEM::FONT<A1>', 'font_face': 'TEST_ITEM::FONT<A1>', 'alt_font_face': 'Times New Roman', 'size_small': 10, 'size_main': 10, 'size_subtitle': 18, 'size_title': 20, 'size_xl_title': 22}, 'border': {'size': 0, 'colour': '#FFFFFF'}}},
    '0x02': {'file_info': {'name': 'TEST_ITEM::META.FINAME', 'display_name': 'TEST_ITEM::META.FDNAME', 'avail_themes': {'num_themes': 1, '0': 'TEST_ITEM::META.TCODE'}}, 'TEST_ITEM::META.TCODE': {'display_name': 'TEST_ITEM::META.TDNAME', 'background': '#000000', 'foreground': '#FFFFFF', 'accent': '#F0F0F0', 'error': '#FF0000', 'warning': '#FFFF00', 'ok': '#00FF00', 'gray': '#DDDDDD', 'font': {'title_font_face': 'TEST_ITEM::FONT<A2>', 'font_face': 'TEST_ITEM::FONT<A1>', 'alt_font_face': 'TEST_ITEM::FONT<A3>', 'size_small': 10, 'size_main': 13, 'size_subtitle': 15, 'size_title': 28, 'size_xl_title': 40}, 'border': {'size': 0, 'colour': '#FFFFFF'}}},
    '0x03': {'file_info': {'name': 'TEST_ITEM::META.FINAME', 'display_name': 'TEST_ITEM::META.FDNAME', 'avail_themes': {'num_themes': 1, '0': 'TEST_ITEM::META.TCODE'}}, 'TEST_ITEM::META.TCODE': {'display_name': 'TEST_ITEM::META.TDNAME', 'background': '#000000', 'foreground': '#FFFFFF', 'accent': '#F0F0F0', 'error': '#FF0000', 'warning': '#FFFF00', 'ok': '#00FF00', 'gray': '#DDDDDD', 'font': {'title_font_face': 'TEST_ITEM::FONT<A2>', 'font_face': 'TEST_ITEM::FONT<A1>', 'alt_font_face': 'TEST_ITEM::FONT<A3>', 'size_small': 10, 'size_main': 13, 'size_subtitle': 15, 'size_title': 28, 'size_xl_title': 40}, 'border': {'size': 0, 'colour': '#FFFFFF'}}},    
}
