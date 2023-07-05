import json, sys, hashlib, datetime, re, random
from qa_functions.qa_std import HexColor, data_at_dict_path, check_hex_contrast
from qa_functions.qa_custom import Theme
from typing import Dict, Optional, Tuple, Any, cast, List, Union
from dataclasses import dataclass
from tkinter import messagebox
from enum import Enum


# the following must trail the data in all TDB
C_TRAILING_ID                   = '%qaQuiz'


# constants (DO NOT CHANGE)
C_META                          = 'meta' 
C_CONTENT                       = 'content'
C_VALIDITY                      = 'validity'


class R1:
    FInfo                       = 'file_info'
    FName                       = 'name'
    FDName                      = 'display_name'
    FAThemes                    = 'avail_themes'
    
    FAT_N                       = 'num_themes'
    
    TDName                      = FDName
    
    TBG                         = 'background'
    TFG                         = 'foreground'
    TAC                         = 'accent'
    TER                         = 'error'
    TWA                         = 'warning'
    TOK                         = 'ok'
    TGR                         = 'gray'
    
    TFont                       = 'font'
    TFont_TTLFF                 = 'title_font_face'
    TFont_FF                    = 'font_face'
    TFont_AFF                   = 'alt_font_face'
    TFont_szSMALL               = 'size_small'
    TFont_szMAIN                = 'size_main'
    TFont_szLARGE               = 'size_subtitle'
    TFont_szTTL                 = 'size_title'
    TFont_szXLTTL               = 'size_xl_title'
    
    TBorder                     = 'border'
    TBorder_sz                  = 'size'
    TBorder_cl                  = 'colour'


class R2:
    M_FRMT                      = 'db.frmt'
    M_FVER                      = 'db.fver'
    M_AVER                      = 'app.ver'
    M_ABUILD                    = 'app.build'
    M_GEN_TIME                  = 'db.gen_time'
    M_FINAME                    = 'db.iname'
    M_FDNAME                    = 'db.dname'
    M_THEMES                    = 'db.themes'
    M_NTHEME                    = 'db.n'
    
    C_TDNAME                    = 'theme.dname'
    
    C_BG                        = f'theme.{R1.TBG}'
    C_FG                        = f'theme.{R1.TFG}'
    C_AC                        = f'theme.{R1.TAC}'
    C_ER                        = f'theme.{R1.TER}'
    C_WA                        = f'theme.{R1.TWA}'
    C_OK                        = f'theme.{R1.TOK}'
    C_GR                        = f'theme.{R1.TGR}'
    
    C_FONT_ROOT                 = f'theme.{R1.TFont}'
    C_FONT_FF_TTL               = f'theme.font.face.title'
    C_FONT_FF_MAIN              = f'theme.font.face.main'
    C_FONT_FF_ALT               = f'theme.font.face.alt'
    C_FONT_SZ1                  = f'theme.font.SZ1'
    C_FONT_SZ2                  = f'theme.font.SZ2'
    C_FONT_SZ3                  = f'theme.font.SZ3'
    C_FONT_SZ4                  = f'theme.font.SZ4'
    C_FONT_SZ5                  = f'theme.font.SZ5'

    C_BORDER_ROOT               = f'theme.{R1.TBorder}'
    C_BORDER_CL                 = f'theme.border.CL'
    C_BORDER_SZ                 = f'theme.border.SZ'
    

NULL_STR                        = 'qaTheme.null'
NULL_INT                        = 0


class T_FRMT(Enum):
    # DO NOT let any enum's value equal 0 as that is reserved for _null_int
    TDB_R1 = 1     # Does not contain any meta information. Added for backwards compatability.
    TDB_R2 = 2 
    
    TDB_II = 9     # Compatible with QAS version 2 theme files. 


class ValidationState(Enum):
    VALIDATION_FAILED = 0
    VALIDATION_SUCCESSFUL = 1
    VALIDATION_UNAVAILABLE = 2


@dataclass
class TDB:
    Theme_FileCode:             str
    Theme_FileName:             str
    Theme_NThemes:              int
    Theme_FilePath:             str
    Theme_AvailableThemes:      List[Theme]
    
    FileVersion:                str
    FileFormat:                 int
    FileGenTime:                str
    
    ValidationAvailable:        bool
    ValidationData:             List[Union[int, str]]        # List of md5 hashes for META and CONTENT (if available)
                                                             # [N_items, <HASHES>]
    Validated:                  ValidationState

    App_Version:                str = NULL_STR
    App_Build:                  str = NULL_STR
    

