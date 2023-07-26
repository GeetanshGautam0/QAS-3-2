import json, sys, hashlib, datetime, re, random
from qa_functions.qa_std import data_at_dict_path, check_hex_contrast, clamp
from qa_functions.qa_file_handler import _Crypt, ConverterFunctionArgs as CFA
from typing import Tuple, List, Dict, Any, Union, cast
from .qa_files_ltbl import qa_file_enck
from .qa_file_std import load_file_sections, FileType
from dataclasses import dataclass
from enum import Enum


NULL_STR = 'qafile:nullstr'
NULL_INT = 0


C_META = 'meta'
C_CONTENT = 'body'
C_VERIFICATION = 'verification'
FF_STATIC_KEY = 'QAP.SKS.FileFormat'


class DataType(Enum):
    (boolean, integer, string) = range(3)


@dataclass
class DataEntry:
    name: str
    index: int
    size: int
    type: DataType


class Data0:
    # Entries
    AutoMark  = DataEntry('auto_mark', 0, 1, DataType.boolean)
    Fuzzy     = DataEntry('fuzzy', 1, 1, DataType.boolean)
    FuzzyThrs = DataEntry('fuzzy:threshold', 2, 2, DataType.integer)

    entries = [AutoMark, Fuzzy, FuzzyThrs]


class Data1:
    QuestionType = DataEntry('qType', 0, 2, DataType.string)
    exD1 = DataEntry('e::1', 1, 1, DataType.boolean)

    entries = [QuestionType, exD1]
    exEntries = [exD1]


class ReadMode(Enum):
    BackComp = 0
    NewGen = 1


class QA_FRMT(Enum):
    BComp = 0
    ALPHA_ONE = 1
    ALPHA_TWO = 2


class VerificationStatus(Enum):
    UNAVAILABLE = 2
    PASSED = 1
    FAILED = 0


@dataclass
class Configuration:
    AllowCustomQuizConfiguration:       bool
    DS_SubsetMode:                      bool    # "p"
    DS_SubsetDiv:                       int
    DS_RandomizeQuestionOrder:          bool
    RM_Deduct:                          bool
    RM_DeductionAmount:                 int   


@dataclass
class Question:
    D0:                                 str
    question:                           str
    answer:                             Union[Dict[str, Union[int, str]], str]
    D1:                                 str


@dataclass
class QuestionAnswerDB:
    App_Version:                str
    App_Build:                  str
    App_IVersion:               int
    App_BuildInfo:              str
    App_InDevMode:              bool

    File_Version:               str
    File_Format:                int
    File_CreateTime:            str
    File_ReadMode:              int
    
    Data_Name:                  str    
    Data_Configuration:         Configuration
    Data_Questions:             List[Question]
    
    Data_Verification_Avail:    bool
    Data_Verification_Status:   int
    Data_VerificationInfo:      List[int | str]  # <N_ITEMS> (Meta, Configuration, Questions)
    
    ProtectionMode_QUIZ:        List[bool | str]
    ProtectionMode_DB:          List[bool | str]
    

class BACK_COMP:
    _KEY = b'FJf5hmYl7OiaUkOpiU-7xrrGtRaN_11mSRjiG6xf_ps='
    
    META_APP_VERSION = {
        'KEY': '<<QA::COMPATABILITY::FILE_VERSION>>',
        'SEP': '::',
        'VAL': '2.0'
    }
    
    CODE_CONFIG_SECTION_START = '<%%QAS-CONFIGURATION--IMPORT--%%>'
    CODE_QAS_SECTION_START = '<%%QAS--QUESTIONS--IMPORT--%%>'
    CODE_SECTION_END = '<%%QAS-IMPORT-END_DIV%%>'
    
    CONTENT_CONFIG = {
        # key: (type, critical data, allowable values (any represents any values))
        'ttl': (str, False, (any, )),
        'acqc': (bool, True, ('true', 'false')),
        'qpoa': (str, True, ('part', 'all')),
        'qsdf': (int, True, (any, )),
        'dma': (bool, True, ('true', 'false')),
        'pdpir': (int, True, (any, )),
        'dist': (bool, False, (any, ))
    }
    
    CONTENT_QAS_CODE_ENTRY_SEP =            '\n'
    CONTENT_QAS_CODE_QA_SEP =               '<<%%QA::0&000003%%>>'
    CONTENT_QAS_CODE_SPACE =                '<<%%QA::0&000002%%>>'
    CONTENT_QAS_CODE_NLCR =                 '<<%%QA::0&000001%%>>'

    CONTENT_QAS_LVL2CODE_MCQ =              '<QAS :: MC_set?True>'
    CONTENT_QAS_LVL2CODE_TFQ =              '<<QAS :: T/F>>'
    CONTENT_QAS_LVL3CODE_MCQ_OPTION =       '[QAS::Option]'
    

class ALPHA_ONE:
    L1_INFO_KEY = 'DB'
    L1_QBANK_KEY = 'QUESTIONS'    
    L1_CONFIG_KEY = 'CONFIGURATION'
    
    L2_CONFIG_ACC = ('acc', bool)
    L2_CONFIG_POA = ('poa', (str, 'p', 'a'))
    L2_CONFIG_RQO = ('rqo', bool)
    L2_CONFIG_SSD = ('ssd', int)
    L2_CONFIG_DPI = ('dpi', bool)
    L2_CONFIG_A2D = ('a2d', int)
    
    L2_META_NAME = 'name'
    L2_META_DPSW = 'psw'
    L2_META_QPSW = 'q_psw'
    
    L2_QBANK_D1 = '0'
    L2_QBANK_Q =  '1'
    L2_QBANK_A =  '2'
    L2_QBANK_D0 = 'd'
    
    SPEC_EXPECTED_N_D0_ENTRIES = 3


class ALPHA_TWO:
    M_FileFormat =              'CMFF'
    M_FileVersion =             'CMFV'
    M_ReadMode =                'CMRM'
    M_FileGenTime =             'CMFGT'
    M_DBName =                  'CMDBN'
    
    M_AppBuild =                'CMAB'
    M_AppVersion =              'CMAVS'
    M_AppIVersion =             'CMAVI'
    M_AppDevMode =              'CMADM'
    M_AppBuildInfo =            'CMABI'
    
    
    ProtectionConfig =          'prtc'
    
    P_Quiz =                    'CPQZ'
    P_Database =                'CPDB'
    
    C_Configuration =           'CCCF'
    C_QuestionBank =            'CCQB'
    
    V_P =                       'CVPC'
    V_CCCF =                    'CVCF'
    V_CCQB =                    'CVQB'
    V_META =                    'CCMT'
    
    CCCF_ACC =                  'CACC'
    CCCF_SSE =                  'CSSE'
    CCCF_SSD =                  'CSSD'
    CCCF_RQO =                  'CRQO'
    CCCF_PDE =                  'CPDE'
    CCCF_ATD =                  'CATD'
    
    CCQB_D0 =                   'd'
    CCQB_D1 =                   '3'
    CCQB_Q =                    '1'
    CCQB_A =                    '0'
    
    VERI_N_IT = 4
    
    VERI_META = 1
    VERI_CCCF = 2
    VERI_PRTC = 3
    VERI_CCQB = 4
    
    PROTECTION_HASH_FNC = hashlib.sha3_512
    

