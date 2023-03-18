import sys, traceback as tb
from qa_functions import ANSI, LoggingLevel, ExceptionCodes, File, stderr, LoggingPackage, qa_logger
from typing import Optional, Any, overload, Union, cast, Type, List
from dataclasses import dataclass


LOGGING_FILE_NAME: Optional[str] = None


def _cl_List(input_list: List[Any]) -> list:
    output = []
    for item in input_list:
        if item not in output:
            output.append(item)

    return output


class _B(Exception):
    def __init__(self, exception_code: ExceptionCodes, sub_class: Any, *args: Any, **kwargs: Any) -> None:
        (self.a, self.k) = args, kwargs
        self.ec, self.sc = exception_code, sub_class

        self.en = self.ec.name.replace('_', ' ').title().replace(' ', '')

    @property
    def string(self) -> str:
        return cast(str, self.sc.e_str() + f'\nQuzzingApp.{self.ec.name.upper()}')

    @property
    def formatted_string(self) -> str:
        return cast(str,
                    (self.sc.f_str() if 'f_str' in dir(self.sc) else self.string) + \
                    f'\n{ANSI.FG_BRIGHT_MAGENTA}{ANSI.FG_BLACK}{ANSI.BOLD}QuizzingApp.{self.ec.name.upper()}{ANSI.RESET}'
                )

    @property
    def hex_code(self) -> str:
        global _EXC_MAP, _VAR_MAP

        exception_hex_c = hex(_cl_List(list(_EXC_MAP.values())).index(self.__class__))
        exception_hex_v = hex(_VAR_MAP.get(self.sc.EObj.exception_code, 0) + self.sc.EOff)
        return exception_hex_c + exception_hex_v.split('x')[-1]

    def __repr__(self) -> str:
        return f'Exceptions.{self.sc.__class__.__name__}(%s, EOff={self.sc.EOff}, ExpObj={self.EObj})' % ','.join([str(d) for d in self.sc._a])  # type: ignore

    def __str__(self) -> str:
        return f'Minf_18m_B:ms0: DUMP << {self.string} >>'


