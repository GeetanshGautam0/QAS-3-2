import json, sys 
from dataclasses import dataclass, field
from qa_functions.qa_std import gen_short_uid
from typing import Dict, Optional, Tuple, Any, cast, List
from enum import Enum


# constants (DO NOT CHANGE)
C_META                  = 'meta' 
C_CONTENT               = 'content'

C_META_FRMT             = 'SCR-format'
C_META_FVER             = 'SCR-version'
C_META_FCTIME           = 'SCR-create-time'

C_META_ABUILD           = 'APP-build'
C_META_AVER             = 'APP-version'

C_META_QTIMET           = 'QZ-time-taken'
C_META_QUSER            = 'QZ-user-info'
C_META_QSESSION         = 'QZ-session-ID'
C_META_QATTEMPT         = 'QZ-attempt'
C_META_QTIMES           = 'QZ-time-started'

ELS_1_CONTENT_ERROR_LOG = 'ELS-1-errors'
ELS_1_CONTENT_GEN_LOGS  = 'ELS-1-logs'
ELS_1_CONTENT_D         = 'ELS-1-score'

class ELS_1_SCORE:
    CORRECT             = 'C'
    INCORRECT           = 'I'
    QUESTIONS           = 'q'
    CONFIGURATION       = 'c'
    D0                  = 'd0'

NULL_STR                = 'qaScore.null'
NULL_INT                = 0


class SCR_FRMT(Enum):
    # DO NOT let any enum's value equal 0 as that is reserved for _null_int
    ELS_1 = 1


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
    
    B_AutoMark:             bool
    B_AutoMark_Fuzzy:       bool
    B_AutoMark_FuzzyThs:    float


@dataclass 
class SCR_RES:
    N_correct:              int
    N_incorrect:            int
    D_questions:            Dict[str, Any]
    D_configuration:        Dict[str, Any]
    DATA0:                  List[SCR_QUESTION]


@dataclass
class SCR:    
    APP_build:              str   = NULL_STR
    APP_version:            str   = NULL_STR
    
    SCR_file_create_time:   str   = NULL_STR
    SCR_file_version:       str   = NULL_STR
    SCR_file_format:        int   = NULL_INT
    
    USER_NAME:              str   = NULL_STR
    USER_ID:                str   = NULL_STR
    USER_APP_GEN_ID:        str   = NULL_STR
    SESSION_ID:             str   = NULL_STR
    
    QUIZ_start_time:        str   = NULL_STR
    QUIZ_time_taken:        str   = NULL_STR
    QUIZ_N_attempts:        int   = NULL_INT

    ELOG:          Dict[str, str] = field(default_factory=dict)
    GLOG:          Dict[str, str] = field(default_factory=dict)
    
    SCR_CONTENT:          SCR_RES = field(default_factory=lambda: SCR_RES(
        NULL_INT, 
        NULL_INT, 
        {NULL_STR: NULL_INT}, 
        {NULL_STR: NULL_INT},
        [
            SCR_QUESTION(
                NULL_INT,
                NULL_STR,
                NULL_STR,
                NULL_STR,
                0.00,
                SCR_VERDICT.UNDETERMINED,
                False, False, 100   
            )
        ]
    ))


