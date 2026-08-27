; Teamworks-CCNS — installateur Windows x64
; Garde-fou : cet installateur ne doit jamais créer, migrer, déplacer,
; supprimer ou écraser une base utilisateur. Il installe uniquement
; les fichiers applicatifs sous {app} et les raccourcis Windows.

#ifndef AppVersion
  #define AppVersion "0.0.0-dev"
#endif

#define AppName "Teamworks-CCNS"
#define AppExeName "Teamworks-CCNS.exe"

[Setup]
AppId={{4D07F1CF-3352-4CE3-8CD8-37BE85E51D28}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
DefaultDirName={autopf}\Teamworks-CCNS
DefaultGroupName=Teamworks-CCNS
DisableProgramGroupPage=yes
DirExistsWarning=no
OutputDir=..\..\dist\installer
OutputBaseFilename=Teamworks-CCNS-{#AppVersion}-windows-x64-setup
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
Source: "..\..\dist\Teamworks-CCNS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Teamworks-CCNS"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\Teamworks-CCNS"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,Teamworks-CCNS}"; Flags: nowait postinstall skipifsilent
