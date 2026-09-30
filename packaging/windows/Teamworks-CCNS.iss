; Teamworks-CCNS — installateur Windows x64
; Garde-fou : cet installateur ne doit jamais créer, migrer, déplacer,
; supprimer ou écraser une base utilisateur. Il installe les fichiers
; applicatifs sous {app} et peut uniquement mémoriser la préférence
; d'affichage des ressources historiques dans Customize.ini.

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
Source: "..\..\dist\Teamworks-CCNS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Teamworks-CCNS"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\Teamworks-CCNS"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,Teamworks-CCNS}"; Flags: nowait postinstall skipifsilent


[Code]
var
  LegacyResourcesPage: TInputOptionWizardPage;

function LegacyCustomizePath(): String;
begin
  Result := ExpandConstant('{userappdata}\teamworks\Customize.ini');
end;

procedure InitializeWizard;
var
  ExistingValue: String;
begin
  LegacyResourcesPage := CreateInputOptionPage(
    wpSelectTasks,
    'Ressources historiques Teamworks / Noethys',
    'Conserver les liens historiques du projet d''origine',
    'Ces liens restent optionnels et n''affectent jamais les crédits, la licence '
      + 'ou les mentions de provenance. Ce choix pourra aussi être modifié dans '
      + 'les préférences de Teamworks-CCNS.',
    False,
    False
  );
  LegacyResourcesPage.Add(
    'Afficher les liens et ressources historiques Teamworks / Noethys'
  );

  ExistingValue := GetIniString(
    'historique',
    'afficher_ressources',
    '1',
    LegacyCustomizePath()
  );
  LegacyResourcesPage.Values[0] := ExistingValue <> '0';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigPath: String;
  ConfigDir: String;
  ConfigValue: String;
begin
  if CurStep = ssPostInstall then
  begin
    ConfigPath := LegacyCustomizePath();
    ConfigDir := ExtractFileDir(ConfigPath);
    ForceDirectories(ConfigDir);

    if LegacyResourcesPage.Values[0] then
      ConfigValue := '1'
    else
      ConfigValue := '0';

    SetIniString(
      'historique',
      'afficher_ressources',
      ConfigValue,
      ConfigPath
    );
  end;
end;
