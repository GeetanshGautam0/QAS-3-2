import json, sys, datetime, hashlib
from dataclasses import dataclass, field
from qa_functions.qa_std import gen_short_uid
from typing import Dict, Optional, Tuple, Any, cast, List
from enum import Enum


# the following must trail the data in all qzdb
C_TRAILING_ID                   = '%qaQuiz'


# constants (DO NOT CHANGE)
C_META                          = 'meta' 
C_CONTENT                       = 'content'
C_VALIDITY                      = 'validity'
        
class QZDB_R1_DB:       
    rt                          = 'DB'       
    META_FLAGS                  = 'FLAGS'
    META_PSWQ                   = 'q_psw'
    META_PSWA                   = 'psw'
    META_NAME                   = 'name'
    

class QZDB_R2_DB:
    META_FLAGS                  = 'db.flags'
    META_PSW_Q                  = 'db.psw.QA'
    META_PSW_A                  = 'db.psw.AT'
    META_NAME                   = 'db.name'
    
    META_FRMT                   = 'qzdb.R2.format'  # This actually applies to ALL databases as of this rendition
    META_FVER                   = 'qzdb.R2.version'
    META_APP_BUILD              = 'qzdb.R2.build'
    META_APP_VERSION            = 'qzdb.R2.version'
    META_GEN_TIME               = 'qzdb.R2.gen_time'
    

C_QZDB_R1_CONTENT_CONFIG        = 'CONFIGURATION'
C_QZDB_R1_CONTENT_QUESTIONS     = 'QUESTIONS'

C_QZDB_R2_CONTENT_CONFIG        = 'db.C'
C_QZDB_R2_CONTENT_QUESTIONS     = 'db.Q'

NULL_STR                        = 'qaQuiz.null'
NULL_INT                        = 0


class QZ_FRMT(Enum):
    # DO NOT let any enum's value equal 0 as that is reserved for _null_int
    QZDB_R1 = 1     # Does not contain any meta information. Added for backwards compatability.
    QZDB_R2 = 2 


@dataclass
class QZDB:
    meta_FLAGS:                 List[str]
    meta_PSWQ:                  List[bool | str]
    meta_PSWA:                  List[bool | str]
    meta_NAME:                  str
    
    content_CONFIG:             Dict[str, str | bool | int]
    content_QUESTIONS:          Dict[str, Dict[str, str | Dict[str, str | int]]] 
    
    # The following are not included in versions prior to QZDB_R2
    meta_APP_BUILD:             str = NULL_STR
    meta_APP_VERSION:           str = NULL_STR
    meta_FVER:                  str = NULL_STR
    meta_FRMT:                  int = NULL_INT
    meta_GEN_TIME:              str = NULL_STR

class Generate:
    @staticmethod
    def ALPHA_TWO(
        # Format and file version implicit (QZDB-R2)
        meta_flags: List[str],
        meta_psw_q: List[bool | str],
        meta_psw_a: List[bool | str],
        meta_db_name: str,
        meta_app_build: str,
        meta_app_version: str,
        content_config: Dict[str, str | bool | int],
        content_questions: Dict[str, Dict[str, str | Dict[str, str | int]]]
    ) -> Tuple[QZDB, str]:
        global _qzdb_file_versions
        global C_META, C_CONTENT, C_QZDB_R2_CONTENT_CONFIG, C_QZDB_R2_CONTENT_QUESTIONS, C_VALIDITY
        
        db_format = QZ_FRMT.QZDB_R2
        db_version = _qzdb_file_versions[db_format.value][0]
        
        db = QZDB(
            meta_flags, meta_psw_q, meta_psw_a, meta_db_name, content_config, content_questions,  # type: ignore
            meta_app_build, meta_app_version, db_version, db_format.value,  # type: ignore
            datetime.datetime.now().strftime('%a, %B %d, %Y - %H:%M:%S')  # type: ignore
        )
        
        output_dict = {
            C_META:
                {
                    QZDB_R2_DB.META_NAME: meta_db_name,
                    QZDB_R2_DB.META_FLAGS: meta_flags,
                    QZDB_R2_DB.META_PSW_A: meta_psw_a,
                    QZDB_R2_DB.META_PSW_Q: meta_psw_q,
                    QZDB_R2_DB.META_APP_BUILD: meta_app_build,
                    QZDB_R2_DB.META_APP_VERSION: meta_app_version,
                    QZDB_R2_DB.META_FRMT: db_format.value,
                    QZDB_R2_DB.META_FVER: db_version,
                    QZDB_R2_DB.META_GEN_TIME: db.meta_GEN_TIME
                },
            C_CONTENT:
                {
                    C_QZDB_R2_CONTENT_CONFIG: content_config,
                    C_QZDB_R2_CONTENT_QUESTIONS: content_questions
                },
            C_VALIDITY:
                {
                    C_QZDB_R2_CONTENT_CONFIG: hashlib.md5(f"{content_config}".encode()).hexdigest(),
                    C_QZDB_R2_CONTENT_QUESTIONS: hashlib.md5(f"{content_questions}".encode()).hexdigest()
                }
        }
        output_dict[C_VALIDITY][C_META] = hashlib.md5(f"{output_dict[C_META]}".encode()).hexdigest()  # type: ignore
        output_str = json.dumps(output_dict, indent=4)
        
        return db, output_str
    
    _latest_ver = ALPHA_TWO