class Read:
    @staticmethod
    def mode_bck_comp(raw_data: str) -> QuestionAnswerDB:
        global _qa_file_versions
        
        E, Q, C = 'SC_END', 'SC_QAI', 'SC_CON'
        
        assert isinstance(raw_data, str),                           '0xBC00000000'  # Input: TypeError
        assert len(raw_data),                                       '0xBC00000000'  # Input: ValueError
        assert raw_data.count('\n'),                                '0xBC00000000'  # Input: ValueError
        
        raw_data = raw_data.strip()
        
        meta_line = raw_data.split('\n')[0]
        raw_data = raw_data.replace(meta_line, '')
        
        assert BACK_COMP.META_APP_VERSION['KEY'] not in raw_data,   '0xBC00000010'
        assert BACK_COMP.META_APP_VERSION['KEY'] in meta_line,      '0xBC00000011'
        assert BACK_COMP.META_APP_VERSION['SEP'] in meta_line,      '0xBC00000012'
        assert BACK_COMP.META_APP_VERSION['VAL'] in meta_line,      '0xBC00000013'
        
        assert meta_line.index(BACK_COMP.META_APP_VERSION['KEY']) \
            == 0,                                                   '0xBC00000020'
        
        meta_line = meta_line.replace(BACK_COMP.META_APP_VERSION['KEY'], 'mode', 1)
        
        meta_split = list(map(
            lambda x: x.strip(), 
            meta_line.split(BACK_COMP.META_APP_VERSION['SEP'])
        ))
                
        assert len(meta_split) == 2,                                '0xBC00000031'
        assert meta_split[0] == 'mode',                             '0xBC00000032'
        assert meta_split[1] == BACK_COMP.META_APP_VERSION['VAL'],  '0xBC00000033'
        
        section_codes = []
        section_codes.extend([E for _ in range(raw_data.count(BACK_COMP.CODE_SECTION_END))])
        section_codes.extend([Q for _ in range(raw_data.count(BACK_COMP.CODE_QAS_SECTION_START))])
        section_codes.extend([C for _ in range(raw_data.count(BACK_COMP.CODE_CONFIG_SECTION_START))])
        
        #                                                              ----||xx
        assert len(section_codes) % 2 == 0,                         '0xBC00000100'  # SC Error: Invalid/corrupted/missing
        assert section_codes.count(Q) == 1,                         '0xBC00000111'  # SC Error: I
        assert section_codes.count(C) == 1,                         '0xBC00000112'  # SC Error: I
        assert (section_codes.count(Q) + section_codes.count(C)) \
            == section_codes.count(E),                              '0xBC00000120'  # SC Error: I/C/M
        
        CS = raw_data.index(BACK_COMP.CODE_CONFIG_SECTION_START)
        QS = raw_data.index(BACK_COMP.CODE_QAS_SECTION_START)        

        assert CS < QS,                                             '0xBC00000130'  # SC Error: I/C
        
        CE = raw_data.index(BACK_COMP.CODE_SECTION_END)
        
        assert CS < CE < QS,                                        '0xBC00000131'  # SC Error: I/C
        
        CONFIG_SECT = raw_data[CS:CE + len(BACK_COMP.CODE_SECTION_END)]                               
        raw_data = raw_data.replace(CONFIG_SECT, '')
        assert len(CONFIG_SECT),                                    '0xBC00000132'  # SC Error: M
        assert BACK_COMP.CODE_SECTION_END in raw_data,              '0xBC00000133'  # SC Error: I/C
        
        QS = raw_data.index(BACK_COMP.CODE_QAS_SECTION_START)       # Index values change when data is removed therefore a new 
                                                                    # start point is required.    
        QE = raw_data.index(BACK_COMP.CODE_SECTION_END)
        assert QS < QE,                                             '0xBC00000140'  # SC Error: I/C
        
        QUESTION_SECTION = raw_data[QS:QE + len(BACK_COMP.CODE_SECTION_END)]
        assert len(QUESTION_SECTION),                               '0xBC00000141'  # SC Error: M
        raw_data = raw_data.replace(QUESTION_SECTION, '').strip()
        assert not len(raw_data),                                   '0xBC00000142'  # SC Error: I/C
        
        configuration: Dict[str, Union[int, bool, str]] = {}
        
        for ENTRY in CONFIG_SECT.split('\n'):
            ENTRY = ENTRY.strip()
            if not len(ENTRY): continue
            if BACK_COMP.CODE_CONFIG_SECTION_START in ENTRY or BACK_COMP.CODE_SECTION_END in ENTRY:
                continue
            
            sys.stdout.write('conf.read ' + ENTRY + '\n')
            
            k, v = ENTRY.split(' ', 1)
            k = k.strip()
            v = v.strip()
            
            assert not (bool(len(k)) ^ bool(len(v))),               '0xBC00000210'
            if not len(k) and not len(v): continue
            configuration[k] = v
            
        for i, (key, (tp, cd, vals)) in enumerate(BACK_COMP.CONTENT_CONFIG.items()):
            f = hex(i)[2:]
            
            assert not cd or key in configuration,                 f'0xBC{f}000022A'
            if any not in vals:
                assert not cd or configuration[key] in vals,       f'0xBC{f}000022B'
            
            configuration[key] = {
                'true': True,
                'false': False
            }.get(configuration[key], configuration[key])  # type: ignore
            
            try:
                configuration[key] = tp(configuration[key])
            except Exception as _:
                assert not cd,                                     f'0xBC{f}000022C'
        
        configuration_inst = Configuration(
            configuration['acqc'],  # type: ignore
            configuration['qpoa'][0].lower() == 'p',  # type: ignore
            configuration['qsdf'],  # type: ignore
            True,  # type: ignore
            configuration['dma'],  # type: ignore
            configuration['pdpir']  # type: ignore
        )    
        
        questions: Dict[str, Question] = {}
        
        for i, ENTRY in enumerate(QUESTION_SECTION.split(BACK_COMP.CONTENT_QAS_CODE_ENTRY_SEP)):    
            
            n_zeros = clamp(0, (6 - len(hex(i))), 9e9)
            code_base = hex(i) + ('0' * n_zeros)  # type: ignore
            code_base = f'0xBC{code_base[2::]}'
            
            ENTRY = ENTRY.strip()
            if not len(ENTRY): continue
            if BACK_COMP.CODE_QAS_SECTION_START in ENTRY or BACK_COMP.CODE_SECTION_END in ENTRY:
                continue
            
            q, a = ENTRY.split(BACK_COMP.CONTENT_QAS_CODE_QA_SEP, 1)
            q = q.replace(BACK_COMP.CONTENT_QAS_CODE_NLCR, '\n').replace(BACK_COMP.CONTENT_QAS_CODE_SPACE, ' ').strip()
            a = a.replace(BACK_COMP.CONTENT_QAS_CODE_NLCR, '\n').replace(BACK_COMP.CONTENT_QAS_CODE_SPACE, ' ').strip()
            
            if BACK_COMP.CONTENT_QAS_LVL2CODE_MCQ in q:
                q = q.replace(BACK_COMP.CONTENT_QAS_LVL2CODE_MCQ, '', 1).strip()
                
                if q.count(BACK_COMP.CONTENT_QAS_LVL3CODE_MCQ_OPTION) <= 1:
                    sys.stderr.write(f'<Auto-WeakHandling> {code_base}A31A\n')
                    continue
                
                # Extracting options
                options = q.split(BACK_COMP.CONTENT_QAS_LVL3CODE_MCQ_OPTION)
                options_map = {}
                q = options.pop(0).strip()
                correct_options = []
                
                for j, option in enumerate(options):
                    option = option.strip()
                    if BACK_COMP.CONTENT_QAS_LVL3CODE_MCQ_OPTION in option:
                        assert option.index(BACK_COMP.CONTENT_QAS_LVL3CODE_MCQ_OPTION) == 0, f'{code_base}0400'
                        option = option.removeprefix(BACK_COMP.CONTENT_QAS_LVL3CODE_MCQ_OPTION).strip()
                    
                    assert len(option) > 3,                         f'{code_base}0410 + {hex(j)}'
                    assert option.startswith('['),                  f'{code_base}0411 + {hex(j)}'
                    assert ']' in option,                           f'{code_base}0412 + {hex(j)}'
                    
                    handle_start = 1
                    handle_end = option.index(']')
                    
                    handle = option[handle_start:handle_end].strip()
                    assert len(handle),                             f'{code_base}0413 + {hex(j)}'
                    assert '[' not in handle and ']' not in handle, f'{code_base}0414 + {hex(j)}'
                    
                    options_map[handle] = {
                        'id': code_base,
                        'index': j,
                        'correct': (a == handle),
                        'data': option.replace(f'[{handle}]', '', 1).strip()
                    }
                    
                    if a == handle:
                        correct_options.append(str(j))
                    
                assert a in options_map,                            f'0x00000501'
                assert len(options_map) > 1,                        f'0x00000502'         
                
                s = ['0' for _ in range(sum(map(lambda x: cast(DataEntry, x).size, Data0.entries)))]  # type: ignore
                assert len(Data0.entries) == 3, 'INTERNAL_ERROR: update database management'
                
                s[Data0.AutoMark.index] = '1'
                s[Data0.Fuzzy.index] = '1'
                
                questions[code_base] = Question(''.join(s) + '0', q, {
                    "C": "/".join(correct_options).strip('/'),
                    "N": len(options_map),
                    **{
                        str(opt['index']): opt['data'] for opt in options_map.values()  # type: ignore
                    }
                }, 'mc0')               
                
            elif BACK_COMP.CONTENT_QAS_LVL2CODE_TFQ in q:
                q = q.replace(BACK_COMP.CONTENT_QAS_LVL2CODE_TFQ, '', 1).strip()
                
                if not (('t' in a.lower()) ^ ('f' in a.lower())):
                    sys.stderr.write(f'<Auto-WeakHandling> {code_base}A31D\n')
                    continue
                
                s = ['0' for _ in range(sum(map(lambda x: cast(DataEntry, x).size, Data0.entries)))]  # type: ignore
                assert len(Data0.entries) == 3, 'INTERNAL_ERROR: update database management'
                
                s[Data0.AutoMark.index] = '1'
                s[Data0.Fuzzy.index] = '1'
                
                questions[code_base] = Question(''.join(s) + '0', q, '1' if ('t' in a) else '0', 'tf')
                
            else:
                if not len(a):
                    sys.stderr.write(f'<Auto-WeakHandling> {code_base}A31E\n')
                    continue
                
                s = ['0' for _ in range(sum(map(lambda x: cast(DataEntry, x).size, Data0.entries)))]  # type: ignore
                assert len(Data0.entries) == 3, 'INTERNAL_ERROR: update database management'
                
                s[Data0.AutoMark.index] = '1'
                s[Data0.Fuzzy.index] = '1'
                
                questions[code_base] = Question(''.join(s) + '0', q.strip(), a.strip(), 'nm')
            
            if not len(q) or not len(a): continue
        
        sys.stdout.write('Found questions:\n\t' + '\n\t'.join(questions.keys()) + '\n')
        
        return QuestionAnswerDB(
            'qa2', NULL_STR, 2, NULL_STR, False,
            NULL_STR, NULL_INT, NULL_STR, ReadMode.BackComp.value, 
            f'PORTED_DATABASE {random.randint(1e10, 1e11)}.{random.random()}',  # type: ignore
            configuration_inst, list(questions.values()), False, VerificationStatus.UNAVAILABLE.value,
            [0], [False, ''], [False, ''] 
        )
    
    @staticmethod
    def alpha_one(data: Dict[str, Any]) -> QuestionAnswerDB:
        global _qa_file_versions
        
        assert isinstance(data, dict),                              '0xA100000000'
        
        assert ALPHA_ONE.L1_INFO_KEY in data,                       '0xA100000100'
        assert ALPHA_ONE.L1_CONFIG_KEY in data,                     '0xA100000101'
        assert ALPHA_ONE.L1_QBANK_KEY in data,                      '0xA100000102'
        
        assert isinstance(data[ALPHA_ONE.L1_INFO_KEY], dict),       '0xA100000200'
        assert isinstance(data[ALPHA_ONE.L1_CONFIG_KEY], dict),     '0xA100000201'
        assert isinstance(data[ALPHA_ONE.L1_QBANK_KEY], dict),      '0xA100000201'
        
        meta: Dict[str, Any] = data[ALPHA_ONE.L1_INFO_KEY]         
         
        assert isinstance(meta.get(ALPHA_ONE.L2_META_NAME), str),   '0xA100000300'
        assert isinstance(meta.get(ALPHA_ONE.L2_META_DPSW), list),  '0xA100000301'
        assert isinstance(meta.get(ALPHA_ONE.L2_META_QPSW), list),  '0xA100000302'
        
        qpsw = meta[ALPHA_ONE.L2_META_QPSW]
        dpsw = meta[ALPHA_ONE.L2_META_DPSW]
        
        assert len(meta[ALPHA_ONE.L2_META_NAME].strip()),           '0xA100000310'
        assert len(dpsw) == 2,                                      '0xA100000311'
        assert len(qpsw) == 2,                                      '0xA100000312'
        assert isinstance(dpsw[0], bool),                           '0xA100000321'
        assert isinstance(qpsw[0], bool),                           '0xA100000322'
        assert isinstance(dpsw[1], str),                            '0xA100000331'
        assert isinstance(qpsw[1], str),                            '0xA100000332'
        
        config = data[ALPHA_ONE.L1_CONFIG_KEY]
        assert len(config),                                         '0xA100000400'
        
        assert ALPHA_ONE.L2_CONFIG_ACC[0] in config,                '0xA101000401'
        assert isinstance(config[ALPHA_ONE.L2_CONFIG_ACC[0]], 
                          ALPHA_ONE.L2_CONFIG_ACC[1]),              '0xA101000402'

        assert ALPHA_ONE.L2_CONFIG_POA[0] in config,                '0xA102000401'
        assert isinstance(config[ALPHA_ONE.L2_CONFIG_POA[0]],
                          ALPHA_ONE.L2_CONFIG_POA[1][0]),           '0xA102000402'
        assert config[ALPHA_ONE.L2_CONFIG_POA[0]] in \
            ALPHA_ONE.L2_CONFIG_POA[1][1::],                        '0xA102000403'
        
        assert ALPHA_ONE.L2_CONFIG_RQO[0] in config,                '0xA103000401'
        assert isinstance(config[ALPHA_ONE.L2_CONFIG_RQO[0]],
                          ALPHA_ONE.L2_CONFIG_RQO[1]),              '0xA103000402'
        
        assert ALPHA_ONE.L2_CONFIG_SSD[0] in config,                '0xA104000401'
        assert isinstance(config[ALPHA_ONE.L2_CONFIG_SSD[0]],
                          ALPHA_ONE.L2_CONFIG_SSD[1]),              '0xA104000402'
        
        if config[ALPHA_ONE.L2_CONFIG_POA[0]] == 'p':
            assert config[ALPHA_ONE.L2_CONFIG_SSD[0]] > 0,          '0xA104000403'
            
        assert ALPHA_ONE.L2_CONFIG_DPI[0] in config,                '0xA105000401'
        assert isinstance(config[ALPHA_ONE.L2_CONFIG_DPI[0]],
                          ALPHA_ONE.L2_CONFIG_DPI[1]),              '0xA105000402'
        
        assert ALPHA_ONE.L2_CONFIG_A2D[0] in config,                '0xA106000401'
        assert isinstance(config[ALPHA_ONE.L2_CONFIG_A2D[0]],
                          ALPHA_ONE.L2_CONFIG_A2D[1]),              '0xA106000402'
        
        questions: Dict[str, Any] = data[ALPHA_ONE.L1_QBANK_KEY]
        questions_cl: Dict[str, Question] = {}
        
        for i, question in enumerate(questions.values()):
            code_base = hex(i)
            code_base = code_base + "0" * clamp(0, (6 - len(code_base)), 9e9)  # type: ignore
            code_base = f'0xA1{code_base[2::]}'
            
            assert isinstance(question, dict),                      f'{code_base}F500' 
            assert ALPHA_ONE.L2_QBANK_D0 in question,               f'{code_base}F501'
            assert ALPHA_ONE.L2_QBANK_D1 in question,               f'{code_base}F502'
            assert ALPHA_ONE.L2_QBANK_Q in question,                f'{code_base}F503'
            assert ALPHA_ONE.L2_QBANK_A in question,                f'{code_base}F504'
                
            d0 = question[ALPHA_ONE.L2_QBANK_D0]
            d1 = question[ALPHA_ONE.L2_QBANK_D1]
            q = question[ALPHA_ONE.L2_QBANK_Q]
            a = question[ALPHA_ONE.L2_QBANK_A]
            
            assert isinstance(d1, str),                             f'{code_base}0501'
            assert isinstance(d0, str),                             f'{code_base}0502'
            assert isinstance(q, str),                              f'{code_base}0503'
            
            d1 = d1.strip()
            d0 = d0.strip()
            q = q.strip()
            
            assert d1 in ('nm', 'mc0', 'mc1', 'tf'),                f'{code_base}0511'
            assert len(q),                                          f'{code_base}0513'
            
            exp_len = sum(
                map(
                    lambda x: cast(DataEntry, x).size,  # type: ignore
                    Data0.entries
                )
            ) + 1
            
            assert len(d0) == exp_len,                              f'{code_base}0512'
            
            d0_a = d0[Data0.AutoMark.index:Data0.AutoMark.index + Data0.AutoMark.size]
            d0_f = d0[Data0.Fuzzy.index:Data0.Fuzzy.index + Data0.Fuzzy.size]
            d0_t = d0[Data0.FuzzyThrs.index:Data0.FuzzyThrs.index + Data0.FuzzyThrs.size]
            d0_e = d0[-1]
            
            try:
                assert d0_a in ('0', '1')
                assert d0_f in ('0', '1')
                assert d0_e in ('0', '1')
                
                int(d0_t)
                
            except Exception as _:
                assert False,                                       f'{code_base}0522'
            
            if 'mc' in d1:
                assert d1[-1] == d0[-1],                            f'{code_base}0524'
                assert isinstance(a, dict),                         f'{code_base}0534'
                assert 'N' in a and 'C' in a,                       f'{code_base}0544'
                assert isinstance(a['N'], int) and \
                    isinstance(a['C'], str),                        f'{code_base}0554'
                assert a['N'] > 0,                                  f'{code_base}0564'
                
                assert len(a) == a['N'] + 2,                        f'{code_base}0574'
                c = a['C'].split('/')                                      

                assert bool(len(c)) and bool(len(a['C'])),          f'{code_base}0584'
                for ind in c:
                    try: int(ind)
                    except Exception as _: assert False,            f'{code_base}0594'
                    
                    assert ind in a,                                f'{code_base}05A4'
                
            elif d1 == 'tf':
                assert a in ('0', '1'),                             f'{code_base}0524'
                
            elif d1 == 'nm':
                assert isinstance(a, str),                          f'{code_base}0524'
                a = a.strip()
            
            else:
                assert False,                                       f'{code_base}B511'
            
            questions_cl[code_base] = Question(d0, q, a, d1)
                        
        conf = Configuration(
            config[ALPHA_ONE.L2_CONFIG_ACC[0]],
            config[ALPHA_ONE.L2_CONFIG_POA[0]] == 'p',
            config[ALPHA_ONE.L2_CONFIG_SSD[0]],
            config[ALPHA_ONE.L2_CONFIG_RQO[0]],
            config[ALPHA_ONE.L2_CONFIG_DPI[0]],
            config[ALPHA_ONE.L2_CONFIG_A2D[0]]
        )
        
        sys.stdout.write('Found questions:\n\t' + '\n\t'.join(questions_cl.keys()) + '\n')
        
        return QuestionAnswerDB(
            'qa3', NULL_STR, 3,
            NULL_STR, False, _qa_file_versions[QA_FRMT.ALPHA_ONE.value],  # type: ignore
            QA_FRMT.ALPHA_ONE.value, NULL_STR,
            ReadMode.NewGen.value,
            meta[ALPHA_ONE.L2_META_NAME],
            conf, list(questions_cl.values()),
            False, VerificationStatus.UNAVAILABLE.value,
            [0], qpsw, dpsw
        )
        
    @staticmethod
    def alpha_two(data: Dict[str, Any]) -> QuestionAnswerDB:
        global C_META, C_CONTENT, C_VERIFICATION, _qa_file_versions, FF_STATIC_KEY
        
        assert isinstance(data, dict),                  '0xA200000000'
        assert C_META in data,                          '0xA200000010'
        assert C_CONTENT in data,                       '0xA200000011'
        assert C_VERIFICATION in data,                  '0xA200000012'
        assert FF_STATIC_KEY in data,                   '0xA200000013'
        assert ALPHA_TWO.ProtectionConfig in data,      '0xA200000014'
        assert 'gg.attr' in data,                       '0xA200000015'
        assert data['gg.attr'] == '%.qafile',            '0xA200000016'
        
        assert data[FF_STATIC_KEY] == \
            QA_FRMT.ALPHA_TWO.value,                    '0xA200000020'
        assert ALPHA_TWO.P_Database in \
            data[ALPHA_TWO.ProtectionConfig],           '0xA200000021'
        assert ALPHA_TWO.P_Quiz in \
            data[ALPHA_TWO.ProtectionConfig],           '0xA200000022'
        
        PRTC = data[ALPHA_TWO.ProtectionConfig]
        PRTC_DB = PRTC[ALPHA_TWO.P_Database]
        PRTC_QZ = PRTC[ALPHA_TWO.P_Quiz]
        
        assert isinstance(PRTC_DB, list),               '0xA200000030'
        assert isinstance(PRTC_QZ, list),               '0xA200000031'
        assert len(PRTC_DB) == 2,                       '0xA200000040'
        assert len(PRTC_QZ) == 2,                       '0xA200000041'
        assert isinstance(PRTC_DB[0], bool),            '0xA200000050'
        assert isinstance(PRTC_QZ[0], bool),            '0xA200000051'
        assert isinstance(PRTC_DB[1], str),             '0xA200000060'
        assert isinstance(PRTC_QZ[1], str),             '0xA200000061'
        
        META = data[C_META]
        CMAVS, CMAVS_T = (META[ALPHA_TWO.M_AppVersion], str)
        CMAVI, CMAVI_T = (META[ALPHA_TWO.M_AppIVersion], int)
        CMABI, CMABI_T = (META[ALPHA_TWO.M_AppBuildInfo], str)
        CMADM, CMADM_T = (META[ALPHA_TWO.M_AppDevMode], bool)
        CMFGT, CMFGT_T = (META[ALPHA_TWO.M_FileGenTime], str)
        CMDBN, CMDBN_T = (META[ALPHA_TWO.M_DBName], str)
        CMVID, CMVID_T = (META['CMVID'], str)
        CMAB, CMAB_T  = (META[ALPHA_TWO.M_AppBuild], str)
        CMFF, CMFF_T  = (META[ALPHA_TWO.M_FileFormat], int)
        CMFV, CMFV_T  = (META[ALPHA_TWO.M_FileVersion], str)
        CMRM, CMRM_T  = (META[ALPHA_TWO.M_ReadMode], int)
        CMCH  = b'6cb6a5d535719aaf4e9dcb7035ff5590'

        assert isinstance(CMAVS, CMAVS_T),              '0xA200000100'
        assert isinstance(CMAVI, CMAVI_T),              '0xA200000101'
        assert isinstance(CMABI, CMABI_T),              '0xA200000102'
        assert isinstance(CMADM, CMADM_T),              '0xA200000103'
        assert isinstance(CMFGT, CMFGT_T),              '0xA200000104'
        assert isinstance(CMDBN, CMDBN_T),              '0xA200000105'
        assert isinstance(CMVID, CMVID_T),              '0xA200000106'
        assert isinstance(CMAB, CMAB_T),                '0xA200000107'
        assert isinstance(CMFF, CMFF_T),                '0xA200000108'
        assert isinstance(CMFV, CMFV_T),                '0xA200000109'
        assert isinstance(CMRM, CMRM_T),                '0xA20000010A'
        
        assert CMFF == data[FF_STATIC_KEY],             '0xA200000110'
        
        CMVID_E = hashlib.md5(
            CMCH +
            _qa_file_versions[QA_FRMT.ALPHA_TWO.value][0].encode() +
            CMDBN.encode()
        ).hexdigest()
        
        assert CMFV == \
            _qa_file_versions[QA_FRMT.ALPHA_TWO.value]\
                [0],                                    '0xA200000112'
        assert CMAVI == 3,                              '0xA200000113'
        
        VERIFICATION = data[C_VERIFICATION]
        fnc = ALPHA_TWO.PROTECTION_HASH_FNC
        
        CVPC, CVPC_E = VERIFICATION[ALPHA_TWO.V_P], _get_dict_hash(data[ALPHA_TWO.ProtectionConfig], fnc)
        CVCF, CVCF_E = VERIFICATION[ALPHA_TWO.V_CCCF], _get_dict_hash(data[C_CONTENT][ALPHA_TWO.C_Configuration], fnc)
        CVQB, CVQB_E = VERIFICATION[ALPHA_TWO.V_CCQB], _get_dict_hash(data[C_CONTENT][ALPHA_TWO.C_QuestionBank], fnc)
        CCMT, CCMT_E = VERIFICATION[ALPHA_TWO.V_META], _get_dict_hash(data[C_META], fnc)
        
        # assert CVPC == CVPC_E,                          '0xA200000120'
        # assert CVCF == CVCF_E,                          '0xA200000121'
        # assert CVQB == CVQB_E,                          '0xA200000122'
        # assert CCMT == CCMT_E,                          '0xA200000123'
        
        verified = True
        
        if CVPC != CVPC_E: verified = False
        if CVCF != CVCF_E: verified = False
        if CVQB != CVQB_E: verified = False
        if CCMT != CCMT_E: verified = False
        
        CCCF = data[C_CONTENT][ALPHA_TWO.C_Configuration]
        CCQB = data[C_CONTENT][ALPHA_TWO.C_QuestionBank]
        
        assert len(CCCF) == 6,                          '0xA200000200'
        
        for i, (KEY, VALUE_TYPE) in enumerate((
            (ALPHA_TWO.CCCF_ACC, bool),                 # Allow Custom Configuration
            (ALPHA_TWO.CCCF_SSE, bool),                 # Subsampling enabled
            (ALPHA_TWO.CCCF_SSD, int),                  # Subsampling divisor
            (ALPHA_TWO.CCCF_RQO, bool),                 # Randomize question order
            (ALPHA_TWO.CCCF_PDE, bool),                 # Penalty: Deductions enabled
            (ALPHA_TWO.CCCF_ATD, int),                  #           Amount to deduct 
        )):
            cd = f'0xA2{clamp(0, 4 - len(hex(i + 1)), 9e9) * "0" + hex(i + 1)[2:]}'  # type: ignore
            
            assert KEY in CCCF,                         f'{cd}0200'
            assert isinstance(CCCF[KEY], VALUE_TYPE),   f'{cd}0201'
            
            
        CCCF_ACC = CCCF[ALPHA_TWO.CCCF_ACC]
        CCCF_SSE = CCCF[ALPHA_TWO.CCCF_SSE]
        CCCF_SSD = CCCF[ALPHA_TWO.CCCF_SSD]
        CCCF_RQO = CCCF[ALPHA_TWO.CCCF_RQO]
        CCCF_PDE = CCCF[ALPHA_TWO.CCCF_PDE]
        CCCF_ATD = CCCF[ALPHA_TWO.CCCF_ATD]
        
        conf = Configuration(CCCF_ACC, CCCF_SSE, CCCF_SSD, CCCF_RQO, CCCF_PDE, CCCF_ATD)
        questions = []
        
        for i, (QC, Q) in enumerate(CCQB.items()):
            EC = '0x' + clamp(0, 12 - len(hex(i)), 9e9) * '0' + hex(i)[2::]  # type: ignore
            assert isinstance(QC, str),                 f'0xA200000300 @ {EC}'
            assert EC == QC,                            f'0xA200000301 @ {EC}'
            assert isinstance(Q, dict),                 f'0xA200000302 @ {EC}'
            assert ALPHA_TWO.CCQB_Q in Q,               f'0xA200000303 @ {EC}'
            assert ALPHA_TWO.CCQB_A in Q,               f'0xA200000304 @ {EC}'
            assert ALPHA_TWO.CCQB_D0 in Q,              f'0xA200000305 @ {EC}'
            assert ALPHA_TWO.CCQB_D1 in Q,              f'0xA200000306 @ {EC}'
            
            D0 = Q[ALPHA_TWO.CCQB_D0]
            D1 = Q[ALPHA_TWO.CCQB_D1]
            A = Q[ALPHA_TWO.CCQB_A]
            Q = Q[ALPHA_TWO.CCQB_Q]
            
            assert isinstance(D0, str),                 f'0xA200001300 @ {EC}'
            assert D1 in ('mc0', 'mc1', 'nm', 'tf'),    f'0xA200001301 @ {EC}'
            assert isinstance(Q, str),                  f'0xA200001303 @ {EC}'   
            assert len(Q),                              f'0xA200001304 @ {EC}'
            
            if D1 in ('mc0', 'mc1'):
                assert D1[-1] == D0[-1],                f'0xA200011302 @ {EC}'
                assert isinstance(A, dict),             f'0xA200011304 @ {EC}'
                assert 'C' in A and 'N' in A,           f'0xA200011314 @ {EC}'
                assert isinstance(A['C'], str),         f'0xA200011324 @ {EC}'
                assert isinstance(A['N'], int),         f'0xA200011334 @ {EC}'
                assert A['N'] == len(A) - 2,            f'0xA200011344 @ {EC}'
                
                A['C'] = A['C'].strip()
                assert len(A['C']),                     f'0xA200011354 @ {EC}'
                assert min([v in A for v in A['C'].split('/')]), \
                                                        f'0xA200011364 @ {EC}'
                opts = {**A}
                opts.pop('C')
                opts.pop('N')
                
                assert min([isinstance(s, str) for s in opts]), \
                                                        f'0xA200011374 @ {EC}'

                opts = {k: s.strip() for k, s in opts.items()}
                
                assert min([len(s) > 0 for s in opts]), f'0xA200011384 @ {EC}'
                assert len(opts) >= 2,                  f'0xA200011394 @ {EC}'
                
                A = {k: opts.get(k, A[k]) for k in A.keys()}
                
            elif D1 == 'tf':
                assert isinstance(A, str),              f'0xA200021302 @ {EC}'
                assert A in ('0', '1'),                 f'0xA200021303 @ {EC}'
                assert D0[Data0.AutoMark.index] == '1', f'0xA200021304 @ {EC}'
                assert D0[Data0.Fuzzy.index] == '0',    f'0xA200021314 @ {EC}'
                assert D0[-1] == '0',                   f'0xA200021324 @ {EC}'
                
            elif D1 == 'nm':
                assert isinstance(A, str),              f'0xA200031302 @ {EC}'
                A = A.strip()
                assert len(A),                          f'0xA200031303 @ {EC}'
                assert D0[-1] == '0',                   f'0xA200021304 @ {EC}'
                
            else:
                raise Exception(                        f'0xA200040000 @ {EC}')         
            
            questions.append(Question(D0, Q, A, D1))
            sys.stdout.write(f'Found question {EC}\n')
        
        verification_data = [ALPHA_TWO.VERI_N_IT, *['' for _ in range(ALPHA_TWO.VERI_N_IT)]]
        verification_data[ALPHA_TWO.VERI_PRTC] = CVPC
        verification_data[ALPHA_TWO.VERI_CCCF] = CVCF
        verification_data[ALPHA_TWO.VERI_CCQB] = CVQB
        verification_data[ALPHA_TWO.VERI_META] = CCMT
        
        return QuestionAnswerDB(
            CMAVS, CMAB, CMAVI, CMABI, CMADM, CMFV, CMFF,
            CMFGT, CMRM, CMDBN, conf, questions, True,
            VerificationStatus.PASSED.value if (CMVID == CMVID_E) and verified \
                else VerificationStatus.FAILED.value, 
            verification_data, PRTC_QZ, PRTC_DB  # type: ignore
        )
            

