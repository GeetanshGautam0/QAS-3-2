import json, sys, hashlib, datetime, re, random
from qa_functions.qa_std import data_at_dict_path, check_hex_contrast, clamp
from typing import Tuple, List, Dict, Any, Union, cast
from .qa_files_ltbl import qa_file_enck
from dataclasses import dataclass
from enum import Enum
from qa_ui.qa_adv_forms.qa_form_q_edit import Data0, Data1, DataEntry, DataType, mc_label_gen


NULL_STR = 'qafile:nullstr'
NULL_INT = 0


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
                    
                questions_cl[code_base] = Question(d0, q, a, d1)
                
            elif d1 == 'tf':
                assert isinstance(a, str),                          f'{code_base}0524'
                a = a.strip()
                
                a = bool(int(a))
                questions_cl[code_base] = Question(d0, q, a, d1)
                
            elif d1 == 'nm':
                assert isinstance(a, str),                          f'{code_base}0524'
                a = a.strip()
                
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
            conf, list(questions_cl.values()),
            False, VerificationStatus.UNAVAILABLE.value,
            [0], qpsw, dpsw
        )
                
        
def ProduceAlphaOneDict(qadb: QuestionAnswerDB) -> Dict[str, Any]:
    pass

    
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
        ('BCOMP_MODE', Read.mode_bck_comp),
    QA_FRMT.ALPHA_ONE.value:
        ('ALPHA_ONE'),
    QA_FRMT.ALPHA_TWO.value:
        ('ALPHA_TWO'),
}

