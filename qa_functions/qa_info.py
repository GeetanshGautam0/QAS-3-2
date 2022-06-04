import appdirs, json, os, sys, traceback, hashlib
from . import qa_err
from . import qa_enum
from . import qa_custom


class ConfigurationFile:
    name = ".\\.config\\main_config.json"
    completed = False

    if not os.path.exists(name):
        qa_err.raise_error(FileNotFoundError, ["Main configuration file not found"], qa_enum.ErrorLevels.FATAL)
        sys.exit(qa_enum.ExitCodes.GENERAL_ERROR)

    try:
        with open(name, 'r') as file:
            d = file.read()
            file.close()
        json_data = json.loads(d)

    except Exception as E:
        qa_err.raise_error(E.__class__, [str(E)], qa_enum.ErrorLevels.FATAL, traceback.format_exc())
        sys.exit(qa_enum.ExitCodes.GENERAL_ERROR)

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
    build_number = ConfigurationFile.json_data['application']['build_number']

    github_url_base = ConfigurationFile.json_data['application']['root_update_url']
    DEV_MODE = ConfigurationFile.json_data['application']['dev_mode']


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
    ThemeCustomFile = "userDefined.qaTheme"

    # Icons
    icoRoot = ".\\.src\\.icons\\.app_ico"
    pngRoot = ".\\.src\\.icons\\.app_ico\\.png"
    TU_ico = f"{icoRoot}\\themer.ico"
    AT_ico = f"{icoRoot}\\admin_tools.ico"
    QF_ico = f"{icoRoot}\\quizzing_tool.ico"
    RU_ico = f"{icoRoot}\\ftsra.ico"

    TU_png = f"{pngRoot}\\themer.png"
    AT_png = f"{pngRoot}\\admin_tools.png"
    QF_png = f"{pngRoot}\\quizzing_tool.png"
    RU_png = f"{pngRoot}\\ftsra.png"


class Encryption:
    default_key: bytes = b"oyJeLcbVk6_w9tbKJArWCZLSBjS8ZfK9M-cAygf6SRQ="


class OnlineFiles:
    class Addons:
        class Theme:
            all_files = (
                f'{App.github_url_base}/additional_themes/retro_theme.qaTheme',
                f'{App.github_url_base}/additional_themes/theme_addons.qaTheme',
                f'{App.github_url_base}/additional_themes/high_contrast.qaTheme',
            )