class Generate:
    @staticmethod
    def ALPHA_TWO(
        # Format and file version implicit (TDB-R2)
        meta_file_path: str,                        # NOTE: Not included JSON representation 
        meta_file_internal_name: str,
        meta_file_display_name: str,
        meta_app_version: str,
        meta_app_build: str,
        themes: Dict[str, Theme]        
    ) -> Tuple[TDB, str]:
        """
        Generates a TDB-R2 compliant TDB instance. 
        
        Args:
            meta_file_path (str): path to theme file
            meta_file_internal_name (str): internal name for file (previously referred to as 'name')
            meta_file_display_name (str): display name for file
            meta_app_version (str): app version
            meta_app_build (str): app build ID
            themes (Dict[str, Theme]): { <THEME_CODE>: <THEME> }

        Implicit Attributes:
            i)      Validation available (hashes generated automatically)
            ii)     Output is TDB-R2 AND TDB-R1 compliant
            iii)    File generation time generated automatically
            iv)     File format str and file format enum (TDB-R2)
        
        Returns:
            Tuple[TDB, str]: DB instance, JSON string representation (TDB-R2 compliant)
        """
        global _TDB_file_versions, C_META, C_CONTENT, C_VALIDITY
        
        assert len(themes), '0x00'
        
        db = TDB(
            meta_file_internal_name, meta_file_display_name, len(themes), meta_file_path, 
            list(themes.values()),
            cast(str, _TDB_file_versions[T_FRMT.TDB_R2.value][0]), T_FRMT.TDB_R2.value, 
            datetime.datetime.now().strftime('%a, %B %d, %Y - %H:%M:%S'), 
            True, [2], ValidationState.VALIDATION_SUCCESSFUL,
            meta_app_version, meta_app_build
        )
        
        dc: Dict[str, Any] = {
            C_META:
                {
                    R2.M_AVER: meta_app_version,
                    R2.M_ABUILD: meta_app_build,
                    R2.M_FDNAME: meta_file_display_name,
                    R2.M_FINAME: meta_file_internal_name,
                    R2.M_FRMT: db.FileFormat,
                    R2.M_FVER: db.FileVersion,
                    R2.M_GEN_TIME: db.FileGenTime,
                    R2.M_THEMES:
                        {
                            R2.M_NTHEME: db.Theme_NThemes,
                            **{str(i): code for i, code in enumerate(themes.keys())}
                        }
                },
            C_CONTENT:
                {
                    # Theme Code: Theme Info
                    code: 
                        {
                            R2.C_TDNAME: theme.theme_display_name,
                            
                            R2.C_BG: theme.background.color,
                            R2.C_FG: theme.foreground.color,    
                            R2.C_AC: theme.accent.color,
                            R2.C_ER: theme.error.color,
                            R2.C_WA: theme.warning.color,
                            R2.C_OK: theme.okay.color,
                            R2.C_GR: theme.gray.color,
                            
                            R2.C_FONT_ROOT:
                                {
                                    R2.C_FONT_FF_TTL: theme.title_font_face,
                                    R2.C_FONT_FF_MAIN: theme.font_face,
                                    R2.C_FONT_FF_ALT: theme.font_alt_face,
                                    
                                    R2.C_FONT_SZ1: theme.font_small_size,
                                    R2.C_FONT_SZ2: theme.font_main_size,
                                    R2.C_FONT_SZ3: theme.font_large_size,
                                    R2.C_FONT_SZ4: theme.font_title_size,
                                    R2.C_FONT_SZ5: theme.font_xl_title_size
                                },
                                
                            R2.C_BORDER_ROOT:
                                {
                                    R2.C_BORDER_CL: theme.border_color.color,
                                    R2.C_BORDER_SZ: theme.border_size
                                },
                            
                            'ATTR.1': theme.check(),
                            'ATTR.2': 'TDB-R2<JSON>'
                        }
                        
                    for code, theme in themes.items()
                },
            C_VALIDITY:
                {
                    C_META: '',
                    C_CONTENT: ''
                }    
        }
        
        dc[C_VALIDITY][C_META] = hashlib.md5(json.dumps(dc[C_META]).encode()).hexdigest()  # type: ignore
        dc[C_VALIDITY][C_CONTENT] = hashlib.md5(json.dumps(dc[C_CONTENT]).encode()).hexdigest()  # type: ignore
        
        db.ValidationData = [2, dc[C_VALIDITY][C_META], dc[C_VALIDITY][C_CONTENT]]
        
        ds = json.dumps(dc, indent=4)
        
        return db, ds
    
    _latest_ver = ALPHA_TWO