class Exceptions:
    m0 = []  # type: ignore
    m1 = {}  # type: ignore
    m2 = {}  # type: ignore

    @staticmethod
    def _E_pKWARGS(cls, **kwargs) -> ExceptionCodes:
        global _EXC_MAP

        ExpObj = kwargs.get('ExpObj', ExceptionObject())
        ExpMode = ExpObj.exception_code if _EXC_MAP[ExpObj.exception_code] == Exceptions.BASE_EXCEPTION else Exceptions.m1[cls.__class__]
        ExpObj.exception_code = ExpMode
        cls.EObj = ExpObj
        cls.EOff = kwargs.get('ExpHexOffset', 0)

        return ExpMode

    class ATTRIBUTE_ERROR(_B):
        @overload
        def __init__(self, error_str: str, *_b_args: Any, **_b_kwargs: Any) -> None: ...
        @overload
        def __init__(self, error_str: str, error_type: str, *_b_args: Any, **_b_kwargs: Any) -> None: ...
        @overload
        def __init__(self, error_str: str, error_type: str, attribute_name: str, *_b_args: Any, **_b_kwargs: Any) -> None: ...
        @overload
        def __init__(self, error_str: str, error_type: str, attribute_name: str, additional_data: str, *_b_args: Any, **_b_kwargs: Any) -> None: ...

        def __init__(self, error_str: str, error_type: Optional[str] = None, attribute_name: Optional[str] = None, additional_data: Optional[str] = '', *_b_args: Any, **_b_kwargs: Any) -> None:
            self.EOff: int = 0
            self.EObj: Optional[ExceptionObject] = None
            ExpMode = Exceptions._E_pKWARGS(self, **_b_kwargs)

            super(Exceptions.ATTRIBUTE_ERROR, self).__init__(ExpMode, self, *_b_args, **_b_kwargs)
            self.an, self.type, self.es, self.ad = attribute_name, error_type, error_str, additional_data
            self._a = [self.es, self.type, self.an, self.ad]

        def e_str(self) -> str:
            return fr'QMEH Attribute Error%s: %s{self.es} {self.ad}'.strip() % (
                f' <{self.type}>' if isinstance(self.type, str) else '',
                f'Attribute "{self.an}": ' if isinstance(self.an, str) else ''
            )

        def f_str(self) -> str:
            return fr'{ANSI.BOLD}QMEH {ANSI.FG_BRIGHT_RED}Attribute Error{ANSI.RESET} [{ANSI.UNDERLINE}{self.hex_code}{ANSI.RESET}] {ANSI.FG_BRIGHT_YELLOW}%s{ANSI.RESET}: {ANSI.UNDERLINE}%s{self.es}{ANSI.RESET} {self.ad}' % (
                f' <{self.type}>' if isinstance(self.type, str) else '',
                f'Attribute "{self.an}": ' if isinstance(self.an, str) else ''
            )

    class BASE_EXCEPTION(_B):
        @overload
        def __init__(self, *_b_args, **_b_kwargs): ...
        @overload
        def __init__(self, exception_type: str, *_b_args, **_b_kwargs): ...
        @overload
        def __init__(self, exception_type: str, exception_data: str, *_b_args, **_b_kwargs): ...
        @overload
        def __init__(self, exception_type: str, exception_data: str, additional_data: str, *_b_args, **_b_kwargs): ...

        def __init__(self, exception_type: str = 'unkE', exception_data: str = '', additional_data: str = '', *_b_args, **_b_kwargs):
            self.EOff: int = 0
            self.EObj: Optional[ExceptionObject] = None
            ExpMode = Exceptions._E_pKWARGS(self, **_b_kwargs)

            super(Exceptions.BASE_EXCEPTION, self).__init__(ExpMode, self, *_b_args, **_b_kwargs)
            self.type, self.data, self.ad = exception_type, exception_data, additional_data
            self._a = [self.type, self.data, exception_data, additional_data]

        def e_str(self) -> str:
            return (fr'QMEH Exception {self.hex_code} <class BE%s>%s %s' % (
                f', {self.type}' if isinstance(self.type, str) else '',
                f': {self.data}' if isinstance(self.data, str) else '',
                self.ad if isinstance(self.data, str) else ''
            )).strip()

        def f_str(self) -> str:
            return (fr'{ANSI.BOLD}QMEH {ANSI.FG_BRIGHT_RED}Exception{ANSI.RESET} [{ANSI.UNDERLINE}{self.hex_code}{ANSI.RESET}] {ANSI.FG_BRIGHT_YELLOW}<class BE%s>{ANSI.RESET}%s %s' % (
                f', {self.type}' if isinstance(self.type, str) else '',
                f': {ANSI.UNDERLINE}{self.data}{ANSI.RESET}' if isinstance(self.data, str) else '',
                self.ad if isinstance(self.data, str) else ''
            )).strip()

    class CONFIG_ERROR(_B):
        @overload
        def __init__(self, *_b_args, **_b_kwargs): ...
        @overload
        def __init__(self, key: str, *_b_args, **_b_kwargs): ...
        @overload
        def __init__(self, key: str, value: str, *_b_args, **_b_kwargs): ...
        @overload
        def __init__(self, key: str, value: str, exception_type: str, *_b_args, **_b_kwargs): ...
        @overload
        def __init__(self, key: str, value: str, exception_type: str, additional_data: str, *_b_args, **_b_kwargs): ...

        def __init__(self, key: str = '<unknown>', value: str = '<unknown>', exception_type: str = '', additional_data: str = '', *_b_args, **_b_kwargs):
            self.EOff: int = 0
            self.EObj: Optional[ExceptionObject] = None
            ExpMode = Exceptions._E_pKWARGS(self, **_b_kwargs)

            super(Exceptions.CONFIG_ERROR, self).__init__(ExpMode, self, *_b_args, **_b_kwargs)
            self.k, self.v, self.type, self.ad = key, value, exception_type, additional_data
            self._a = [key, value, exception_type, additional_data]

        def e_str(self) -> str:
            return fr'QMEH Configuration Error <{self.type}>: Value ({self.k}, {self.v}) {self.ad}'.strip()

        def f_str(self) -> str:
            return fr'{ANSI.BOLD}QMEH {ANSI.FG_BRIGHT_RED}Configuration Error {ANSI.FG_BRIGHT_YELLOW}<{self.type}>{ANSI.RESET}: {ANSI.UNDERLINE}Value ({self.k}, {self.v}){ANSI.RESET} {self.ad}'.strip()

    class FILE_RELATED_ERROR(_B):
        @overload
        def __init__(self, error_str: str): ...
        @overload
        def __init__(self, error_str: str, file: File): ...
        @overload
        def __init__(self, error_str: str, file: str): ...
        @overload
        def __init__(self, error_str: str, file: File, additional_data: str): ...
        @overload
        def __init__(self, error_str: str, file: str, additional_data: str): ...

        def __init__(self, error_str: str, file: Optional[Union[str, File]] = None, additional_data: str = '', *_b_args, **_b_kwargs):
            self.EOff: int = 0
            self.EObj: Optional[ExceptionObject] = None

            ExpMode = Exceptions._E_pKWARGS(self, **_b_kwargs)

            if isinstance(file, File):
                file = file.file_path

            elif not isinstance(file, str) and file is not None:
                # If an ExceptionObject object was supplied to the parent class (via _b_kwargs), use it to get some 'default' values.
                # Invoke a new exception (type aTE)
                InvokeException(
                    ExceptionObject(
                        ExceptionCodes.ARGUMENT_TYPE_ERROR,  # Change exception type to aTE (aTE errors redirected to _BASE_EXCEPTION; use _BASE_EXCEPTION syntax)
                        fatal=self.EObj.fatal,  # Attributes from original exception
                        Raise=False,  # Want to make sure that the _FILE_NOT_FOUND_ERROR is dealt with before an exception is raised
                    ),
                    'arg_TypeError (class aTE)', f'FILE_RELATED_ERROR expected attribute "file" to be of type QA.std.File or str; got {type(file)}'
                )

            super(Exceptions.FILE_RELATED_ERROR, self).__init__(ExpMode, self, *_b_args, **_b_kwargs)
            self.fp, self.ad, self.es = file, additional_data, error_str
            self._a = [error_str, file, additional_data]

        def e_str(self) -> str:
            return (fr'QMEH File-Related Error [{self.hex_code}]:%s {self.ad}' % (fr' <file:"{self.fp}">' if isinstance(self.fp, str) else '')).strip()

        def f_str(self) -> str:
            return (
                f'{ANSI.BOLD}QMEH {ANSI.FG_BRIGHT_RED}File-Related Error{ANSI.RESET} [{ANSI.UNDERLINE}{self.hex_code}{ANSI.RESET}]:{ANSI.UNDERLINE}%s{ANSI.RESET} {self.ad}' % (fr' {self.fp}' if isinstance(self.fp, str) else '')
            ).rstrip()

    class ARITHMETIC_ERROR(_B):
        @overload
        def __init__(self, *_b_args, **_b_kwargs): ...
        @overload
        def __init__(self, error_type: str, *_b_args, **_b_kwargs): ...
        @overload
        def __init__(self, error_type: str, error_str: str, *_b_args, **_b_kwargs): ...
        @overload
        def __init__(self, error_type: str, error_str: str, additional_data: str, *_b_args, **_b_kwargs): ...

        def __init__(self, error_type: Optional[str] = None, error_str: Optional[str] = None, additional_data: Optional[str] = None, *_b_args, **_b_kwargs):
            self.EOff: int = 0
            self.EObj: Optional[ExceptionObject] = None
            ExpMode = Exceptions._E_pKWARGS(self, **_b_kwargs)
            super(self.__class__, self).__init__(ExpMode, self, *_b_args, **_b_kwargs)

            self._a = [error_type, error_str, additional_data]
            self.et, self.es, self.ad = error_type, error_str, additional_data

        def e_str(self) -> str:
            return fr'QMEH Arithmetic Error [{self.hex_code}] %s%s%s' % (
                f' <{self.et}>' if self.et is not None else '',
                f': {self.es}' if self.es is not None else '',
                f' {self.ad}' if self.ad is not None else '',
            )

        def f_str(self) -> str:
            return fr'{ANSI.BOLD}QMEH {ANSI.FG_BRIGHT_RED}Arithmetic Error{ANSI.RESET} [{ANSI.UNDERLINE}{self.hex_code}{ANSI.RESET}] %s%s%s' % (
                f' <{ANSI.FG_BRIGHT_YELLOW}{self.et}{ANSI.RESET}>' if self.et is not None else '',
                f': {ANSI.UNDERLINE}{self.es}{ANSI.RESET}' if self.es is not None else '',
                f' {self.ad}' if self.ad is not None else '',
            )


