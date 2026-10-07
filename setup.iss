; KyteRename - Inno Setup 現代安裝程式設定檔
; 適用於 Inno Setup 6.x / 7.x

#define MyAppName "KyteRename"
#define MyAppVersion "1.1.1"
#define MyAppPublisher "ais7896-hue"
#define MyAppURL "https://github.com/ais7896-hue/KyteRename"
#define MyAppExeName "KyteRename.exe"

[Setup]
AppId={{5E6F7A8B-9C0D-1E2F-3A4B-5C6D7E8F9A0B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=LICENSE
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=KyteRename_Setup_{#MyAppVersion}

[Languages]
Name: "chinesetrad"; MessagesFile: "compiler:Languages\ChineseTraditional.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
chinesetrad.SystemIntegration=系統整合:
chinesetrad.ContextMenuDesc=新增至 Windows 右鍵選單「使用 KyteRename 批次整理」 (推薦)
chinesetrad.ContextMenuName=使用 KyteRename 批次整理

english.SystemIntegration=System Integration:
english.ContextMenuDesc=Add "Batch Rename with KyteRename" to Windows context menu (Recommended)
english.ContextMenuName=Batch Rename with KyteRename

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "contextmenu"; Description: "{cm:ContextMenuDesc}"; GroupDescription: "{cm:SystemIntegration}"; Flags: checkablealone

[Files]
Source: "dist\KyteRename\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\KyteRename\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; 右鍵選單：資料夾項目右鍵
Root: HKCU; Subkey: "Software\Classes\Directory\shell\KyteRename"; ValueType: string; ValueData: "{cm:ContextMenuName}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\KyteRename"; ValueType: string; ValueName: "Icon"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\KyteRename\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey; Tasks: contextmenu

; 右鍵選單：資料夾空白處背景右鍵
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\KyteRename"; ValueType: string; ValueData: "{cm:ContextMenuName}"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\KyteRename"; ValueType: string; ValueName: "Icon"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\Background\shell\KyteRename\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" ""%V"""; Flags: uninsdeletekey; Tasks: contextmenu

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