class Read:
    @staticmethod
    def QAS2_theme_file(data: str, path_to_file: str) -> TDB:
        global _TDB_file_versions
        
        assert isinstance(data, str) & isinstance(path_to_file, str), '0x00'
        
        lines = {}
        
        for line in data.split('\n'):
            if len(line.strip()):
                if line.strip()[0] == '#': continue
                
                k = line.strip().split(' ')[0]
                v = line.replace(k, '', 1).strip()
                
                lines[k] = v
        
        exp_vs = {
            'Credit': (str, None, None, []),  # ignored
            'font': (str, None, None, []),
            'fsize_para': (int, 5, 25, []),
            'btn_fsize': (int, None, None, []),  # ignored
            'sttl_base_fsize': (int, 10, 30, []),
            'min_fsize': (int, 5, 20, []),
            'bg': (str, None, None, ['hex_color_code']),
            'fg': (str, None, None, ['hex_color_code']),
            'ac': (str, None, None, ['hex_color_code']),
            'hg': (str, None, None, ['hex_color_code']),
            'border_color': (str, None, None, ['hex_color_code']),
            'border': (int, 0, 10, [])
        }
        
        assert len(lines) == len(exp_vs), '0xC0'
        lP = {}
        
        for K, V in lines.items():
            assert K in exp_vs, f'0xC1 <{K}>'
            
            tp, minimum, maximum, flags = exp_vs[K]
            
            cast(List[str], flags)
            
            try:
                Vp = tp(V)
            except Exception as _:
                raise Exception (f'0xC2')
            
            if isinstance(minimum, int):
                assert Vp >= minimum, '0xC3 (a)' 
            
            if isinstance(maximum, int):
                assert Vp <= maximum, '0xC3 (b)'
                
            if 'hex_color_code' in flags:  # type: ignore
                assert Vp[0] == '#', '0xC4 (a)'
                m = re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', Vp)
                
                assert m is not None, '0xC4 (b)'
                Vp = HexColor(m.string)
                
            lP[K] = Vp
        
        messagebox.showwarning('QA Files: QA Theme', 'The file you selected was created for version 2 of the application. Although some of the data was recovered, \n\n(a) The theming system may refuse to use this file if it does not adhere to this version\'s theming requirements; and, \n\n(b) a lot of information is missing from this file; it is highly recommended to use the THEMING UTILITY to provide the missing information.')
        
        theme = Theme(
            NULL_STR, NULL_STR, f'QAS 2 Theme {random.randint(100_000_000, 999_999_999)}', '<COMP+QA2.THEME>:LOADED', path_to_file,
            lP['bg'], lP['fg'], lP['ac'], HexColor('#ff0000'), HexColor('#ffff00'),
            HexColor('#00ff00'), HexColor('#988998'), lP['font'], lP['font'], 'Times New Roman',
            lP['min_fsize'], lP['fsize_para'], lP['sttl_base_fsize'], 20, 22, lP['border'], lP['border_color']
        )
        
        name = path_to_file.replace('/', '\\').split('\\')[-1]
        
        db = TDB(
            name, name, 1, path_to_file,                                        # File information (code, name, N, path)
            [theme],                                                            # Theme
            _TDB_file_versions[T_FRMT.TDB_II.value][0], T_FRMT.TDB_II.value,    # type: ignore  
                                                                                # ^ Format information
            NULL_STR,                                                           # Additional meta (gen_time)
            False, [0], ValidationState.VALIDATION_UNAVAILABLE                  # Validation information
        )
        
        fail, warn, pss = Check.TDB_R1(TDB_to_DICT(db))
        pss1 = theme.check()
        pss &= pss1
        
        if not pss1:
            fail[hex(int('pss1', 16)) + 'A0FF'] = 'APPLICATION_THEME_REQUIREMENT_FORMAT_STANDARD_NOT_MET'
        
        if not pss:
            messagebox.showerror('QA Theming Service', 'Although the file provided is a valid theme file, its content is not condusive to the Quizzing Application version 3 theme requirements. \n\nWARN:\n%s\n\nERRORS:\n%s' % (
                '\n* '.join('<Check %s> %s' % (code, string) for code, string in warn.items()),
                '\n* '.join('<Check %s> %s' % (code, string) for code, string in fail.items())
            ))
        
        if (len(fail) + len(warn)):
            sys.stderr.write('QA Theming Service <Check: TDB-R1<DICT>>: \n\nFAILURES:\n%s\n\nWARNINGS:\n%s\n\nEND\n' % (
                '\n* '.join('<Check %s> %s' % (code, string) for code, string in fail.items()),
                '\n* '.join('<Check %s> %s' % (code, string) for code, string in warn.items())
            ))
        
        assert pss, '0x00CF'
        
        return db
        
    @staticmethod 
    def ALPHA_ONE(data: Dict[str, Any], path_to_file: str) -> TDB:        
        global _TDB_file_versions
        # format = TDB-R1 
        
        assert isinstance(data, dict) & isinstance(path_to_file, str), '0x00'
        assert len(data) > 1 and R1.FInfo in data, '0x10'
        
        themes = []
        
        for key, value in data.items():
            if key == R1.FInfo: continue 
            
            theme_code, theme = key, value
            
            themes.append(
                Theme(
                    data[R1.FInfo][R1.FName],
                    data[R1.FInfo][R1.FDName],
                    theme[R1.TDName],
                    theme_code,
                    path_to_file,
                    HexColor(theme[R1.TBG]),
                    HexColor(theme[R1.TFG]),
                    HexColor(theme[R1.TAC]),
                    HexColor(theme[R1.TER]),
                    HexColor(theme[R1.TWA]),
                    HexColor(theme[R1.TOK]),
                    HexColor(theme[R1.TGR]),
                    theme[R1.TFont][R1.TFont_TTLFF],
                    theme[R1.TFont][R1.TFont_FF],
                    theme[R1.TFont][R1.TFont_AFF],
                    theme[R1.TFont][R1.TFont_szSMALL],
                    theme[R1.TFont][R1.TFont_szMAIN],
                    theme[R1.TFont][R1.TFont_szLARGE],
                    theme[R1.TFont][R1.TFont_szTTL],
                    theme[R1.TFont][R1.TFont_szXLTTL],
                    theme[R1.TBorder][R1.TBorder_sz],
                    HexColor(theme[R1.TBorder][R1.TBorder_cl]),
                )
            )
        
        assert bool(len(themes)) and (len(themes) == data[R1.FInfo][R1.FAThemes][R1.FAT_N]), f'0x20 {len(themes)} {data[R1.FInfo][R1.FAThemes][R1.FAT_N]}'
        
        db = TDB(
            data[R1.FInfo][R1.FName],
            data[R1.FInfo][R1.FDName],
            len(themes),
            path_to_file,
            themes,
            _TDB_file_versions[T_FRMT.TDB_R1.value][0],  # type: ignore
            T_FRMT.TDB_R1.value,
            datetime.datetime.now().strftime('%a, %B %d, %Y - %H:%M:%S'),
            False,
            [0],
            ValidationState.VALIDATION_UNAVAILABLE
        )
        
        failures, warnings, pss0 = Check.TDB_R1(TDB_to_DICT(db))
        pss1 = sum( int(theme.check()) for theme in themes ) == len(themes)  # If all themes pass, then this statement is TRUE
        
        pss0 &= pss1
        if not pss1:
            failures[hex(int('pss1', 16)) + 'A0FF'] = 'APPLICATION_THEME_REQUIREMENT_FORMAT_STANDARD_NOT_MET'
        
        if not pss0:
            messagebox.showerror('QA Theming Service', 'Although the file provided is a valid theme file, its content is not condusive to the Quizzing Application version 3 theme requirements. \n\nWARN:\n%s\n\nERRORS:\n%s' % (
                '\n* '.join('<Check %s> %s' % (code, string) for code, string in warnings.items()),
                '\n* '.join('<Check %s> %s' % (code, string) for code, string in failures.items())
            ))
        
        if (len(failures) + len(warnings)):
            sys.stderr.write('QA Theming Service <Check: TDB-R1<DICT>>: \n\nFAILURES:\n%s\n\nWARNINGS:\n%s\n\nEND\n' % (
                '\n* '.join('<Check %s> %s' % (code, string) for code, string in failures.items()),
                '\n* '.join('<Check %s> %s' % (code, string) for code, string in warnings.items())
            ))
        
        assert pss0, '0x00CF'
        
        return db
        
    @staticmethod 
    def ALPHA_TWO(data: Dict[str, Any], path_to_file: str) -> TDB:
        global _TDB_file_versions, C_META, C_CONTENT, C_VALIDITY
        
        assert C_META in data,        '0x00A100'
        assert C_CONTENT in data,     '0x00A200'
        assert C_VALIDITY in data,    '0x00A300'
        
        for path in (
            R2.M_AVER, R2.M_ABUILD, R2.M_FDNAME, R2.M_FINAME, R2.M_FRMT, R2.M_FVER, R2.M_GEN_TIME, R2.M_THEMES,
            f'{R2.M_THEMES}/{R2.M_NTHEME}'
        ):
            assert data_at_dict_path(path, data[C_META])[0], '0x00B000' + hex(int(hashlib.md5(path.encode()).hexdigest()[-5:], 16))[2:]
        
        assert data[C_META][R2.M_THEMES][R2.M_NTHEME] == len(data[C_META][R2.M_THEMES]) - 1 == len(data[C_CONTENT]), '0x00B1A0'
        
        for key, code in data[C_META][R2.M_THEMES].items():
            if key == R2.M_NTHEME: continue
            assert code in data[C_CONTENT], '0x00B1B0' + hex(int(hashlib.md5(code.encode()).hexdigest()[-5:], 16))[2:]
        
        for theme in data[C_CONTENT]:
            for path in (
                R2.C_FG, R2.C_BG, R2.C_AC, R2.C_ER, R2.C_WA, R2.C_OK, R2.C_GR,
                f'{R2.C_FONT_ROOT}/{R2.C_FONT_FF_TTL}', f'{R2.C_FONT_ROOT}/{R2.C_FONT_FF_MAIN}', 
                f'{R2.C_FONT_ROOT}/{R2.C_FONT_FF_ALT}', f'{R2.C_FONT_ROOT}/{R2.C_FONT_SZ1}', 
                f'{R2.C_FONT_ROOT}/{R2.C_FONT_SZ2}', f'{R2.C_FONT_ROOT}/{R2.C_FONT_SZ3}', f'{R2.C_FONT_ROOT}/{R2.C_FONT_SZ4}', 
                f'{R2.C_FONT_ROOT}/{R2.C_FONT_SZ5}', f'{R2.C_BORDER_ROOT}/{R2.C_BORDER_CL}', f'{R2.C_BORDER_ROOT}/{R2.C_BORDER_SZ}',
                'ATTR.1', 'ATTR.2'
            ):
                assert data_at_dict_path(path, data[C_CONTENT][theme])[0], '0x00B2C0' + hex(int(hashlib.md5(path.encode()).hexdigest()[-5:], 16))[2:]
                
            assert data[C_CONTENT][theme]['ATTR.2'] == 'TDB-R2<JSON>',      '0x00B3CA' 
            assert data[C_CONTENT][theme]['ATTR.1'],                        '0x00B3CB'
        
        assert data_at_dict_path(f'{C_VALIDITY}/{C_META}', data)[0],        '0x00C000'
        assert data_at_dict_path(f'{C_VALIDITY}/{C_CONTENT}', data)[0],     '0x00C001'
        
        exp_hash_M = hashlib.md5(json.dumps(data[C_META]).encode()).hexdigest()
        exp_hash_C = hashlib.md5(json.dumps(data[C_CONTENT]).encode()).hexdigest()

        assert data[C_VALIDITY][C_META] == exp_hash_M,                      '0x00D000'
        assert data[C_VALIDITY][C_CONTENT] == exp_hash_C,                   '0x00D001'
        
        # All checks passed, time to actually load the data
        
        themes: List[Theme] = []
        for i, (code, theme) in enumerate(data[C_CONTENT].items()):
            themes.append(
                Theme(
                    data[C_META][R2.M_FINAME],
                    data[C_META][R2.M_FDNAME],
                    theme[R2.C_TDNAME],
                    code, 
                    path_to_file,
                    HexColor(theme[R2.C_BG]),
                    HexColor(theme[R2.C_FG]),
                    HexColor(theme[R2.C_AC]),
                    HexColor(theme[R2.C_ER]),
                    HexColor(theme[R2.C_WA]),
                    HexColor(theme[R2.C_OK]),
                    HexColor(theme[R2.C_GR]),
                    theme[R2.C_FONT_ROOT][R2.C_FONT_FF_TTL],
                    theme[R2.C_FONT_ROOT][R2.C_FONT_FF_MAIN],
                    theme[R2.C_FONT_ROOT][R2.C_FONT_FF_ALT],
                    theme[R2.C_FONT_ROOT][R2.C_FONT_SZ1],
                    theme[R2.C_FONT_ROOT][R2.C_FONT_SZ2],
                    theme[R2.C_FONT_ROOT][R2.C_FONT_SZ3],
                    theme[R2.C_FONT_ROOT][R2.C_FONT_SZ4],
                    theme[R2.C_FONT_ROOT][R2.C_FONT_SZ5],
                    theme[R2.C_BORDER_ROOT][R2.C_BORDER_SZ],
                    HexColor(theme[R2.C_BORDER_ROOT][R2.C_BORDER_CL])
                )
            )
            
            assert themes[-1].check(),                                      '0x00E0' + hex(i)[2::]
        
        return TDB(
            data[C_META][R2.M_FINAME], data[C_META][R2.M_FDNAME], data[C_META][R2.M_THEMES][R2.M_NTHEME],
            path_to_file, themes, _TDB_file_versions[T_FRMT.TDB_R2.value][0], T_FRMT.TDB_R2.value,  # type: ignore
            data[C_META][R2.M_GEN_TIME], True, [2, exp_hash_M, exp_hash_C], ValidationState.VALIDATION_SUCCESSFUL, 
            data[C_META][R2.M_AVER], data[C_META][R2.M_ABUILD]
        )
        