def _get_dict_hash(data: Dict[str, Any], fnc: Any) -> str:
    jd = json.dumps(data)
    return fnc(jd.encode()).hexdigest()  # type: ignore


class Generate:
    @staticmethod
    def ALPHA_TWO(
        App_Version: str,
        App_Build: str,
        App_IVersion: int,
        App_BuildInfo: str,
        App_InDevMode: bool,
        Database_Name: str,
        configuration: Configuration,
        Questions: List[Question],
        DataProtection_QUIZ: List[bool | str],  # Enabled?, hash for password
        DataProtection_ATDB: List[bool | str]
    ) -> Tuple[Dict[str, Any], QuestionAnswerDB, str]:
        
        global _qa_file_versions, C_META, C_CONTENT, C_VERIFICATION, FF_STATIC_KEY

        assert isinstance(App_Version, str)
        assert isinstance(App_Build, str)
        assert isinstance(App_IVersion, int)
        assert isinstance(App_BuildInfo, str)
        assert isinstance(App_InDevMode, bool)
        assert isinstance(Database_Name, str)
        assert isinstance(configuration, Configuration)
        assert isinstance(Questions, list)
        assert isinstance(DataProtection_ATDB, list)
        assert isinstance(DataProtection_QUIZ, list)
        assert (len(DataProtection_QUIZ) * len(DataProtection_ATDB)) > 0
        for i in range(len(Questions)): assert isinstance(Questions[i], Question)
        assert isinstance(DataProtection_ATDB[0], bool) and isinstance(DataProtection_ATDB[1], str)
        assert isinstance(DataProtection_QUIZ[0], bool) and isinstance(DataProtection_QUIZ[1], str)
        Database_Name = Database_Name.strip()
        assert len(Database_Name)
        
        dc = {
            'gg.attr': 
                '%.qafile',
            
            FF_STATIC_KEY:
                QA_FRMT.ALPHA_TWO.value,
                
            C_META: 
                {
                    
                    ALPHA_TWO.M_AppVersion: App_Version,
                    ALPHA_TWO.M_AppIVersion: App_IVersion,
                    ALPHA_TWO.M_AppBuild: App_Build,
                    ALPHA_TWO.M_AppBuildInfo: App_BuildInfo,
                    ALPHA_TWO.M_AppDevMode: App_InDevMode,
                    
                    ALPHA_TWO.M_FileFormat: QA_FRMT.ALPHA_TWO.value,
                    ALPHA_TWO.M_FileVersion: _qa_file_versions[QA_FRMT.ALPHA_TWO.value][0],
                    ALPHA_TWO.M_FileGenTime: datetime.datetime.now().strftime('%a, %B %d, %Y - %H:%M:%S'),
                    ALPHA_TWO.M_ReadMode: ReadMode.NewGen.value,
                    ALPHA_TWO.M_DBName: Database_Name,
                    
                    'CMVID': hashlib.md5(
                        b'6cb6a5d535719aaf4e9dcb7035ff5590' +
                        _qa_file_versions[QA_FRMT.ALPHA_TWO.value][0].encode() +
                        Database_Name.encode()
                    ).hexdigest(), 
                    
                    # cr. geetanshgautam
                    
                },
            
            ALPHA_TWO.ProtectionConfig:
                {
                  
                    ALPHA_TWO.P_Database: DataProtection_ATDB,
                    ALPHA_TWO.P_Quiz: DataProtection_QUIZ
                    
                },
            
            C_CONTENT:
                {
                    
                    ALPHA_TWO.C_Configuration:
                        {
                            ALPHA_TWO.CCCF_ACC: configuration.AllowCustomQuizConfiguration,
                            ALPHA_TWO.CCCF_SSE: configuration.DS_SubsetMode,
                            ALPHA_TWO.CCCF_SSD: configuration.DS_SubsetDiv,
                            ALPHA_TWO.CCCF_RQO: configuration.DS_RandomizeQuestionOrder,
                            ALPHA_TWO.CCCF_PDE: configuration.RM_Deduct,
                            ALPHA_TWO.CCCF_ATD: configuration.RM_DeductionAmount
                        },
                        
                    ALPHA_TWO.C_QuestionBank:
                        {
                            ('0x' + clamp(0, 12 - len(hex(i)), 9e9) * '0' + hex(i)[2::]):  # type: ignore
                                {
                                    ALPHA_TWO.CCQB_D1: q.D1,
                                    ALPHA_TWO.CCQB_Q: q.question,
                                    ALPHA_TWO.CCQB_A: q.answer,
                                    ALPHA_TWO.CCQB_D0: q.D0
                                }
                            for i, q in enumerate(Questions)
                        }
                    
                },
                
            C_VERIFICATION:
                {
                    ALPHA_TWO.V_P: '',
                    ALPHA_TWO.V_CCCF: '',
                    ALPHA_TWO.V_CCQB: '',
                    ALPHA_TWO.V_META: ''
                }
        }

        dc[C_VERIFICATION][ALPHA_TWO.V_P] = _get_dict_hash(dc[ALPHA_TWO.ProtectionConfig], ALPHA_TWO.PROTECTION_HASH_FNC)  # type: ignore
        dc[C_VERIFICATION][ALPHA_TWO.V_CCCF] = _get_dict_hash(dc[C_CONTENT][ALPHA_TWO.C_Configuration], ALPHA_TWO.PROTECTION_HASH_FNC)  # type: ignore
        dc[C_VERIFICATION][ALPHA_TWO.V_CCQB] = _get_dict_hash(dc[C_CONTENT][ALPHA_TWO.C_QuestionBank], ALPHA_TWO.PROTECTION_HASH_FNC)  # type: ignore
        dc[C_VERIFICATION][ALPHA_TWO.V_META] = _get_dict_hash(dc[C_META], ALPHA_TWO.PROTECTION_HASH_FNC)  # type: ignore
        
        verification_data = [ALPHA_TWO.VERI_N_IT, *['' for _ in range(ALPHA_TWO.VERI_N_IT)]]
        verification_data[ALPHA_TWO.VERI_PRTC] = dc[C_VERIFICATION][ALPHA_TWO.V_P]  # type: ignore
        verification_data[ALPHA_TWO.VERI_CCCF] = dc[C_VERIFICATION][ALPHA_TWO.V_CCCF]  # type: ignore
        verification_data[ALPHA_TWO.VERI_CCQB] = dc[C_VERIFICATION][ALPHA_TWO.V_CCQB]  # type: ignore
        verification_data[ALPHA_TWO.VERI_META] = dc[C_VERIFICATION][ALPHA_TWO.V_META]  # type: ignore
        
        qadb = QuestionAnswerDB(
            App_Version, App_Build, App_IVersion, App_BuildInfo, App_InDevMode,
            _qa_file_versions[QA_FRMT.ALPHA_TWO.value][0], QA_FRMT.ALPHA_TWO.value,
            dc[C_META][ALPHA_TWO.M_FileGenTime], dc[C_META][ALPHA_TWO.M_ReadMode],  # type: ignore
            Database_Name, configuration, Questions,
            True, VerificationStatus.PASSED, verification_data,  # type: ignore
            DataProtection_QUIZ, DataProtection_ATDB
        )
        
        return dc, qadb, json.dumps(dc, indent=4)
        
    latest = ALPHA_TWO
    
        
