import json, sys, hashlib, datetime, re, random
from qa_functions.qa_std import data_at_dict_path, check_hex_contrast, clamp
from qa_functions.qa_file_handler import _Crypt, ConverterFunctionArgs as CFA
from typing import Tuple, List, Dict, Any, Union, cast
from .qa_files_ltbl import qa_file_enck
from .qa_file_std import load_file_sections, FileType
from dataclasses import dataclass
from enum import Enum
from qa_ui.qa_adv_forms.qa_form_q_edit import Data0, Data1, DataEntry, DataType, mc_label_gen


NULL_STR = 'qafile:nullstr'
NULL_INT = 0


C_META = 'meta'
C_CONTENT = 'body'
C_VERIFICATION = 'verification'
FF_STATIC_KEY = 'QAP.SKS.FileFormat'


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
            }.get(configuration[key], configuration[key])
            
            try:
                configuration[key] = tp(configuration[key])
            except Exception as _:
                assert not cd,                                     f'0xBC{f}000022C'
        
        configuration_inst = Configuration(
            configuration['acqc'],
            configuration['qpoa'][0].lower() == 'p',
            configuration['qsdf'],
            True,
            configuration['dma'],
            configuration['pdpir']
        )    
        
        questions: Dict[str, Question] = {}
        
        for i, ENTRY in enumerate(QUESTION_SECTION.split(BACK_COMP.CONTENT_QAS_CODE_ENTRY_SEP)):    
            
            n_zeros = clamp(0, (6 - len(hex(i))), 9e9)
            code_base = hex(i) + ('0' * n_zeros)
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
                        'label': mc_label_gen(j),
                        'correct': (a == handle),
                        'data': option.replace(f'[{handle}]', '', 1).strip()
                    }
                    
                    if a == handle:
                        correct_options.append(str(j))
                    
                assert a in options_map,                            f'0x00000501'
                assert len(options_map) > 1,                        f'0x00000502'         
                
                s = ['0' for _ in range(sum(map(lambda x: cast(DataEntry, x).size, Data0.entries)))]
                assert len(Data0.entries) == 3, 'INTERNAL_ERROR: update database management'
                
                s[Data0.AutoMark.index] = '1'
                s[Data0.Fuzzy.index] = '1'
                
                questions[code_base] = Question(''.join(s) + '0', q, {
                    "C": "/".join(correct_options).strip('/'),
                    "N": len(options_map),
                    **{
                        str(opt['index']): opt['data'] for opt in options_map.values() 
                    }
                }, 'mc0')               
                
            elif BACK_COMP.CONTENT_QAS_LVL2CODE_TFQ in q:
                q = q.replace(BACK_COMP.CONTENT_QAS_LVL2CODE_TFQ, '', 1).strip()
                
                if not (('t' in a.lower()) ^ ('f' in a.lower())):
                    sys.stderr.write(f'<Auto-WeakHandling> {code_base}A31D\n')
                    continue
                
                s = ['0' for _ in range(sum(map(lambda x: cast(DataEntry, x).size, Data0.entries)))]
                assert len(Data0.entries) == 3, 'INTERNAL_ERROR: update database management'
                
                s[Data0.AutoMark.index] = '1'
                s[Data0.Fuzzy.index] = '1'
                
                questions[code_base] = Question(''.join(s) + '0', q, '1' if ('t' in a) else '0', 'tf')
                
            else:
                if not len(a):
                    sys.stderr.write(f'<Auto-WeakHandling> {code_base}A31E\n')
                    continue
                
                s = ['0' for _ in range(sum(map(lambda x: cast(DataEntry, x).size, Data0.entries)))]
                assert len(Data0.entries) == 3, 'INTERNAL_ERROR: update database management'
                
                s[Data0.AutoMark.index] = '1'
                s[Data0.Fuzzy.index] = '1'
                
                questions[code_base] = Question(''.join(s) + '0', q.strip(), a.strip(), 'nm')
            
            if not len(q) or not len(a): continue
        
        sys.stdout.write('Found questions:\n\t' + '\n\t'.join(questions.keys()) + '\n')
        
        return QuestionAnswerDB(
            'qa2', NULL_STR, 2, NULL_STR, False,
            NULL_STR, NULL_INT, NULL_STR, ReadMode.BackComp.value, 
            f'PORTED_DATABASE {random.randint(1e10, 1e11)}.{random.random()}',
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
            code_base = code_base + "0" * clamp(0, (6 - len(code_base)), 9e9)
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
                    lambda x: cast(DataEntry, x).size,
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
            NULL_STR, False, _qa_file_versions[QA_FRMT.ALPHA_ONE.value],
            QA_FRMT.ALPHA_ONE.value, NULL_STR,
            ReadMode.NewGen.value,
            meta[ALPHA_ONE.L2_META_NAME],
            conf, list(questions_cl.values()),
            False, VerificationStatus.UNAVAILABLE.value,
            [0], qpsw, dpsw
        )
        
    @staticmethod
    def alpha_two(data: Dict[str, Any]) -> QuestionAnswerDB:
        pass


