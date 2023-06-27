import os, sys, hashlib
from .qa_info import App
from typing import *


if __name__ == "__main__":
    sys.exit('cannot use as standalone script')


ROOT = f"{App.appdata_dir}\\.nvf"
DELIMITER = "=="


def create_flag(script: str, name: str) -> None:
    global ROOT, DELIMITER

    if not os.path.isdir(ROOT):
        os.makedirs(ROOT)

    name = name.replace(DELIMITER, '__')

    if not check_flag(script, name):
        with open(f"{ROOT}\\{script}{DELIMITER}{name}.qaEnc", 'w') as flag:
            flag.write(hex(int(hashlib.sha3_512(f'{script}{DELIMITER}{name}.qaEnc'.encode()).hexdigest(), 16)))
            flag.close()


def delete_flag(script: str, name: str) -> None:
    global ROOT, DELIMITER

    name = name.replace(DELIMITER, '__')

    if check_flag(script, name):
        os.remove(f"{ROOT}\\{script}{DELIMITER}{name}.qaEnc")


def check_flag(script: str, name: str) -> bool:
    global ROOT, DELIMITER

    name = name.replace(DELIMITER, '__')

    return os.path.exists(f"{ROOT}\\{script}{DELIMITER}{name}.qaEnc")


def verify_flag(script: str, name: str) -> bool:
    global ROOT, DELIMETER
    
    file = f"{script}{DELIMITER}{name}.qaEnc"
    path = f'{ROOT}\\{file}'
    
    if not os.path.exists(path):
        return False
    
    else:
        with open(path, 'r') as file_vec:
            file_contents = file_vec.read().strip()
            file_vec.close()
            
        return file_contents == hex(int(hashlib.sha3_512(file.encode()).hexdigest(), 16))


def clear_all_app_flags(script: str) -> None:
    global ROOT, DELIMITER

    if os.path.isdir(ROOT):
        for item in os.listdir(ROOT):
            if item.split(DELIMITER)[0].lower().strip() == script.lower().strip():
                os.remove(f"{ROOT}\\{item}")


def clear_all_flags() -> None:
    global ROOT

    if os.path.isdir(ROOT):
        for item in os.listdir(ROOT):
            os.remove(f"{ROOT}\\{item}")


def yield_all_flags(script: str) -> Generator[str, Any, None]:
    global ROOT, DELIMITER

    if os.path.isdir(ROOT):
        for item in os.listdir(ROOT):
            if script == 'any':
                yield item.replace('__', DELIMITER)
                continue

            if item.split(DELIMITER)[0].lower().strip() == script.lower().strip():
                yield item.split(DELIMITER)[1].replace('__', DELIMITER)


def yield_all_flags_as_list(script: str) -> List[str]:
    global ROOT, DELIMITER

    acc: List[str] = []

    if os.path.isdir(ROOT):
        for item in os.listdir(ROOT):
            if script == 'any':
                acc.append(item.replace('__', DELIMITER))

            if item.split(DELIMITER)[0].lower().strip() == script.lower().strip():
                acc.append(item.split(DELIMITER)[1].replace('__', DELIMITER))

    return acc