def ProduceAlphaOneDict(qadb: QuestionAnswerDB) -> Dict[str, Any]:
    return {
        ALPHA_ONE.L1_INFO_KEY:
            {
                ALPHA_ONE.L2_META_NAME: qadb.Data_Name,
                ALPHA_ONE.L2_META_QPSW: qadb.ProtectionMode_QUIZ,
                ALPHA_ONE.L2_META_DPSW: qadb.ProtectionMode_DB  
            },
        ALPHA_ONE.L1_CONFIG_KEY:
            {
                ALPHA_ONE.L2_CONFIG_ACC[0]: qadb.Data_Configuration.AllowCustomQuizConfiguration,
                ALPHA_ONE.L2_CONFIG_POA[0]: 'p' if qadb.Data_Configuration.DS_SubsetMode else 'a',
                ALPHA_ONE.L2_CONFIG_SSD[0]: qadb.Data_Configuration.DS_SubsetDiv,
                ALPHA_ONE.L2_CONFIG_RQO[0]: qadb.Data_Configuration.DS_RandomizeQuestionOrder,
                ALPHA_ONE.L2_CONFIG_DPI[0]: qadb.Data_Configuration.RM_Deduct,
                ALPHA_ONE.L2_CONFIG_A2D[0]: qadb.Data_Configuration.RM_DeductionAmount
            },
        ALPHA_ONE.L1_QBANK_KEY:
            {
                ('0x' + clamp(0, 12 - len(hex(i)), 9e9) * '0' + hex(i)[2::]): {  # type: ignore
                    ALPHA_ONE.L2_QBANK_D1: q.D1,
                    ALPHA_ONE.L2_QBANK_Q: q.question,
                    ALPHA_ONE.L2_QBANK_A: q.answer,
                    ALPHA_ONE.L2_QBANK_D0: q.D0
                }
                for i, q in enumerate(qadb.Data_Questions)
            },
        'Extras.LFormat': Generate.latest(
            qadb.App_Version,
            qadb.App_Build,
            qadb.App_IVersion,
            qadb.App_BuildInfo,
            qadb.App_InDevMode,
            qadb.Data_Name,
            qadb.Data_Configuration,
            qadb.Data_Questions,
            qadb.ProtectionMode_QUIZ,
            qadb.ProtectionMode_DB
        )[0]
    }

    
