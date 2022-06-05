; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "Quizzing Application 3"
#define MyAppBuildNumber "1"  
#define MyAppVersion "3.0"
#define MyAppPublisher "Geetansh Gautam"
#define MyAppURL "https://geetanshgautam.wixsite.com/home"
#define SetupEXEName "qa_update_app.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{F9E57D15-6FBF-43D3-9655-7774A92A4BF9}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no
DisableWelcomePage=no
DisableDirPage=no
; Uncomment the following line to run in non administrative install mode (install for current user only.)
;PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=D:\User Files\OneDrive\Documents\2. Electronics\1. Python\QAS 3-2\installer
OutputBaseFilename=QuizzingAppInstaller
SetupIconFile=D:\User Files\OneDrive\Documents\2. Electronics\1. Python\QAS 3-2\.src\.icons\.app_ico\setup.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "addons_theme"; Description: "Install 'Official Themes Addon' package"; GroupDescription: "ADDONS"; Flags: unchecked

[Files]
Source: "D:\User Files\OneDrive\Documents\2. Electronics\1. Python\QAS 3-2\installer\.config\*"; DestDir: "{app}\.config"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "D:\User Files\OneDrive\Documents\2. Electronics\1. Python\QAS 3-2\installer\.qa_update\*"; DestDir: "{app}\.qa_update"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Run]
Filename: "{app}\.qa_update\{#SetupEXEName}"; Parameters: "install"; WorkingDir: "{app}"; StatusMsg: "Installing Modules (ADMIN REQURIED)"; Flags: shellexec hidewizard waituntilterminated
Filename: "{app}\.qa_update\{#SetupEXEName}"; Parameters: "addon -a ADDONS_THEME"; WorkingDir: "{app}"; Tasks: addons_theme; StatusMsg: "Installing Official Themes Addon"; Flags: shellexec hidewizard waituntilterminated

[UninstallDelete]
; <test::uninstaller> start_here

Type: filesandordirs; Name: "{app}\.config"
Type: filesandordirs; Name: "{app}\.qa_update"
Type: filesandordirs; Name: "{app}\.src"
Type: filesandordirs; Name: "{app}\*.py"
Type: filesandordirs; Name: "{app}\.gitignore"
Type: filesandordirs; Name: "{app}\qa_files"
Type: filesandordirs; Name: "{app}\qa_functions"
Type: filesandordirs; Name: "{app}\qa_installer_functions"
Type: filesandordirs; Name: "{app}\_config.yml"
Type: filesandordirs; Name: "{app}\compile.bat"
Type: filesandordirs; Name: "{app}\README.md"
Type: filesandordirs; Name: "{app}\.github"
Type: filesandordirs; Name: "{app}\mypy.ini"
Type: filesandordirs; Name: "{app}\pyproject.toml"
Type: filesandordirs; Name: "{app}\requirements.txt"
Type: filesandordirs; Name: "{app}\qa_ui"
Type: filesandordirs; Name: "{app}\TEST_ALL.bat"
Type: filesandordirs; Name: "{app}\qa_auto_tests"
Type: filesandordirs; Name: "{app}\mypy_switches.txt"

; <test::uninstaller> stop_here

[Messages]
BeveledLabel=Geetansh Gautam