class Read:
    @staticmethod 
    def ALPHA_ONE(data: Dict[str, Any]) -> QZDB:        
        global C_QZDB_R1_CONTENT_QUESTIONS, C_QZDB_R1_CONTENT_CONFIG
        
        return QZDB(
            data[QZDB_R1_DB.rt][QZDB_R1_DB.META_FLAGS],
            data[QZDB_R1_DB.rt][QZDB_R1_DB.META_PSWQ],
            data[QZDB_R1_DB.rt][QZDB_R1_DB.META_PSWA],
            data[QZDB_R1_DB.rt][QZDB_R1_DB.META_NAME],
            data[C_QZDB_R1_CONTENT_CONFIG],
            data[C_QZDB_R1_CONTENT_QUESTIONS]
        )
    
    
    @staticmethod 
    def ALPHA_TWO(data: Dict[str, Any]) -> QZDB:
        global C_META, C_CONTENT, C_QZDB_R2_CONTENT_CONFIG, C_QZDB_R2_CONTENT_QUESTIONS, _qzdb_file_versions
        
        return QZDB(
            data[C_META][QZDB_R2_DB.META_FLAGS],
            data[C_META][QZDB_R2_DB.META_PSW_Q],
            data[C_META][QZDB_R2_DB.META_PSW_A],
            data[C_META][QZDB_R2_DB.META_NAME],
            data[C_CONTENT][C_QZDB_R2_CONTENT_CONFIG],
            data[C_CONTENT][C_QZDB_R2_CONTENT_QUESTIONS],
            data[C_META][QZDB_R2_DB.META_APP_BUILD],
            data[C_META][QZDB_R2_DB.META_APP_VERSION],
            _qzdb_file_versions[QZ_FRMT.QZDB_R2.value][0],  # type: ignore
            QZ_FRMT.QZDB_R2.value,
            data[C_META][QZDB_R2_DB.META_GEN_TIME]
        )


_qzdb_file_versions = {
    QZ_FRMT.QZDB_R1.value: [
        '0.0.1 <A>', 
        ['no_meta', 'flagged_as'], 
        'ALPHA ONE', 
        Read.ALPHA_ONE
    ],
    
    QZ_FRMT.QZDB_R2.value: [
        '0.0.2 <A>',
        [C_META, C_CONTENT, 'flagged_as'],
        'ALPHA TWO',
        Read.ALPHA_TWO
    ]
}


def _read_meta(meta: str | Dict[str, str]) -> Tuple[int, bool]:
    global _qzdb_file_versions
        
    if isinstance(meta, str):
        assert meta == 'no_meta'
        return QZ_FRMT.QZDB_R1.value, True
    
    assert isinstance(meta, dict)
    
    given_format = meta[QZDB_R2_DB.META_FRMT]
    expected_ver = _qzdb_file_versions[given_format][0]  # type: ignore
    given_ver = meta[QZDB_R2_DB.META_FVER]
    
    return given_format, (expected_ver == given_ver)  # type: ignore


def ReadData(data: str) -> QZDB:
    """Automatically chooses the appropriate file version and decodes the provided DATA as per that format.
    
    Currently available formats:
        QZDB-R1   (QZ_FRMT.QZDB_R1)    <int>id: 1           
        QZDB-R2   (QZ_FRMT.QZDB_R2)    <int>id: 2

    Args:
        data (str): data read from file

    Raises:
        AttributeError: If unable to read file

    Returns:
        SCR: SCR instance that contains all data from the file. 
        
    Note:
        SCR data that is not present in the file (usually as a result of outdated files) will be marked as 
        NULL_STR ('qaQuiz.null') or NULL_INT (0) depending on the type of variable in ___. Be sure to appropriately
        handle such instances. 
    """
    
    global _qzdb_file_versions, C_META
    
    data = data.strip()
    assert len(data), 'Invalid data input'
    
    try:
        dP = cast(Dict[str, Any], json.loads(data))
        fmrt, matches = _read_meta(dP.get(C_META, 'no_meta'))
        
        assert matches, 'frmt<lookup>.name != given_name'
        
        fn = _qzdb_file_versions[fmrt][-1]
        return fn(dP)  # type: ignore
    
    except Exception as E:
        sys.stderr.write(f'qa_files.qa_quiz.read_data: {E.__class__.__name__}: {str(E)}\n')
        raise AttributeError ("Provided data cannot be decoded as JSON data OR had invalid data.")
        
        
LATEST_GENERATE_FUNCTION = Generate._latest_ver
