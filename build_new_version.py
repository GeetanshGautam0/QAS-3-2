import os, sys, json, subprocess
from qa_functions import ANSI, File, SaveFunctionArgs, SaveFile
from datetime import datetime
from ctypes import windll


def _build_number():
    return float(datetime.now().strftime('%y%m%j.%H%M%S%f'))


def _set_build_number(build_number, build_id, build_name):
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


def _run_command(COM: str, *args, admin=False):
    sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.RESET} Running Command:         {ANSI.FG_BRIGHT_GREEN}{ANSI.REVERSED}{ANSI.BOLD} {' '.join([COM, *args]).strip()} {ANSI.RESET} (UAC_ELEVATION: {ANSI.FG_BRIGHT_GREEN}{ANSI.REVERSED}{ANSI.BOLD}{admin}{ANSI.RESET})\n")
    try:
        if admin:
            windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(args), None, True)
        else:
            subprocess.call(" ".join([COM, *args]), shell=True)
    except Exception as E:
        sys.stderr.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.FG_BRIGHT_RED} Failed to run command:   {ANSI.FG_BRIGHT_RED}{ANSI.REVERSED}{ANSI.BOLD} {E.__class__.__name__}({E}) {ANSI.RESET}\n")
        return
    
    sys.stdout.write(f"{ANSI.BOLD}{ANSI.FG_BRIGHT_BLUE}[BUILD_MANAGER]{ANSI.RESET} Command Status:          {ANSI.FG_BRIGHT_GREEN}{ANSI.REVERSED}{ANSI.BOLD} Successfully ran command {ANSI.RESET}\n")


if __name__ == "__main__":
    subprocess.call('', shell=True)
    if os.name == 'nt':  # Only if we are running on Windows
        k = windll.kernel32
        k.SetConsoleMode(k.GetStdHandle(-11), 7)

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
Push changes to gihub? Answer below:
    ({ANSI.BOLD}{ANSI.FG_BRIGHT_GREEN}0{ANSI.RESET}) No
    ({ANSI.BOLD}{ANSI.FG_BRIGHT_GREEN}1{ANSI.RESET}) Yes
""")
        _p = input("> ")
        if _p.strip() in ('0', '1'):
            push = bool(int(_p.strip()))
            msg = input('\n\tGit: Commit message > ')
            extra = input('\n\tGit: Add extra push flags > ')
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
    
    ISCC = '"C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"'
    COM = f"\"installer\\installer.iss\""
    
    _run_command(ISCC, COM, admin=False)
    
    if push:
        _run_command(*f'git commit -a -m \"{msg}\"')
        _run_command(*f'git commit -a -m \"dev::{BUILD_NAME_STR}\"'.split())
        _run_command(*f'git push {extra}'.split())
    