@dataclass
class ExceptionObject:
    exception_code: ExceptionCodes = ExceptionCodes.BASE_EXCEPTION
    Raise: bool = False
    fatal: bool = False


_EXC_MAP = {
    ExceptionCodes.CONFIG_ERROR: Exceptions.CONFIG_ERROR,
    ExceptionCodes.FILE_RELATED_ERROR: Exceptions.FILE_RELATED_ERROR,
    ExceptionCodes.ATTRIBUTE_ERROR: Exceptions.ATTRIBUTE_ERROR,
    ExceptionCodes.BASE_EXCEPTION: Exceptions.BASE_EXCEPTION,
    ExceptionCodes.ARITHMETIC_ERROR: Exceptions.ARITHMETIC_ERROR,

    # Non-specific error classes MUST follow the specific ones (otherwise the error code generation will be thrown off).
    ExceptionCodes.ARGUMENT_TYPE_ERROR: Exceptions.ATTRIBUTE_ERROR,
    ExceptionCodes.INTERNAL_ERROR: Exceptions.BASE_EXCEPTION,
    ExceptionCodes.ZERO_DIVISION_ERROR: Exceptions.ARITHMETIC_ERROR,
    ExceptionCodes.FILE_NOT_FOUND_ERROR: Exceptions.FILE_RELATED_ERROR,
    ExceptionCodes.VALUE_ERROR: Exceptions.ATTRIBUTE_ERROR,
}

