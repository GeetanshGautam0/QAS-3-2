import os, sys, json, subprocess, traceback
from qa_functions import ANSI, File, SaveFunctionArgs, SaveFile
from datetime import datetime
from ctypes import windll
from typing import Optional, cast, Iterable
from qa_functions.qa_svh import compile_svh


def _build_number() -> float:
    return float(datetime.now().strftime('%y%m%j.%H%M%S%f'))


def _disable_dev_mode() -> None:
    with open('.config\\main_config.json', 'r') as mc_file:
        mc_json = json.loads(mc_file.read())
        mc_file.close()

    mc_json['application']['dev_mode'] = False

    # .config\main_config.json
    file = File('.config\\main_config.json')
    if SaveFile.secure(file, json.dumps(mc_json, indent=4), SaveFunctionArgs(False)):
        sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.RESET} Successfully saved new configuration to dev_config (disabled dev_mode)\n")
    else:
        sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.FG_BRIGHT_RED} Failed to save new configuration to dev_config (failed to disable dev_mode)\n")


def _enable_dev_mode() -> None:
    with open('.config\\main_config.json', 'r') as mc_file:
        mc_json = json.loads(mc_file.read())
        mc_file.close()

    mc_json['application']['dev_mode'] = True

    # .config\main_config.json
    file = File('.config\\main_config.json')
    if SaveFile.secure(file, json.dumps(mc_json, indent=4), SaveFunctionArgs(False)):
        sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.RESET} Successfully saved new configuration to dev_config (enabled dev_mode)\n")
    else:
        sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.FG_BRIGHT_RED} Failed to save new configuration to dev_config (failed to enable dev_mode)\n")


def _set_build_number(build_number: float, build_id: str, build_name: str) -> None:
    with open('.config\\main_config.json', 'r') as mc_file:
        mc_json = json.loads(mc_file.read())
        mc_file.close()
        
    mc_json['application']['build_number'] = build_number
    mc_json['application']['build_id_str'] = build_id
    mc_json['application']['build_title']  = build_name

    # .config\main_config.json
    file = File('.config\\main_config.json')
    if SaveFile.secure(file, json.dumps(mc_json, indent=4), SaveFunctionArgs(False)):
        sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.RESET} Successfully saved new configuration to dev_config\n")
    else:
        sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.FG_BRIGHT_RED} Failed to save new configuration to dev_config\n")
    
    # installer\.config\main_config.json
    file = File('installer\\.config\\main_config.json')
    mc_json['application']['dev_mode'] = False
    if SaveFile.secure(file, json.dumps(mc_json, indent=4), SaveFunctionArgs(False)):
        sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.RESET} Successfully saved new configuration to inst_config\n")
    else:
        sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.FG_BRIGHT_RED} Failed to save new configuration to inst_config\n")


def _run_command(com: str, *args: Optional[str], admin: bool = False, silent: bool = False) -> None:
    sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.RESET} Running Command:         {ANSI.FG_BRIGHT_GREEN}{ANSI.REVERSED}{ANSI.BOLD} {' '.join(cast(Iterable[str], [com, *args])).strip()} {ANSI.RESET} (UAC_ELEVATION: {ANSI.FG_BRIGHT_GREEN}{ANSI.REVERSED}{ANSI.BOLD}{admin}{ANSI.RESET})\n")
    try:
        if admin:
            windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(cast(Iterable[str], args)), None, True)
        else:
            subprocess.call(" ".join(cast(Iterable[str], [com, *args])), shell=True)
    except Exception as E:
        sys.stderr.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.FG_BRIGHT_RED} Failed to run command:   {ANSI.FG_BRIGHT_RED}{ANSI.REVERSED}{ANSI.BOLD} {E.__class__.__name__}({E}) {ANSI.RESET}\n")
        return

    if not silent:
        sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.RESET} Command Status:          {ANSI.FG_BRIGHT_GREEN}{ANSI.REVERSED}{ANSI.BOLD} Successfully ran command {ANSI.RESET}\n")


def setup_svh() -> None:
    svh = json.dumps(compile_svh(), indent=4)
    with open('.config\\svh.json', 'w') as SVH_F:
        SVH_F.write(svh)
        SVH_F.close()


def setup_esvh() -> None:
    svh = compile_svh()
    tmp = {}
    for script_that_needs in ('Logger', ):
        tmp[f'by{script_that_needs}'] = svh

    svhs = json.dumps(tmp, indent=4)
    del tmp

    with open('.config\\esvh.json', 'w') as SVH_F:
        SVH_F.write(svhs)
        SVH_F.close()


