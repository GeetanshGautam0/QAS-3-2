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
    Data_VerificationInfo:      List[str]  # Meta, Configuration, Questions
    

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
    

class Read:
    @staticmethod
    def mode_bck_comp(raw_data: str) -> QuestionAnswerDB:
        global _qa_file_versions
        
        E, Q, C = 'SC_END', 'SC_QAI', 'SC_CON'
        
        assert isinstance(raw_data, str),                           '0x00000000'  # Input: TypeError
        assert len(raw_data),                                       '0x00000000'  # Input: ValueError
        assert raw_data.count('\n'),                                '0x00000000'  # Input: ValueError
        
        raw_data = raw_data.strip()
        
        meta_line = raw_data.split('\n')[0]
        raw_data = raw_data.replace(meta_line, '')
        
        assert BACK_COMP.META_APP_VERSION['KEY'] not in raw_data,   '0x00000010'
        assert BACK_COMP.META_APP_VERSION['KEY'] in meta_line,      '0x00000011'
        assert BACK_COMP.META_APP_VERSION['SEP'] in meta_line,      '0x00000012'
        assert BACK_COMP.META_APP_VERSION['VAL'] in meta_line,      '0x00000013'
        
        assert meta_line.index(BACK_COMP.META_APP_VERSION['KEY']) \
            == 0,                                                   '0x00000020'
        
        meta_line = meta_line.replace(BACK_COMP.META_APP_VERSION['KEY'], 'mode', 1)
        
        meta_split = list(map(
            lambda x: x.strip(), 
            meta_line.split(BACK_COMP.META_APP_VERSION['SEP'])
        ))
                
        assert len(meta_split) == 2,                                '0x00000031'
        assert meta_split[0] == 'mode',                             '0x00000032'
        assert meta_split[1] == BACK_COMP.META_APP_VERSION['VAL'],  '0x00000033'
        
        section_codes = []
        section_codes.extend([E for _ in range(raw_data.count(BACK_COMP.CODE_SECTION_END))])
        section_codes.extend([Q for _ in range(raw_data.count(BACK_COMP.CODE_QAS_SECTION_START))])
        section_codes.extend([C for _ in range(raw_data.count(BACK_COMP.CODE_CONFIG_SECTION_START))])
        
        #                                                              ----||xx
        assert len(section_codes) % 2 == 0,                         '0x00000100'  # SC Error: Invalid/corrupted/missing
        assert section_codes.count(Q) == 1,                         '0x00000111'  # SC Error: I
        assert section_codes.count(C) == 1,                         '0x00000112'  # SC Error: I
        assert (section_codes.count(Q) + section_codes.count(C)) \
            == section_codes.count(E),                              '0x00000120'  # SC Error: I/C/M
        
        CS = raw_data.index(BACK_COMP.CODE_CONFIG_SECTION_START)
        QS = raw_data.index(BACK_COMP.CODE_QAS_SECTION_START)        

        assert CS < QS,                                             '0x00000130'  # SC Error: I/C
        
        CE = raw_data.index(BACK_COMP.CODE_SECTION_END)
        
        assert CS < CE < QS,                                        '0x00000131'  # SC Error: I/C
        
        CONFIG_SECT = raw_data[CS:CE + len(BACK_COMP.CODE_SECTION_END)]                               
        raw_data = raw_data.replace(CONFIG_SECT, '')
        assert len(CONFIG_SECT),                                    '0x00000132'  # SC Error: M
        assert BACK_COMP.CODE_SECTION_END in raw_data,              '0x00000133'  # SC Error: I/C
        
        QS = raw_data.index(BACK_COMP.CODE_QAS_SECTION_START)       # Index values change when data is removed therefore a new 
                                                                    # start point is required.    
        QE = raw_data.index(BACK_COMP.CODE_SECTION_END)
        assert QS < QE,                                             '0x00000140'  # SC Error: I/C
        
        QUESTION_SECTION = raw_data[QS:QE + len(BACK_COMP.CODE_SECTION_END)]
        assert len(QUESTION_SECTION),                               '0x00000141'  # SC Error: M
        raw_data = raw_data.replace(QUESTION_SECTION, '').strip()
        assert not len(raw_data),                                   '0x00000142'  # SC Error: I/C
        
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
            
            assert not (bool(len(k)) ^ bool(len(v))),               '0x00000210'
            if not len(k) and not len(v): continue
            configuration[k] = v
            
        for i, (key, (tp, cd, vals)) in enumerate(BACK_COMP.CONTENT_CONFIG.items()):
            f = hex(i)[2:]
            
            assert not cd or key in configuration,                 f'0x{f}000022A'
            if any not in vals:
                assert not cd or configuration[key] in vals,       f'0x{f}000022B'
            
            configuration[key] = {
                'true': True,
                'false': False
            }.get(configuration[key], configuration[key])
            
            try:
                configuration[key] = tp(configuration[key])
            except Exception as _:
                assert not cd,                                     f'0x{f}000022C'
        
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
            
            n_zeros = 6 - len(hex(i))
            code_base = hex(i) + ('0' * n_zeros)
            
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
                
                if BACK_COMP.CONTENT_QAS_LVL3CODE_MCQ_OPTION not in q:
                    sys.stderr.write(f'<Auto-WeakHandling> {code_base}A31B\n')
                    continue
                
                for j, option in enumerate(options):
                    option = option.strip()
                    assert option.index(BACK_COMP.CONTENT_QAS_LVL3CODE_MCQ_OPTION) == 0, f'{code_base}0400'
                    option = option.removeprefix(BACK_COMP.CONTENT_QAS_LVL3CODE_MCQ_OPTION).strip()
                    
                    assert len(option) > 3,                         f'{code_base}0410'
                    assert option.startswith('['),                  f'{code_base}0411'
                    assert ']' in option,                           f'{code_base}0412'
                    
                    handle_start = 1
                    handle_end = option.index(']')
                    
                    handle = option[handle_start:handle_end].strip()
                    assert len(handle),                             f'{code_base}0413'
                    assert '[' not in handle and ']' not in handle, f'{code_base}0414'
                    
                    options_map[handle] = {
                        'id': code_base,
                        'index': j,
                        'label': mc_label_gen(j),
                        'correct': (a == handle)
                    }
                    
                assert a in options_map,                            f'0x00000501'
                assert len(options_map) > 1,                        f'0x00000502'         
                
                s = ['0' for _ in range(sum(map(lambda x: cast(DataEntry, x).size, Data0.entries)))]
                assert len(Data0.entries) == 3, 'INTERNAL_ERROR: update database management'
                
                s[Data0.AutoMark.index] = '1'
                s[Data0.Fuzzy.index] = '1'
                
                questions[code_base] = Question(''.join(s) + '0', q, a, 'mc')               
                
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
            
        return QuestionAnswerDB(
            'qa2', 'qa2', 2, 'qas-version-2-unknown-status', False,
            NULL_STR, NULL_INT, NULL_STR, ReadMode.BackComp.value, 
            configuration_inst, list(questions.values()), False, VerificationStatus.UNAVAILABLE,
            [0] 
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
        ('BCOMP_MODE', ),
    QA_FRMT.ALPHA_ONE.value:
        ('ALPHA_ONE'),
    QA_FRMT.ALPHA_TWO.value:
        ('ALPHA_TWO'),
}