class Check:
    @staticmethod
    def TDB_R1(data: Dict[str, Any]) -> Tuple[Dict[str, str], Dict[str, str], bool]:
        """
        Determines whether DATA is TDB-R1<DICT> compliant.
        
        ALL databases must pass this format's test. 

        Args:
            data (Dict[str, Any])

        Returns:
            Tuple[Dict[str, str], Dict[str, str], bool]: failures, warnings, <pass?>
        """
        
        assert isinstance(data, dict), 'ATTRIBUTE_TYPE_ERROR <data>'
        
        failures = {}
        warnings = {}
        
        checks = {                                            # (type,      meta)
            f'{R1.FInfo}/{R1.FName}':                           (str,       True),
            f'{R1.FInfo}/{R1.FDName}':                          (str,       True),
            f'{R1.FInfo}/{R1.FAThemes}/{R1.FAT_N}':             (int,       True),

            R1.TBG:                                             (HexColor,  False),
            R1.TFG:                                             (HexColor,  False),
            R1.TAC:                                             (HexColor,  False),
            R1.TER:                                             (HexColor,  False),
            R1.TWA:                                             (HexColor,  False),
            R1.TOK:                                             (HexColor,  False),
            R1.TGR:                                             (HexColor,  False),
            R1.TDName:                                          (str,       False),

            f'{R1.TFont}/{R1.TFont_TTLFF}':                     (str,       False),
            f'{R1.TFont}/{R1.TFont_FF}':                        (str,       False),
            f'{R1.TFont}/{R1.TFont_AFF}':                       (str,       False),
            f'{R1.TFont}/{R1.TFont_szSMALL}':                   (int,       False),
            f'{R1.TFont}/{R1.TFont_szMAIN}':                    (int,       False),
            f'{R1.TFont}/{R1.TFont_szLARGE}':                   (int,       False),
            f'{R1.TFont}/{R1.TFont_szTTL}':                     (int,       False),
            f'{R1.TFont}/{R1.TFont_szXLTTL}':                   (int,       False),
            
            f'{R1.TBorder}/{R1.TBorder_sz}':                    (int,       False),
            f'{R1.TBorder}/{R1.TBorder_cl}':                    (HexColor,  False),                        
        }

        # Check meta information
        for _i, (_key, (_type, _meta)) in enumerate(checks.items()):
            i = hex(_i) + '0001'  # 00 indicates step 1, 01 indicates _meta is TRUE (logs only produced when _meta)
            if _meta:             
                d = data_at_dict_path(_key, data)[1]
                if not isinstance(d, _type):
                    failures[i + 'A0'] = f'TYPE_ERROR      <{_type}, {type(d)}> @ C.TDB-R1<DICT>'
                    failures[i + 'B0'] = f'VALUE_ERROR     <MIN 0> @ C.TDB-R1<DICT>'
                
                if _key == f'{R1.FInfo}/{R1.FAThemes}/{R1.FAT_N}':
                    if d <= 0:
                        failures[i + 'B1'] = f'VALUE_ERROR     <MIN FATN 0> @ C.TDB-R1<DICT>'
                    
                    if not (len(data) - 1 == len(data[R1.FInfo][R1.FAThemes]) - 1 == d):
                        failures[i + 'B2'] = f'VALUE_ERROR     <lD, lG, lC> @ C.TDB-R1<DICT>'

        # Check theme contents
        bCode = '0x000100'  # non-iter, step 2, _meta is FALSE
        avail_themes = data.get(R1.FInfo, {}).get(R1.FAThemes, {})
        
        assert isinstance(avail_themes, dict), '0xF1'
        
        if (R1.FAT_N not in avail_themes) \
            or not (len(avail_themes) - 1 == avail_themes.get(R1.FAT_N, -2) == len(data) - 1) \
            or (avail_themes.get(R1.FAT_N, 0) == 0):
                
            warnings[bCode + '10'] = 'Cannot test CONTENT (drr.FATN).'
            failures[bCode + '10'] = 'MISSING_CONTENT       <FATN> @ C.TDB-R1<DICT>'
            failures[bCode + '1A'] = 'CANNOT_TEST           <drr.FATN> @ C.TDB-R1<DICT>'
            
            return failures, warnings, not bool(len(failures))

        N = avail_themes.pop(R1.FAT_N)
        assert len(avail_themes), '0xF2 (a)'
        assert N, '0xF2 (b)'
        
        nCode = '0xFF0200'
        
        for i, theme_code in enumerate(avail_themes.values()):  # type: ignore
            if theme_code not in data:
                failures[bCode + '20' + hex(i)[2::]] = f'MISSING_CONTENT       <TCODE, {theme_code}> @ C.TDB-R1<DICT>'  # type: ignore
                failures[bCode + '2F' + hex(i)[2::]] = f'THEME_FAILURE         <AUTO> @ C.TDB-R1<DICT>'  # type: ignore
                warnings[bCode + '20' + hex(i)[2::]] = f'No CONTENT for TCODE "{theme_code}"'  # type: ignore
        
                continue
            
            # Test the theme itself
            theme = data[theme_code]
            for _j, (_key, (_type, _meta)) in enumerate(checks.items()):
                j = hex(_j)[2::]
                if _meta: continue  # Do not want to check for meta keys.
                
                df, d = data_at_dict_path(_key, theme)
                
                if not df:
                    failures[nCode + j + '00'] = f'MISSING_CONTENT @ {theme_code} <{_key}> @ C.TDB-R1<DICT>'
                    continue
                
                if not isinstance(d, _type):
                    failures[nCode + j + '01'] = f'TYPE_ERROR @ {_key} <{_type}, {type(d)}> @ C.TDB-R1<DICT>'
                    continue
                
                if isinstance(d, str):
                    d = d.strip()
                    if not len(d):
                        failures[nCode + j + '02'] = f'MISSING_CONTENT @ {_key} <str:>0> @ C.TDB-R1<DICT>'
                        continue
                    
                    if d == NULL_STR:
                        warnings[nCode + j + '02'] = f'CONTENT @ {_key} <NULL_STR> @ C.TDB-R1<DICT>'
                
                elif isinstance(d, (int, float)):
                    if d < 0:
                        failures[nCode + j + '03'] = f'CONTENT @ {_key} <int/float:>=0> @ C.TDB-R1<DICT>'
                        continue
                    
                    if d == NULL_INT:
                        warnings[nCode + j + '03'] = f'CONTENT @ {_key} <NULL_INT> @ C.TDB-R1<DICT>'
                        
                elif isinstance(d, HexColor):
                    if d.check() is None:
                        failures[nCode + j + '11'] = f'CONTENT @ {_key} <HEXCOLOR.CHECK> @ C.TDB-R1<DICT>'
                        continue
                    
                    if _key in (R1.TBG, f'{R1.TBorder}/{R1.TBorder_cl}'): continue  # do not want to compare the background to the background, obviously
                    if R1.TBG not in theme:
                        failures[nCode + j + '1E'] = f'CANNOT_TEST                  <WC_AA, WC_AAA: x1> @ C.TDB-R1<DICT>'
                        failures[nCode + j + '1F'] = f'MISSING_CONTENT              <bg.key IN theme> @ C.TDB-R1<DICT>'

                        continue
                        
                    WC_AA, WC_AAA = check_hex_contrast(theme[R1.TBG], d, contrast_ratio_adjustment_tbl.get(_key, 1.00))

                    if not WC_AA:
                        failures[nCode + j + '2F'] = f'CONTRAST                     <WC_AA @ {_key}> @ C.TDB_R1<DICT>'
                        
                    if not WC_AAA:
                        warnings[nCode + j + '20'] = f'CONTRAST                     <WC_AAA @ {_key}> @ C.TDB_R1<DICT>'
        
        return failures, warnings, not bool(len(failures))
    
        