def _get_dict_hash(data: Dict[str, Any], fnc: Any) -> str:
    jd = json.dumps(data)
    return fnc(jd.encode()).hexdigest()


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
                            ('0x' + clamp(0, 12 - len(hex(i)), 9e9) * '0' + hex(i)[2::]):
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

        dc[C_VERIFICATION][ALPHA_TWO.V_P] = _get_dict_hash(dc[ALPHA_TWO.ProtectionConfig], ALPHA_TWO.PROTECTION_HASH_FNC)
        dc[C_VERIFICATION][ALPHA_TWO.V_CCCF] = _get_dict_hash(dc[C_CONTENT][ALPHA_TWO.C_Configuration], ALPHA_TWO.PROTECTION_HASH_FNC)
        dc[C_VERIFICATION][ALPHA_TWO.V_CCQB] = _get_dict_hash(dc[C_CONTENT][ALPHA_TWO.C_QuestionBank], ALPHA_TWO.PROTECTION_HASH_FNC)
        dc[C_VERIFICATION][ALPHA_TWO.V_META] = _get_dict_hash(dc[C_META], ALPHA_TWO.PROTECTION_HASH_FNC)
        
        verification_data = [ALPHA_TWO.VERI_N_IT, *['' for _ in range(ALPHA_TWO.VERI_N_IT)]]
        verification_data[ALPHA_TWO.VERI_PRTC] = dc[C_VERIFICATION][ALPHA_TWO.V_P]
        verification_data[ALPHA_TWO.VERI_CCCF] = dc[C_VERIFICATION][ALPHA_TWO.V_CCCF]
        verification_data[ALPHA_TWO.VERI_CCQB] = dc[C_VERIFICATION][ALPHA_TWO.V_CCQB]
        verification_data[ALPHA_TWO.VERI_META] = dc[C_VERIFICATION][ALPHA_TWO.V_META]
        
        qadb = QuestionAnswerDB(
            App_Version, App_Build, App_IVersion, App_BuildInfo, App_InDevMode,
            _qa_file_versions[QA_FRMT.ALPHA_TWO.value][0], QA_FRMT.ALPHA_TWO.value,
            dc[C_META][ALPHA_TWO.M_FileGenTime], dc[C_META][ALPHA_TWO.M_ReadMode],
            Database_Name, configuration, Questions,
            True, VerificationStatus.PASSED, verification_data,
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
                ('0x' + clamp(0, 12 - len(hex(i)), 9e9) * '0' + hex(i)[2::]): {
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


def ReadRawData(raw_data: bytes) -> Tuple[QuestionAnswerDB, Dict[str, Any]]:
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
        _hash, _dd1 = load_file_sections(FileType.QA_FILE, _mn)
        _dd2 = _Crypt.decrypt(_dd1, enck, CFA())
        
        assert isinstance(_dd2, (str, bytes))
        if isinstance(_dd2, bytes):
            _sd = _dd2.decode()
            
        else:
            _sd = _dd2
            
        jd: Dict[str, Any] = json.loads(_sd)
        
        if C_META in jd:
            format = ReadMeta(jd[C_META])
            qadb = _qa_file_versions[format.value][1](jd)
        
        else:
            # Assume ALPHA_ONE 
            qadb = Read.alpha_one(jd)
            
        