def GetReadMode(raw_data: bytes) -> Tuple[ReadMode, bytes]:
    """Returns the read mode information for the qaFile file. 
    Used for backwards compatability purposes.
    

    Args:
        raw_data (bytes): Raw data from file
    
    Returns:
        Tuple(ReadMode, bytes): ReadMode (ENUM), encryption key
    """
    
    return (ReadMode.BackComp, BACK_COMP._KEY) if \
        raw_data[0:2] == 'gA' else (ReadMode.NewGen, qa_file_enck)


_qa_file_versions = {
    QA_FRMT.BComp.value:
        ('BCOMP_MODE', Read.mode_bck_comp, QA_FRMT.BComp),
    QA_FRMT.ALPHA_ONE.value:
        ('ALPHA_ONE', Read.alpha_one, QA_FRMT.ALPHA_ONE),
    QA_FRMT.ALPHA_TWO.value:
        ('ALPHA_TWO', Read.alpha_two, QA_FRMT.ALPHA_TWO),
}


def ReadMeta(meta: Dict[str, Any]) -> QA_FRMT:
    global FF_STATIC_KEY
    
    assert isinstance(meta, dict)
    assert FF_STATIC_KEY in meta
    assert isinstance(meta[FF_STATIC_KEY], int)
    assert meta[FF_STATIC_KEY] in _qa_file_versions and \
        (meta[FF_STATIC_KEY] not in (QA_FRMT.BComp.value, QA_FRMT.ALPHA_ONE.value))
        
    return _qa_file_versions[meta[FF_STATIC_KEY]][2]