class Generate:
    @staticmethod
    def ALPHA_ONE(
        # Format and file version implicit (ELS-1)
        meta_SCR_USER_FIRST: str,
        meta_SCR_USER_LAST: str,
        meta_SCR_USER_ID: str,
        meta_SCR_USER_GEN_ID: str,
        meta_SCR_SESSION_ID: str,
        meta_SCR_FILE_GEN_TIME: str,
        meta_APP_VERSION: str,
        meta_APP_BUILD: str,
        meta_QUIZ_START_TIME: str,
        meta_QUIZ_TIME_TAKEN: str,
        meta_QUIZ_N_ATTEMPT: int,
        content_ERROR_LOGS: Dict[str, str],
        content_GENERAL_LOGS: Dict[str, str],
        content_SCORE_INFO: SCR_RES
    ) -> Tuple[SCR, str]:
        """Generates the SCR and string versions of an ELS-1 complicit .qaScore file.

        Args:
            meta_SCR_USER_FIRST (str):                  User first name
            meta_SCR_USER_LAST (str):                   User last name
            meta_SCR_USER_ID (str):                     User alphanumeric identifeiier
            meta_SCR_USER_GEN_ID (str):                 Generated UID for user
            meta_SCR_SESSION_ID (str):                  Generated session ID
            meta_SCR_FILE_GEN_TIME (str):               Time at which this file is to be generated. 
            meta_APP_VERSION (str):                     qa_info.App.version
            meta_APP_BUILD (str):                       qa_info.App.build
            meta_QUIZ_START_TIME (str):                 Time at which the quizzing form was first prompted
            meta_QUIZ_TIME_TAKEN (str):                 How long it took the user to complete the quiz
            meta_QUIZ_N_ATTEMPT (int):                  Number of attempts the user took (NVF-based)
            content_ERROR_LOGS (Dict[str, str]):        {time: error event}
            content_GENERAL_LOGS (Dict[str, str]):      {time: logged event}
            content_SCORE_INFO (SCR_RES):               SCR_RES instance

        Returns:
            Tuple[SCR, str]: The SCR instance used to generate the output_data
        """
        
        global _scr_file_versions
        
        file_format = SCR_FRMT.ELS_1
        file_version: str = _scr_file_versions[file_format.value][0]  # type: ignore
        
        scr = SCR(
            meta_APP_BUILD, meta_APP_VERSION, meta_SCR_FILE_GEN_TIME, file_version, file_format.value,  # type: ignore
            f'{meta_SCR_USER_LAST}, {meta_SCR_USER_FIRST}', meta_SCR_USER_ID,   # type: ignore
            meta_SCR_USER_GEN_ID, meta_SCR_SESSION_ID, meta_QUIZ_START_TIME, meta_QUIZ_TIME_TAKEN,  # type: ignore
            meta_QUIZ_N_ATTEMPT, content_ERROR_LOGS, content_GENERAL_LOGS, content_SCORE_INFO  # type: ignore
        )    
        
        scr_dict = {
            C_META:
                {
                    'SCR.FLAG.AGEN(R)': 'Hola amigo!',
                    C_META_ABUILD: scr.APP_build,
                    C_META_AVER: scr.APP_version,
                    C_META_FCTIME: scr.SCR_file_create_time,
                    C_META_FRMT: file_format.value,
                    C_META_FVER: file_version,
                    C_META_QATTEMPT: scr.QUIZ_N_attempts,
                    C_META_QSESSION: scr.SESSION_ID,
                    C_META_QTIMES: scr.QUIZ_start_time,
                    C_META_QTIMET: scr.QUIZ_time_taken,
                    C_META_QUSER: [scr.USER_NAME, scr.USER_ID, scr.USER_APP_GEN_ID]
                },
            C_CONTENT: 
                {
                    ELS_1_CONTENT_ERROR_LOG: scr.ELOG,
                    ELS_1_CONTENT_GEN_LOGS: scr.GLOG,
                    ELS_1_CONTENT_D: {
                        ELS_1_SCORE.CORRECT: scr.SCR_CONTENT.N_correct,
                        ELS_1_SCORE.INCORRECT: scr.SCR_CONTENT.N_incorrect,
                        ELS_1_SCORE.QUESTIONS: scr.SCR_CONTENT.D_questions,
                        ELS_1_SCORE.CONFIGURATION: scr.SCR_CONTENT.D_configuration,
                        ELS_1_SCORE.D0: {
                            str(S.K_index): [S.S_quid, S.S_question, S.U_response, S.F_percent_match, S.I_verdict.value, S.B_AutoMark, S.B_AutoMark_Fuzzy, S.B_AutoMark_FuzzyThs] for S in content_SCORE_INFO.DATA0
                        }
                    }
                }
        }

        return scr, json.dumps(scr_dict, indent=4)
        
    _latest_ver = ALPHA_ONE


