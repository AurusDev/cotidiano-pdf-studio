; installer_cotidiano.iss
; Script do Inno Setup para Cotidiano PDF Studio

[Setup]
AppId={{D7A6F2D2-1234-4FA9-ABCD-0000COTIDIANO}}   ; GUID qualquer, só não repetir em outro app
AppName=Cotidiano PDF Studio
AppVersion=1.0.0
AppPublisher=Seu Nome
DefaultDirName={pf}\Cotidiano PDF Studio
DefaultGroupName=Cotidiano PDF Studio
OutputBaseFilename=CotidianoPDFStudioSetup
Compression=lzma
SolidCompression=yes
DisableDirPage=no
DisableProgramGroupPage=no
WizardStyle=modern

; Ícone do instalador (opcional, pode remover se quiser)
SetupIconFile=assets\codex_pdf.ico

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
; Copia tudo o que o PyInstaller gerou
; ATENÇÃO: caminho relativo à pasta onde o .iss está
Source: "dist\Cotidiano PDF Studio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
; Atalho no menu iniciar
Name: "{group}\Cotidiano PDF Studio"; Filename: "{app}\Cotidiano PDF Studio.exe"; IconFilename: "{app}\Cotidiano PDF Studio.exe"
; Atalho na área de trabalho
Name: "{commondesktop}\Cotidiano PDF Studio"; Filename: "{app}\Cotidiano PDF Studio.exe"; IconFilename: "{app}\Cotidiano PDF Studio.exe"

[Run]
; Pergunta se o usuário quer abrir o programa ao final da instalação
Filename: "{app}\Cotidiano PDF Studio.exe"; Description: "Executar Cotidiano PDF Studio"; Flags: nowait postinstall skipifsilent