def ReadRawData(raw_data: bytes) -> Tuple[QuestionAnswerDB, Dict[str, Any]]:  # type: ignore
    """
    Takes in raw data from a qaFile file, reads it, and returns its
    data as a QADB and an ALPHA_ONE-compliant dictionary containing
    said data.  
    
    ALPHA_ONE-compliance means that the dictionary keys and structure
    from ALPHA_ONE files (for compatability with the quizzing app suite)
    with extra data. 
    
    At the time of the creation of this docstring, this extra data includes:
        (a) file meta data
        (b) app meta data
        (c) verification data

    Args:
        raw_data (bytes): raw data read from the file. use mode 'rb' 

    Returns:
        Tuple[QuestionAnswerDB, Dict[str, Any]]: QADB, A1-compliant dict
    """
    
    global _qa_file_versions, C_META
    rmode, enck = GetReadMode(raw_data)
    
    if (rmode == ReadMode.BackComp):
        sys.stdout.write('[WARN] DB invokes ReadMode.BackComp. Attempting to decrypt using qa2.k\n')
        dec_data = _Crypt.decrypt(raw_data, enck, CFA())
        assert isinstance(dec_data, (str, bytes))
        dec_data = dec_data.strip()
        
        if isinstance(dec_data, bytes):
            str_data = dec_data.decode()
        
        else:
            str_data = dec_data
        
        qadb = Read.mode_bck_comp(str_data)
        
    else:
        # Standard:
        #   (1) Decrypt the data
        #   (2) Pass it on to load_file_sections
        #   (3) Decrypt body section again (same key)
        #   (4) Load as JSON
        #   (5) Pass it on (check meta information, or the lack thereof for ALPHA_ONE)
        
        _mn = _Crypt.decrypt(raw_data, enck, CFA())
        _hash, _dd1 = load_file_sections(FileType.QA_FILE, _mn)  # type: ignore
        _dd2 = _Crypt.decrypt(_dd1, enck, CFA())
        
        assert isinstance(_dd2, (str, bytes))
        if isinstance(_dd2, bytes):
            _sd = _dd2.decode()
            
        else:
            _sd = _dd2
            
        jd: Dict[str, Any] = json.loads(_sd)
        
        if C_META in jd:
            format = ReadMeta(jd[C_META])
            qadb = _qa_file_versions[format.value][1](jd)  # type: ignore
        
        else:
            # Assume ALPHA_ONE 
            qadb = Read.alpha_one(jd)
            
    return qadb, ProduceAlphaOneDict(qadb)


LATEST_GENERATE_FUNCTION = Generate.latest