class Read:
    @staticmethod 
    def ALPHA_ONE(data: Dict[str, Any]) -> SCR:
        global ELS_1_CONTENT_D, ELS_1_CONTENT_ERROR_LOG, ELS_1_CONTENT_GEN_LOGS, C_META, C_CONTENT
        global C_META_FRMT, C_META_FVER, C_META_QUSER, C_META_QTIMES, C_META_QTIMET, \
                C_META_QATTEMPT, C_META_FCTIME
        
        output_data = SCR(
            SCR_file_version=data[C_META][C_META_FVER],  # type: ignore
            SCR_file_format=SCR_FRMT.ELS_1.value,  # type: ignore
            USER_NAME=data[C_META][C_META_QUSER][0],  # type: ignore
            USER_ID=data[C_META][C_META_QUSER][1],  # type: ignore
            USER_APP_GEN_ID=data[C_META][C_META_QUSER][2],  # type: ignore
            SESSION_ID=data[C_META][C_META_QSESSION],  # type: ignore
            QUIZ_start_time=data[C_META][C_META_QTIMET],  # type: ignore
            QUIZ_time_taken=data[C_META][C_META_QTIMES],  # type: ignore
            QUIZ_N_attempts=data[C_META][C_META_QATTEMPT],  # type: ignore
            SCR_file_create_time=data[C_META][C_META_FCTIME],  # type: ignore
            APP_build=data[C_META][C_META_ABUILD],  # type: ignore
            APP_version=data[C_META][C_META_AVER]  # type: ignore
        )
        
        content = data[C_CONTENT]
        error_logs, general_logs, score = content[ELS_1_CONTENT_ERROR_LOG], content[ELS_1_CONTENT_GEN_LOGS], content[ELS_1_CONTENT_D]
        assert isinstance(error_logs, dict) and isinstance(general_logs, dict) and isinstance(score, dict)
        
        correct, incorrect, questions, configuration, data0 = (
            score[ELS_1_SCORE.CORRECT], score[ELS_1_SCORE.INCORRECT], score[ELS_1_SCORE.QUESTIONS], score[ELS_1_SCORE.CONFIGURATION],
            score[ELS_1_SCORE.D0]
        )
        
        assert isinstance(correct, int) and isinstance(incorrect, int) and isinstance(questions, dict) and \
            isinstance(configuration, dict) and isinstance(data0, dict)
        
        d0_exp = []
        for index, data in data0.items():
            d0_exp.append(
                SCR_QUESTION(
                    int(index), data[0], data[1], data[2], data[3], data[4], bool(data[5]), bool(data[6]), float(data[7])  # type: ignore
                )
            )
        
        _cont = SCR_RES(correct, incorrect, questions, configuration, d0_exp)
        output_data.SCR_CONTENT = _cont
        output_data.ELOG = error_logs
        output_data.GLOG = general_logs
        
        return output_data


_scr_file_versions = {
    # int             : [version code, format code, version name, mapped method]
    SCR_FRMT.ELS_1.value: [
        '0.0.1 <A>', 
        [ELS_1_CONTENT_ERROR_LOG, ELS_1_CONTENT_GEN_LOGS, ELS_1_CONTENT_D], 
        'ALPHA ONE', 
        Read.ALPHA_ONE
    ]
}


def _read_meta(meta: Dict[str, str]) -> Tuple[int, bool]:
    global _scr_file_versions, C_META_FRMT, C_META_FVER
    
    given_format = meta[C_META_FRMT]  # type: ignore
    expected_ver = _scr_file_versions[given_format][0]  # type: ignore
    given_ver = meta[C_META_FVER]  # type: ignore
    
    return given_format, (expected_ver == given_ver)  # type: ignore


def ReadData(data: str) -> SCR:
    """Automatically chooses the appropriate file version and decodes the provided DATA as per that format.
    
    Currently available formats:
        ELS-1   (SCR_FRMT.ELS_1)    <int>id: 1           (E)rror logs, general (L)ogs, and (S)core data; rendition (1)

    Args:
        data (str): data read from file

    Raises:
        AttributeError: If unable to read file

    Returns:
        SCR: SCR instance that contains all data from the file. 
        
    Note:
        SCR data that is not present in the file (usually as a result of outdated files) will be marked as 
        NULL_STR ('qaScore.null') or NULL_INT (0) depending on the type of variable in SCR. Be sure to appropriately
        handle such instances. 
    """
    global _scr_file_versions, C_META
    
    data = data.strip()
    assert len(data), 'Invalid data input'
    
    try:
        dP = cast(Dict[str, Any], json.loads(data))
        fmrt, matches = _read_meta(dP[C_META])
        
        assert matches, 'frmt<lookup>.name != given_name'
        
        fn = _scr_file_versions[fmrt][-1]
        return fn(dP)  # type: ignore
    
    except Exception as E:
        sys.stderr.write(f'qa_files.qa_score.read_data: {E.__class__.__name__}: {str(E)}\n')
        raise AttributeError ("Provided data cannot be decoded as JSON data OR had invalid data.")
        
        
LATEST_GENERATE_FUNCTION = Generate._latest_ver
