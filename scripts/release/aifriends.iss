; AIFriends Windows installer (Inno Setup 6)
; 由 build-portable.ps1 调用 ISCC 编译；命令行可覆盖 MyAppVersion / MyAppVersionInfo / SourceDir / OutputDir。
; 简体中文语言包随仓库 vendored（ChineseSimplified.isl），避免依赖 Chocolatey 是否附带非官方翻译。

#ifndef MyAppVersion
  #define MyAppVersion "dev"
#endif
#ifndef MyAppVersionInfo
  #define MyAppVersionInfo "0.0.0"
#endif
#ifndef SourceDir
  #define SourceDir "."
#endif
#ifndef OutputDir
  #define OutputDir "."
#endif

#define MyAppName "AIFriends"
#define MyAppPublisher "ppshuX"
#define MyAppURL "https://github.com/ppshuX/AIFriends"
#define MyAppExeName "start.bat"

[Setup]
; 固定 AppId，升级安装时识别为同一应用（勿随意更改）
AppId={{A1F41E4D-8B2C-4E9F-9D3A-7C5E6F1B2A90}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename=AIFriends-windows-x64-{#MyAppVersion}-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
UninstallDisplayName={#MyAppName}
VersionInfoVersion={#MyAppVersionInfo}
VersionInfoCompany={#MyAppPublisher}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersionInfo}

[Languages]
; ChineseSimplified.isl 与本脚本同目录（仓库内 vendored）
Name: "chinesesimplified"; MessagesFile: "ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 与便携 ZIP 内 AIFriends-windows-x64-<version>/ 布局一致
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent