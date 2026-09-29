; ============================================================================
; TsukiSynth installer script for Inno Setup -- DRAFT, NEVER COMPILED
; ============================================================================
; WF0925-G1, 2026-09-25.
; 狀態：草稿。開發機上沒有安裝 Inno Setup，本檔**從未編譯、從未試裝**。
;       編譯與試裝前請先讀同資料夾的 README.md（未驗證項目、待月月裁決項目都列在那裡）。
;
; What this script installs (Windows x64 only):
;   - VST3 plug-in bundle  -> {commoncf64}\VST3\TsukiSynth.vst3\  (the whole bundle folder)
;   - Standalone app       -> {app}\TsukiSynth.exe   ({app} defaults to C:\Program Files\TsukiSynth)
;   - CLI renderer         -> {app}\TsukiSynthCLI.exe (the Standalone's Score console looks for it
;                             next to TsukiSynth.exe: src/ScoreConsole.h findCli())
;   - EULA.txt and THIRD_PARTY_NOTICES.txt -> {app}\
; The EULA is shown on the license page and must be accepted before installing.
; Uninstall removes only the files installed here. User data is NOT touched:
;   %APPDATA%\TsukiSynth\Presets, %APPDATA%\TsukiSynth\IR,
;   Documents\TsukiSynth\Recordings, Desktop\TsukiSynth_Renders.
; ============================================================================

; "x64compatible" (used below) was introduced in Inno Setup 6.3.0.
#if VER < EncodeVer(6,3,0)
  #error Inno Setup 6.3.0 or newer is required to compile this script.
#endif

#define AppName        "TsukiSynth"
; Version comes from CMakeLists.txt line 2: project(TsukiSynth VERSION 0.3.0).
; Keep the two in sync; the release rule (version <-> git tag) is still open (status check E13/S10).
#define AppVersion     "0.3.0"
; Publisher = COMPANY_NAME in CMakeLists.txt juce_add_plugin(). 待月月確認對外名稱（EULA 空格 E1）。
#define AppPublisher   "TsKR"
; AppId must never change between versions, or upgrades will not find the previous install.
#define AppIdGuid      "{{FC4D29B8-412E-4982-A4F2-4BF404A3BCDD}"

#define InstallerDir   RemoveBackslashUnlessRoot(SourcePath)
#define RepoRoot       InstallerDir + "\..\.."
; Binaries are taken from the integration build tree (build\, Release config).
; Only the integration card rebuilds build\ (WF0925 rules).
#define BuildDir       RepoRoot + "\build"
#define Vst3BundleDir  BuildDir + "\TsukiSynth_artefacts\Release\VST3\TsukiSynth.vst3"
#define StandaloneExe  BuildDir + "\TsukiSynth_artefacts\Release\Standalone\TsukiSynth.exe"
#define CliExe         BuildDir + "\TsukiSynthCLI_artefacts\Release\TsukiSynthCLI.exe"
#define NoticesFile    RepoRoot + "\THIRD_PARTY_NOTICES.txt"
; EULA.txt is NOT in the repo on purpose: it must be the text 月月 approved
; (from docs/legal/EULA_BUYER_DRAFT.md, placeholders filled, saved as UTF-8 plain text).
#define EulaFile       InstallerDir + "\EULA.txt"

#if !FileExists(EulaFile)
  #error EULA.txt not found next to this script. Export the approved EULA first (see README.md). The draft must not be shipped.
#endif
#if !FileExists(NoticesFile)
  #error THIRD_PARTY_NOTICES.txt not found at the repository root.
#endif
#if !FileExists(Vst3BundleDir + "\Contents\x86_64-win\TsukiSynth.vst3")
  #error VST3 bundle not found. Build the Release VST3 target into build\ first.
#endif
#if !FileExists(StandaloneExe)
  #error Standalone TsukiSynth.exe not found. Build the Release Standalone target into build\ first.
#endif
#if !FileExists(CliExe)
  #error TsukiSynthCLI.exe not found. Build the Release TsukiSynthCLI target into build\ first.
#endif