_TDB_file_versions = {
    T_FRMT.TDB_II.value: 
        [
            'QA2.theme',
            ['QAS_VERSION_II', 'not_flagged', 'not_json', 'no_meta', 'backwards_compatability'],
            'COMP+VII',
            Read.QAS2_theme_file
        ],
    T_FRMT.TDB_R1.value: 
        [
            '0.0.1 <A>',
            ['not_flagged', 'is_json', 'v3'],
            'Original QA3 theme file format',
            Read.ALPHA_ONE
        ],
    T_FRMT.TDB_R2.value:
        [
            '0.0.2 <A>',
            ['flagged_as', 'is_json', 'v3'],
            'QA3 Theme File',
            Read.ALPHA_TWO
        ]
}


contrast_ratio_adjustment_tbl = {
    R1.TWA: 2.25555,
    R1.TAC: 2.0899
}


def TDB_to_DICT(DB: TDB, convert_hexcolor_to_str: bool = False) -> Dict[str, Any]:
    """

    Returns a theme database in the format TDB-R1:DICT
    
    Args:
        DB (TDB): Database instance 

    Returns:
        Dict[str, Any]: TDB-R1:DICT compliant database; used by qa-theme-loader modules.
    """
    
    fnwrap = (lambda x: x) if not convert_hexcolor_to_str else (lambda x: cast(HexColor, x).color)
    
    return {
        R1.FInfo:
            {
                R1.FName: DB.Theme_FileCode,
                R1.FDName: DB.Theme_FileName,
                R1.FAThemes: {
                    R1.FAT_N: DB.Theme_NThemes,
                    **{str(I): theme.theme_code for I, theme in enumerate(DB.Theme_AvailableThemes)}
                }
            },
        **{
            theme.theme_code: 
                {
                    R1.TDName: theme.theme_display_name,
                    
                    R1.TBG: fnwrap(theme.background),
                    R1.TFG: fnwrap(theme.foreground),
                    R1.TAC: fnwrap(theme.accent),
                    R1.TER: fnwrap(theme.error),
                    R1.TWA: fnwrap(theme.warning),
                    R1.TOK: fnwrap(theme.okay),
                    R1.TGR: fnwrap(theme.gray),
                    R1.TFont:
                        {
                            R1.TFont_TTLFF: theme.title_font_face,
                            R1.TFont_FF: theme.font_face,
                            R1.TFont_AFF: theme.font_alt_face,
                            R1.TFont_szSMALL: theme.font_small_size,
                            R1.TFont_szMAIN: theme.font_main_size,
                            R1.TFont_szLARGE: theme.font_large_size,
                            R1.TFont_szTTL: theme.font_title_size,
                            R1.TFont_szXLTTL: theme.font_xl_title_size                       
                        },
                    R1.TBorder:
                        {
                            R1.TBorder_sz: theme.border_size,
                            R1.TBorder_cl: fnwrap(theme.border_color)
                        }
                } 
                for theme in DB.Theme_AvailableThemes
        }
    }
    

