import appdirs, json, os, sys, traceback, hashlib
from .qa_err import *


class ConfigurationFile:
    name = ".\\.config\\main_config.json"
    completed = False

    if not os.path.exists(name):
        raise_error(FileNotFoundError, "Main configuration file not found", ErrorLevels.Fatal)
        sys.exit(ExitCodes.GENERAL_ERROR)

    try:
        with open(name, 'r') as file:
            d = file.read()
            file.close()
        json_data = json.loads(d)

    except Exception as E:
        raise_error(E.__class__, str(E), ErrorLevels.FATAL, traceback.format_exc())
        sys.exit(ExitCodes.GENERAL_ERROR)

    completed = True


class App:
    appdata_dir = appdirs.user_data_dir(
        ConfigurationFile.json_data['application']['appdata_app_name'],
        ConfigurationFile.json_data['application']['app_author'],
        str(ConfigurationFile.json_data['application']['version']),
        ConfigurationFile.json_data['application']['appdata_roaming']
    )

    ENCODING = 'utf-8'

    name = ConfigurationFile.json_data['application']['name']
    version = ConfigurationFile.json_data['application']['version']
    build_id = hashlib.md5(ConfigurationFile.json_data['application']['build_id_str'].encode(ENCODING)).hexdigest()
    build_name = ConfigurationFile.json_data['application']['build_title']


class Extensions:
    class Logging:
        extn_str = "qaLog"

    class RegularFile:
        extn_str = "qaFile"

    class QuizFile:
        extn_str = "qaQuiz"

    class ExportFile:
        extn_str = "qaExport"

    class BackupFile:
        extn_str = "qaBackup"


class Files:
    # Logging
    logs_folder = ".logs"
    error_file = f"{App.appdata_dir}\\{logs_folder}\\0 Error Logs\\log.{Extensions.Logging.extn_str}"

    # Backups
    backup_folder = f"{App.appdata_dir}\\.backups"

    # Default Files
    default_src = ".src"
    default_dir = ".defaults"
    default_theme_dir = f".\\{default_src}\\{default_dir}\\.themes"
    default_theme_file = f"{default_theme_dir}\\default.json"
    default_theme_file_code = ".\\.src\\.defaults\\.themes"
    default_theme_hashes = f"{default_theme_dir}\\hashes.json"

    # Theme (AppData)
    ad_theme_folder = ".themes"
    ThemePrefFile = "pref.json"

    # Icons
    icoRoot = ".\\.src\\.icons\\.app_ico"
    TU_ico = f"{icoRoot}\\themer.ico"


class Encryption:
    default_key: bytes = b"oyJeLcbVk6_w9tbKJArWCZLSBjS8ZfK9M-cAygf6SRQ="