if __name__ == "__main__":
    subprocess.call('', shell=True)
    if os.name == 'nt':  # Only if we are running on Windows
        k = windll.kernel32
        k.SetConsoleMode(k.GetStdHandle(-11), 7)
        _run_command('cls', silent=True)

    else:
        _run_command('clear', silent=True)

    if '--checks-only' in sys.argv and '--no-checks' in sys.argv: raise Exception

    if '--reset-all-svh' in sys.argv:
        setup_esvh()
        setup_svh()
        sys.stdout.write('Reset SVH and ESVH\n')
        if '--checks-only' not in sys.argv:
            sys.exit(0)

    if '--no-checks' not in sys.argv:
        with open('mypy_switches.txt', 'r') as mp_switch:
            mp_flags_str = mp_switch.read()
            mp_switch.close()

        mp_flags = mp_flags_str.replace('\n', ' ').split()
        del mp_flags_str

        _run_command('mypy', '--pretty', '.')
        _run_command('mypy', *mp_flags, '.')
        _run_command(f'pytest', '-vv')

        if input(f"""Do you want to continue with the build?
        ({ANSI.BOLD}{ANSI.FG_BRIGHT_GREEN}1{ANSI.RESET}) Yes
        ({ANSI.BOLD}{ANSI.FG_BRIGHT_GREEN}0{ANSI.RESET}) No
    > """) != '1':
            sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_RED}EXITING{ANSI.RESET}")
            sys.exit(0)

        if '--checks-only' in sys.argv: sys.exit(0)

    lvl = ''
    push = False
    release = False
    recompile = True

    while True:
        print(
f"""Quizzing App - Build Manager
Select the type of build:
    ({ANSI.BOLD}{ANSI.FG_BRIGHT_GREEN}1{ANSI.RESET}) Alpha
    ({ANSI.BOLD}{ANSI.FG_BRIGHT_GREEN}2{ANSI.RESET}) Beta
    ({ANSI.BOLD}{ANSI.FG_BRIGHT_GREEN}3{ANSI.RESET}) Stable
""")
        lvl = input("> ")
        if lvl.strip() in ('1', '2', '3'):
            lvl = {
                1: 'alpha',
                2: 'beta',
                3: 'stable-release'
            }[int(lvl.strip())]
            break
    
    while True:
        print(
f"""Quizzing App - Build Manager
Push changes to github? Answer below:
    ({ANSI.BOLD}{ANSI.FG_BRIGHT_GREEN}0{ANSI.RESET}) No
    ({ANSI.BOLD}{ANSI.FG_BRIGHT_GREEN}1{ANSI.RESET}) Yes
""")
        _p = input("> ")
        if _p.strip() in ('0', '1'):
            push = bool(int(_p.strip()))
            msg = input('\n\tGit: Commit message > ')
            break

    while True:
        print(
f"""Quizzing App - Build Manager
Release changes? Answer below:
({ANSI.BOLD}{ANSI.FG_BRIGHT_GREEN}0{ANSI.RESET}) No
({ANSI.BOLD}{ANSI.FG_BRIGHT_GREEN}1{ANSI.RESET}) Yes
""")
        _p = input("> ")
        if _p.strip() in ('0', '1'):
            release = bool(int(_p.strip()))
            break

    while True:
        print(
            f"""Quizzing App - Build Manager
Recompile installer?
({ANSI.BOLD}{ANSI.FG_BRIGHT_GREEN}0{ANSI.RESET}) No
({ANSI.BOLD}{ANSI.FG_BRIGHT_GREEN}1{ANSI.RESET}) Yes
""")
        _p = input("> ")
        if _p.strip() in ('0', '1'):
            recompile = bool(int(_p.strip()))
            break

    BUILD_NUMBER = _build_number()
    
    if lvl == "alpha":
        BUILD_ID_STR = f"x_x_{BUILD_NUMBER}"
    elif lvl == "beta":
        BUILD_ID_STR = f'x_{BUILD_NUMBER}'
    elif lvl == 'stable-release':
        BUILD_ID_STR = str(BUILD_NUMBER)
    else:
        raise Exception
    
    BUILD_NAME_STR = f"{lvl}_{BUILD_NUMBER}"
    
    sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.RESET} New build number:        {ANSI.FG_BRIGHT_GREEN}{ANSI.REVERSED}{ANSI.BOLD} {BUILD_NUMBER} {ANSI.RESET}\n")
    sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.RESET} New build id:            {ANSI.FG_BRIGHT_GREEN}{ANSI.REVERSED}{ANSI.BOLD} {BUILD_ID_STR} {ANSI.RESET}\n")
    sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.RESET} New build name:          {ANSI.FG_BRIGHT_GREEN}{ANSI.REVERSED}{ANSI.BOLD} {BUILD_NAME_STR} {ANSI.RESET}\n")
    
    _set_build_number(BUILD_NUMBER, BUILD_ID_STR, BUILD_NAME_STR)

    if recompile:
        with open('compile.bat', 'r') as compile_commands:
            commands = compile_commands.readlines()
            compile_commands.close()

        for command in commands:
            if 'rem' not in command and 'echo' not in command and len(command.strip()) > 0:
                _run_command(*command.split())

        ISCC = '"C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"'
        COM = f"\"installer\\installer.iss\""

        _run_command(ISCC, COM)

    sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.RESET} Disabling developer mode\n")
    _disable_dev_mode()

    if '--reset-esvh' in sys.argv:
        try:
            setup_esvh()
        except Exception as E:
            sys.stderr.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.FG_BRIGHT_RED}{ANSI.REVERSED} [ERROR] {ANSI.RESET} Failed to save ESVH (fatal); more information: \n{traceback.format_exc()}\n")

    sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.RESET} Fixing SVH information\n")
    try:
        setup_svh()
    except Exception as E:
        sys.stderr.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.FG_BRIGHT_RED}{ANSI.REVERSED} [ERROR] {ANSI.RESET} Failed to save SVH (fatal); more information: \n{traceback.format_exc()}\n")

    if push:
        _run_command(*f'git commit -a -m \"{msg}\"'.split())
        _run_command(*f'git commit -a -m \"dev::{BUILD_NAME_STR}\"'.split())
        _run_command(*f'git push'.split())

    if release:
        _run_command(*'git pull origin release'.split())
        _run_command(*'git checkout release'.split())
        _run_command(*'git merge master'.split())
        _run_command(*'git push -u origin release'.split())

        _run_command(*'git pull origin master'.split())
        _run_command(*'git checkout master'.split())
        _run_command(*'git merge release'.split())
        _run_command(*'git push -u origin master'.split())

    sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.RESET} Enabling (resetting) developer mode\n")
    _enable_dev_mode()