[Setup]
AppId={#AppIdGuid}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
; AppPublisherURL / AppSupportURL: 待月月提供網址（VST3 moduleinfo.json 的 URL 目前是空的，盤點 S10）。
;AppPublisherURL=
;AppSupportURL=
VersionInfoVersion={#AppVersion}
VersionInfoProductName={#AppName}

; 64-bit only. Both directives are needed so that {commoncf64}/{autopf} resolve to the
; 64-bit folders and Setup refuses to run on 32-bit Windows.
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Writing to C:\Program Files\Common Files\VST3 requires administrator rights.
PrivilegesRequired=admin

DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
UsePreviousAppDir=yes

LicenseFile={#EulaFile}

UninstallDisplayName={#AppName} {#AppVersion}
UninstallDisplayIcon={app}\TsukiSynth.exe

OutputDir={#RepoRoot}\output\installer
OutputBaseFilename=TsukiSynth-{#AppVersion}-win-x64-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

; Code signing: the monetization plan says the first release is not signed
; (docs/MONETIZATION_PLAN_2026-09-16.zh-TW.md §3). No SignTool entry on purpose.

[Types]
Name: "full";   Description: "Full installation (VST3 + Standalone + CLI renderer)"
Name: "custom"; Description: "Custom installation"; Flags: iscustom

[Components]
Name: "vst3";       Description: "VST3 plug-in (C:\Program Files\Common Files\VST3\TsukiSynth.vst3)"; Types: full custom
Name: "standalone"; Description: "Standalone application"; Types: full custom
; The CLI is what the Standalone's Score console runs. Default on in "full".
; 待月月確認：CLI 要不要隨商品發行（盤點 release-readiness:C2 也提到範例譜的授權白名單）。
Name: "cli";        Description: "Command-line score renderer (used by the Standalone Score console)"; Types: full

[Files]
; VST3: copy the whole bundle folder (Contents\x86_64-win\TsukiSynth.vst3, Contents\Resources\moduleinfo.json, ...).
Source: "{#Vst3BundleDir}\*"; DestDir: "{commoncf64}\VST3\TsukiSynth.vst3"; Components: vst3; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#StandaloneExe}"; DestDir: "{app}"; Components: standalone; Flags: ignoreversion
Source: "{#CliExe}"; DestDir: "{app}"; Components: cli; Flags: ignoreversion
; Legal texts are always installed, whichever components are chosen.
Source: "{#EulaFile}"; DestDir: "{app}"; DestName: "EULA.txt"; Flags: ignoreversion
Source: "{#NoticesFile}"; DestDir: "{app}"; DestName: "THIRD_PARTY_NOTICES.txt"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\TsukiSynth.exe"; WorkingDir: "{app}"; Components: standalone
Name: "{autoprograms}\{#AppName} - Third-party notices"; Filename: "{app}\THIRD_PARTY_NOTICES.txt"
Name: "{autoprograms}\{#AppName} - License agreement"; Filename: "{app}\EULA.txt"

[Run]
Filename: "{app}\THIRD_PARTY_NOTICES.txt"; Description: "Open the third-party notices"; Flags: postinstall shellexec skipifsilent unchecked

; No [UninstallDelete] section on purpose: presets, imported IRs, recordings and
; renders are user data and stay on the computer after uninstall.

; ============================================================================
; VC++ runtime -- 待月月裁決（兩案二選一，下面兩個區塊都先註解掉）
; ============================================================================
; 事實（2026-09-25 掃描 build\ 的三個 binary，reports/gate_outputs/wf0925_G1_sources.txt §4）：
;   VST3、Standalone、CLI 都動態連結 MSVCP140.dll、MSVCP140_2.dll、VCRUNTIME140.dll、
;   VCRUNTIME140_1.dll（加上 api-ms-win-crt-*）。買家電腦沒裝 Microsoft Visual C++
;   可轉散發套件時，DAW 可能載不進外掛（盤點 engineering-gaps:E4）。
;
; ---- 甲案：靜態 CRT（installer 不用動）----
;   改 CMakeLists.txt 讓 MSVC 靜態連結 C/C++ runtime，重建後 binary 不再依賴上述 DLL。
;   會動 CMakeLists（C++ lane，走 R6，並要證明 8/8 位元不變或依 R10 停下回報）；
;   本卡不動 CMakeLists。選甲案時，下面乙案整段刪掉即可。
;   改完用 output\wf0925\G1\scan_binaries.py（或同等工具）確認 DLL imports 裡沒有 MSVCP140*/VCRUNTIME140*。
;
; ---- 乙案：安裝包附 Microsoft 的 vc_redist.x64.exe ----
;   - 檔案來源：Visual Studio 安裝目錄附的 vc_redist.x64.exe，或 Microsoft 官方永久連結
;     https://aka.ms/vc14/vc_redist.x64.exe（下載需月月同意；AI 不下載執行檔）。
;   - Microsoft 文件：只有持有 Visual Studio 授權的使用者可以轉散發，且受 Microsoft 授權條款約束；
;     可轉散發套件的版本必須「same or later than」建置用的 MSVC Build Tools 版本。
;   - 本機建置用的編譯器：19.50.35730.0（build\CMakeCache 的 CMAKE_CXX_COMPILER_VERSION）。
;     對應的 runtime 最低版本號：待確認（本卡沒有查到官方對照表，不猜）。
;   - 已安裝版本可讀登錄 HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64
;     的 Major/Minor/Bld/Rbld（REG_DWORD）；已有更新版時不要再裝（Microsoft 文件：否則安裝會回報失敗）。
;   - 要啟用乙案，把下面各行開頭的 ";;" 拿掉，並填上最低版本。
;
;;[Files]
;;Source: "{#InstallerDir}\redist\vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall
;;
;;[Run]
;;Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Installing Microsoft Visual C++ Redistributable..."; Check: VCRedistNeeded; Flags: waituntilterminated
;;
;;[Code]
;;const
;;  { 待確認：runtime 最低版本（Major.Minor.Bld），見 README.md「乙案」 }
;;  MinMajor = 14;
;;  MinMinor = 0;   { TODO(月月裁決乙案後填) }
;;  MinBld   = 0;   { TODO(月月裁決乙案後填) }
;;
;;function VCRedistNeeded: Boolean;
;;var
;;  Major, Minor, Bld: Cardinal;
;;  Key: String;
;;begin
;;  { In 64-bit install mode the Reg* support functions read the 64-bit registry view. }
;;  Key := 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64';
;;  if not (RegQueryDWordValue(HKEY_LOCAL_MACHINE, Key, 'Major', Major) and
;;          RegQueryDWordValue(HKEY_LOCAL_MACHINE, Key, 'Minor', Minor) and
;;          RegQueryDWordValue(HKEY_LOCAL_MACHINE, Key, 'Bld', Bld)) then
;;  begin
;;    Result := True;   { not installed }
;;    exit;
;;  end;
;;  if Major <> MinMajor then
;;    Result := Major < MinMajor
;;  else if Minor <> MinMinor then
;;    Result := Minor < MinMinor
;;  else
;;    Result := Bld < MinBld;
;;end;
