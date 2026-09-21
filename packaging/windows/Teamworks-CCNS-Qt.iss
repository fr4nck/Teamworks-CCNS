; Teamworks-CCNS Qt Vanilla 0.1 — installateur Windows x64
; Installé côte à côte avec la Vanilla wx pendant la transition.
; Aucune base, configuration ou donnée utilisateur n'est créée, déplacée ou supprimée.

#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

#define AppName "Teamworks-CCNS Qt Vanilla"
#define AppExeName "Teamworks-CCNS-Qt.exe"

[Setup]
AppId={{CB1D45F1-67A8-4C7D-A2E2-1FA0C5D61C01}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
DefaultDirName={autopf}\Teamworks-CCNS-Qt
DefaultGroupName=Teamworks-CCNS Qt Vanilla
DisableProgramGroupPage=yes
DirExistsWarning=no
OutputDir=..\..\dist\qt-vanilla\installer
OutputBaseFilename=Teamworks-CCNS-Qt-{#AppVersion}-windows-x64-setup
SetupIconFile=..\..\teamworks\Static\Images\Branding\Teamworks-CCNS.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\qt-vanilla\Teamworks-CCNS-Qt\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Teamworks-CCNS Qt Vanilla"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\Teamworks-CCNS Qt Vanilla"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,Teamworks-CCNS Qt Vanilla}"; Flags: nowait postinstall skipifsilent