_VAR_MAP = {
    # All base-exception "codes"
    # Base-exception itself does not need to be here as it will automatically default to 0
    # (therefore, variant indexes must start 1)
    # (different error classes can have overlapping __VAR_MAP values)
    ExceptionCodes.INTERNAL_ERROR: 1,
    ExceptionCodes.ARGUMENT_TYPE_ERROR: 2,

    # Arithmetic error types
    ExceptionCodes.ZERO_DIVISION_ERROR: 10,

    # File-related error types
    ExceptionCodes.FILE_NOT_FOUND_ERROR: 4,

    # Attr Errors
    ExceptionCodes.VALUE_ERROR: 1
}

Exceptions.m0 = _cl_List(list(_EXC_MAP.keys()))

for _k in Exceptions.m0:
    Exceptions.m1[_EXC_MAP[_k]] = _k


def SetExceptionMap(exception_code: ExceptionCodes, exception_class: Any) -> None:
    """
    Exception Handler: Change Exception Mapping

    :param exception_code: Exception code (type: ExceptionCodes)
    :param exception_class: Exception class (see Exception Class Format)

    **Exception Class Format** - The exception class must be of the following format:


    class YOUR_CLASS(exception_handler._B):

        ::: REQUIRED METHODS (2) :::

        def __init__(self, your_arguments, *_b_args, **_b_kwargs):
            super(YOUR_CLASS, self).__init__(EXCEPTION_CODE <ExceptionCodes>, self, *_b_args, **_b_kwargs)

        def e_str(self) -> str:
            return 'a human-readable error string'

        ::: OPTIONAL FUNCTIONALITY :::

        def f_str(self) -> str:
            return 'A formatted error string (colors, bold, underline, etc.).'

        ::: OTHER METHODS (for your usage) :::

     Note:  The hex error code can be computed by simply using the property "self.hex_code"
            This property is part of the parent class and does NOT need to be implemented by you.

    :return: None
    """

    global _EXC_MAP
    _EXC_MAP[exception_code] = exception_class


def SetupException(exception: ExceptionObject, *exception_arguments, offset=0, **kwargs) -> Union[
    Exceptions.CONFIG_ERROR, Exceptions.ATTRIBUTE_ERROR, Exceptions.FILE_RELATED_ERROR, Exceptions.BASE_EXCEPTION, Exceptions.ATTRIBUTE_ERROR
]:
    global _EXC_MAP
    try:
        assert not bool([name in _EXC_MAP for name in ExceptionCodes.__members__.values()].count(False)), fr'Insufficient exception mapping'

        exception_class = _EXC_MAP.get(exception.exception_code, Exceptions.BASE_EXCEPTION)
        ei = lambda *_, **__: exception_class(*exception_arguments, **kwargs, ExpObj=exception, ExpHexOffset=offset)

        return cast(Union[Exceptions.CONFIG_ERROR, Exceptions.ATTRIBUTE_ERROR, Exceptions.FILE_RELATED_ERROR, Exceptions.BASE_EXCEPTION, Exceptions.ATTRIBUTE_ERROR], ei)

    except Exception as E:
        exception.exception_code = ExceptionCodes.INTERNAL_ERROR
        SetExceptionMap(ExceptionCodes.INTERNAL_ERROR, Exceptions.BASE_EXCEPTION)
        SetExceptionMap(ExceptionCodes.BASE_EXCEPTION, Exceptions.BASE_EXCEPTION)

        stderr(ANSI.FG_BRIGHT_YELLOW, exception, 'class iE', f'exception_handler::InvokeException raised an {E.__class__.__name__}: {str(E)}', ANSI.RESET)
        stderr(tb.format_exc())

        # Re-invoke exception as a base exception
        exception.exception_code = ExceptionCodes.BASE_EXCEPTION
        return SetupException(exception, *exception_arguments, offset, **kwargs)


