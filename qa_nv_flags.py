import os, sys
from qa_info import App


if __name__ == "__main__":
    sys.exit('cannot use as standalone script')


ROOT = f"{App.appdata_dir}\\.nvf"
DELIMITER = "=="


def create_flag(script: str, name: str):
    global ROOT, DELIMITER

    if not os.path.isdir(ROOT):
        os.makedirs(ROOT)

    name = name.replace(DELIMITER, '__')

    if not check_flag(script, name):
        with open(f"{ROOT}\\{script}{DELIMITER}{name}", 'w') as flag:
            flag.close()


def delete_flag(script: str, name: str):
    global ROOT, DELIMITER

    name = name.replace(DELIMITER, '__')

    if check_flag(script, name):
        os.remove(f"{ROOT}\\{script}{DELIMITER}{name}")


def check_flag(script: str, name: str):
    global ROOT, DELIMITER

    name = name.replace(DELIMITER, '__')

    return os.path.exists(f"{ROOT}\\{script}{DELIMITER}{name}")


def clear_all_app_flags(script: str):
    global ROOT, DELIMITER

    if os.path.isdir(ROOT):
        for item in os.listdir(ROOT):
            if item.split(DELIMITER)[0].lower().strip() == script.lower().strip():
                os.remove(f"{ROOT}\\{item}")


def clear_all_flags():
    global ROOT

    if os.path.isdir(ROOT):
        for item in os.listdir(ROOT):
            os.remove(f"{ROOT}\\{item}")


def yield_all_flags(script: str):
    global ROOT, DELIMITER

    if os.path.isdir(ROOT):
        for item in os.listdir(ROOT):
            if isinstance(script, type):
                if script is any:
                    yield item.replace('__', DELIMITER)

                continue

            if item.split(DELIMITER)[0].lower().strip() == script.lower().strip():
                yield item.split(DELIMITER)[1].replace('__', DELIMITER)


def yield_all_flags_as_list(script: str):
    global ROOT, DELIMITER

    acc = []

    if os.path.isdir(ROOT):
        for item in os.listdir(ROOT):
            if isinstance(script, type):
                if script is any:
                    acc.append(item.replace('__', DELIMITER))

                continue

            if item.split(DELIMITER)[0].lower().strip() == script.lower().strip():
                acc.append(item.split(DELIMITER)[1].replace('__', DELIMITER))

    return acc