def _read_meta(meta: str | Dict[str, str]) -> Tuple[int, bool]:
    global _TDB_file_versions
        
    if isinstance(meta, str):
        assert meta == 'no_meta'
        return T_FRMT.TDB_R1.value, True
    
    assert isinstance(meta, dict)
    
    given_format = meta[R2.M_FRMT]
    expected_ver = _TDB_file_versions[given_format][0]  # type: ignore
    given_ver = meta[R2.M_FVER]
    
    return given_format, (expected_ver == given_ver)  # type: ignore


def ReadData(data: str, path_to_file: str) -> TDB:
    """Automatically chooses the appropriate file version and decodes the provided DATA as per that format.
    
    Currently available formats:
        TDB-R1   (T_FRMT.TDB_R1)    <int>id: 1           
        TDB-R2   (T_FRMT.TDB_R2)    <int>id: 2
        TDB-II   (T_FRMT.TDB_II)    <int>id: 9   

    Args:
        data (str): data read from file

    Raises:
        AttributeError: If unable to read file

    Returns:
        TDB: TDB instance that contains all data from the file. 
        
    Note:
        TDB data that is not present in the file (usually as a result of outdated files) will be marked as 
        NULL_STR ('qaTheme.null') or NULL_INT (0) depending on the type of variable in ___. Be sure to appropriately
        handle such instances. 
    """
    
    global _TDB_file_versions, C_META
    
    data = data.strip()
    assert len(data), 'Invalid data input'
    
    try:
        dP = cast(Dict[str, Any], json.loads(data))
        fmrt, matches = _read_meta(dP.get(C_META, 'no_meta'))
        
        assert matches, 'frmt<lookup>.name != given_name'
        
        fn = _TDB_file_versions[fmrt][-1]
        return fn(dP, path_to_file)  # type: ignore
    
    except Exception as E:
        
        for (name, flags, code, func) in _TDB_file_versions.values():
            if 'not_json' in flags:  # type: ignore
                break
            
        if 'not_json' in flags:  # type: ignore
            sys.stderr.write(f'[LL_WARN] qa_files.qa_theme.read_data: found theme file that does not satisfy the requirement of "JSON". Likely "{name}" file ({code}). Calling {func}\n')

            try:
                return func(data, path_to_file)  # type: ignore
            
            except Exception as E1:
                sys.stderr.write(f'qa_files.qa_theme.read_data <d2>: {E1.__class__.__name__}: {str(E1)}\n')
                raise AttributeError('qa_files.qa_theme.read_data: Error <D2>')
        
        sys.stderr.write(f'qa_files.qa_theme.read_data: {E.__class__.__name__}: {str(E)}\n')
        raise AttributeError ("Provided data cannot be decoded as JSON data OR had invalid data.")
        
        
LATEST_GENERATE_FUNCTION = Generate._latest_ver