def InvokeException(exception: ExceptionObject, *exception_arguments, offset=0, **kwargs) -> None:
    global _EXC_MAP

    try:
        assert not bool([name in _EXC_MAP for name in ExceptionCodes.__members__.values()].count(False)), fr'Insufficient exception mapping'

        exception_class = _EXC_MAP.get(exception.exception_code, Exceptions.BASE_EXCEPTION)
        ei = exception_class(*exception_arguments, **kwargs, ExpObj=exception, ExpHexOffset=offset)

        qa_logger.DEBUGGING_ENABLED = True
        qa_logger.normal_logger([LoggingPackage(LoggingLevel.ERROR, ei.formatted_string, LOGGING_FILE_NAME, 'QA_MASTER_ERROR_HANDLER')])

    except Exception as E:
        exception.exception_code = ExceptionCodes.INTERNAL_ERROR
        SetExceptionMap(ExceptionCodes.INTERNAL_ERROR, Exceptions.BASE_EXCEPTION)
        SetExceptionMap(ExceptionCodes.BASE_EXCEPTION, Exceptions.BASE_EXCEPTION)

        stderr(ANSI.FG_BRIGHT_YELLOW, exception, 'class iE', f'exception_handler::InvokeException raised an {E.__class__.__name__}: {str(E)}', ANSI.RESET)
        stderr(tb.format_exc())

        # Re-invoke exception as a base exception
        exception.exception_code = ExceptionCodes.BASE_EXCEPTION


