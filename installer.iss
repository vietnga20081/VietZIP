; Inno Setup Script for VietZIP 2.0
; Can be compiled with ISCC.exe

#define MyAppName "VietZIP"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "VietZIP Team"
#define MyAppExeName "VietZIP.exe"

[Setup]
AppId={{D37F2C5A-9D2E-4F3A-B162-8E3A7E294B10}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=VietZIP_InnoSetup_v{#MyAppVersion}
SetupIconFile=assets\vietzip.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "contextmenu"; Description: "Tích hợp vào menu chuột phải Windows Explorer"; GroupDescription: "Tùy chọn hệ thống:"

[Files]
Source: "dist\VietZIP\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Context menu cho mọi file
Root: HKCU; Subkey: "Software\Classes\*\shell\VietZIP.Compress"; ValueType: string; ValueData: "Nén bằng VietZIP"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\*\shell\VietZIP.Compress"; ValueType: string; ValueName: "Icon"; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\*\shell\VietZIP.Compress\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" compress ""%1"""; Tasks: contextmenu

; Context menu cho thư mục
Root: HKCU; Subkey: "Software\Classes\Directory\shell\VietZIP.Compress"; ValueType: string; ValueData: "Nén bằng VietZIP"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\VietZIP.Compress"; ValueType: string; ValueName: "Icon"; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\Directory\shell\VietZIP.Compress\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" compress ""%1"""; Tasks: contextmenu

; Context menu cho file .zip
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.zip\shell\VietZIP.Extract"; ValueType: string; ValueData: "Giải nén bằng VietZIP"; Flags: uninsdeletekey; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.zip\shell\VietZIP.Extract"; ValueType: string; ValueName: "Icon"; ValueData: """{app}\{#MyAppExeName}"",0"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\SystemFileAssociations\.zip\shell\VietZIP.Extract\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" extract ""%1"""; Tasks: contextmenu

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
