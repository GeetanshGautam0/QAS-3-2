import json, sys 
from dataclasses import dataclass
from qa_functions.qa_std import gen_short_uid
from typing import Dict, Optional, Tuple, Any, cast, List
from enum import Enum


# constants (DO NOT CHANGE)
C_META          = 'meta' 
C_CONTENT       = 'content'
C_META_FRMT     = 'SCR-file-format'
C_META_FVER     = 'SCR-file-version'

C_META_ABUILD   = 'APP-build'
C_META_AVER     = 'APP-version'
C_META_

NULL_STR        = 'qaScore.null'
NULL_INT        = 0


class SCR_FRMT(Enum):
    # DO NOT let any enum's value equal 0 as that is reserved for _null_int
    ELS = 1


class SCR_VERDICT(Enum):
    CORRECT = 1
    INCORRECT= 0
    UNDETERMINED = -1


@dataclass
class SCR_QUESTION:
    K_index:                int
    S_quid:                 str
    S_question:             str
    U_response:             bool | str
    F_percent_match:        float
    I_verdict:              SCR_VERDICT


@dataclass 
class SCR_RES:
    N_correct:              int
    N_incorrect:            int
    D_questions:            dict
    D_configuration:        dict
    DATA0:                  List[SCR_QUESTION]


@dataclass
class SCR:    
    APP_build:              str   = NULL_STR
    APP_version:            str   = NULL_STR
    
    SCR_file_create_time:   str   = NULL_STR
    SCR_file_version:       str
    SCR_file_format:        int
    
    USER_NAME:              str
    USER_ID:                str
    SESSION_ID:             str
    
    QUIZ_start_time:        str   = NULL_STR
    QUIZ_time_taken:        str   = NULL_STR
    QUIZ_N_attempts:        str   = NULL_STR

    SCR_CONTENT:            SCR_RES
    

class Read:
    @staticmethod 
    def ALPHA_ONE(data: Dict[str, Any]) -> SCR:
        pass


_scr_file_versions = {
    # int             : [version code, format code, version name, mapped method]
    SCR_FRMT.ELS.value: ['0.0.1 <A>', '_E/_L/_S', 'ALPHA ONE', Read.ALPHA_ONE]
}


def _read_meta(meta: Dict[str, str]) -> Tuple[int, bool]:
    given_format = 


def read_data(data: str) -> SCR:
    global _scr_file_versions
    
    data = data.strip()
    assert len(data), 'Invalid data input'
    
    try:
        dP = cast(Dict[str, Any], json.loads(data))
        fmrt, matches = _read_meta(dP['meta'])
        
        assert matches, 'frmt<lookup>.name != given_name'
        
        fn = _scr_file_versions[fmrt][-1]
        return fn(dP)
    
    except Exception as E:
        sys.stderr.write(f'qa_files.qa_score.read_data: {E.__class__.__name__}: {str(E)}\n')
        raise AttributeError ("Provided data cannot be decoded as JSON data OR had invalid data.")
        