_O_exceptions = (KeyboardInterrupt, SystemExit)
_O_map = {
    ValueError: (+1100, ExceptionCodes.VALUE_ERROR, '@aOE_dS', '@aCLS_nS', None, (), {'additional_data': f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback'}),
    AttributeError: (+1010, ExceptionCodes.ATTRIBUTE_ERROR, '@aOE_dS', '@aCLS_nS', None, (), {'additional_data': f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback'}),
    TypeError: (+1001, ExceptionCodes.ARGUMENT_TYPE_ERROR, '@aOE_dS', '@aCLS_nS', None, (), {'additional_data': f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback'}),
    NameError: (+1011, ExceptionCodes.ATTRIBUTE_ERROR, '@aOE_dS', '@aCLS_nS', None, (), {'additional_data': f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback'}),
    EOFError: (+1000, ExceptionCodes.FILE_RELATED_ERROR, '<@aCLS_nS>: @aOE_dS', (), {'additional_data': f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback'}),
    NotADirectoryError: (+1010, ExceptionCodes.FILE_RELATED_ERROR, '<@aCLS_nS>: @aOE_dS', (), {'additional_data': f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback'}),
    IsADirectoryError: (+1020, ExceptionCodes.FILE_RELATED_ERROR, '<@aCLS_nS>: @aOE_dS', (), {'additional_data': f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback'}),
    FileNotFoundError: (+1050, ExceptionCodes.FILE_NOT_FOUND_ERROR, '<@aCLS_nS>: @aOE_dS', (), {'additional_data': f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback'}),
    FileExistsError: (+1500, ExceptionCodes.FILE_RELATED_ERROR, '<@aCLS_nS>: @aOE_dS', (), {'additional_data': f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback'}),
    ArithmeticError: (+1500, ExceptionCodes.ARITHMETIC_ERROR, '@aCLS_nS', '@aOE_dS', f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback', (), {}),
    ZeroDivisionError: (+1203, ExceptionCodes.ZERO_DIVISION_ERROR, '@aCLS_nS', '@aOE_dS', f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback', (), {}),
    Exception: (+1010, ExceptionCodes.BASE_EXCEPTION, '@aCLS_nS', '@aOE_dS', f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback', (), {}),
    FloatingPointError: (+1001, ExceptionCodes.ARITHMETIC_ERROR, '@aCLS_nS', '@aOE_dS', f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback', (), {}),
    BaseException: (+1020, ExceptionCodes.BASE_EXCEPTION, '@aCLS_nS', '@aOE_dS', f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback', (), {}),
    AssertionError: (+1011, ExceptionCodes.BASE_EXCEPTION, '@aCLS_nS', '@aOE_dS', f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback', (), {}),
    MemoryError: (+1022, ExceptionCodes.INTERNAL_ERROR, 'INTERNAL_ERROR: @aCLS_nS', '@aOE_dS', f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback', (), {}),
    RuntimeError: (+1023, ExceptionCodes.INTERNAL_ERROR, 'INTERNAL_ERROR: @aCLS_nS', '@aOE_dS', f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback', (), {}),
    RuntimeWarning: (+1024, ExceptionCodes.INTERNAL_ERROR, 'INTERNAL_ERROR: @aCLS_nS', '@aOE_dS', f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback', (), {}),
    SyntaxWarning: (+1025, ExceptionCodes.INTERNAL_ERROR, 'INTERNAL_ERROR: @aCLS_nS', '@aOE_dS', f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback', (), {}),
    SyntaxError: (+1026, ExceptionCodes.INTERNAL_ERROR, 'INTERNAL_ERROR: @aCLS_nS', '@aOE_dS', f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback', (), {}),
    SystemError: (+1014, ExceptionCodes.INTERNAL_ERROR, 'INTERNAL_ERROR: @aCLS_nS', '@aOE_dS', f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback', (), {}),
    PermissionError: (+1011, ExceptionCodes.INTERNAL_ERROR, 'INTERNAL_ERROR: @aCLS_nS', '@aOE_dS', f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback', (), {}),
    RecursionError: (+1013, ExceptionCodes.INTERNAL_ERROR, 'INTERNAL_ERROR: @aCLS_nS', '@aOE_dS', f'\n{ANSI.FG_BRIGHT_YELLOW}Traceback info{ANSI.RESET}: \n@traceback', (), {}),
}

Minf_EH_Md7182_eHookTasks = []
Minf_EH_Md7182_eHookTasks_PRE = []


def _O_exception_hook(exception_type: Type[BaseException], value, traceback, _invoke_exception=True, _re_inst=False):
    global _O_map, Minf_EH_Md7182_eHookTasks

    def _O_eh_run_tasks(tasks, fatal):
        for (condition, task) in tasks:
            try:
                if condition(fatal):
                    task()

            except Exception as E:
                stderr(f'Failed to run task in UTIL_ExceptionHook: {E}')

        return

    _O_eh_run_tasks(Minf_EH_Md7182_eHookTasks_PRE, _invoke_exception)

    if exception_type not in _O_exceptions:
        offset, exception_code, *exception_args, args, kwargs = _O_map.get(exception_type, _O_map[BaseException])
        rMap = {
            '@aCLS_nS': str(exception_type.__name__),
            '@aOE_dS': str(value),
            '@traceback': "\n".join(tb.extract_tb(traceback).format())
        }

        L = []
        A = []
        K = {}

        for ea in exception_args:
            sN = ea
            if isinstance(sN, str):
                for key, rep in rMap.items():
                    sN = sN.replace(key, rep, 1)
            L.append(sN)

        for aa in args:
            sN = aa
            if isinstance(sN, str):
                for key, rep in rMap.items():
                    sN = sN.replace(key, rep, 1)
            A.append(sN)

        for ka, va in kwargs.items():  # Keys not modified
            vN = va
            if isinstance(vN, str):
                for key, rep in rMap.items():
                    vN = vN.replace(key, rep, 1)
            K[ka] = vN

        if _invoke_exception:
            InvokeException(ExceptionObject(exception_code, False), *L, *A, **{'offset': offset, **K})
            _O_eh_run_tasks(Minf_EH_Md7182_eHookTasks, True)
            return None

        elif _re_inst:
            _O_eh_run_tasks(Minf_EH_Md7182_eHookTasks, False)
            return SetupException(ExceptionObject(exception_code, False), *L, *A, **{'offset': offset, **K})

        else:
            sys.__excepthook__(exception_type, value, traceback)

    else:
        sys.__excepthook__(exception_type, value, traceback)


def RedirectExceptionHandler() -> None:
    sys.excepthook = sys.__excepthook__ if not (sys.excepthook == sys.__excepthook__) else _O_exception_hook
