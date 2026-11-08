# SideStart

Minimale Flutter-App mit Offline-Zähler für iOS, Android, Windows und Web. GitHub Actions baut eine unsignierte iOS-Geräte-App und verpackt sie als IPA zum anschließenden Signieren mit SideStore, AltStore Classic oder Sideloadly. Ein eigener Mac und Apple-Signierungsgeheimnisse in GitHub sind für diesen Build-Weg nicht erforderlich.

## Stand und Voraussetzungen

Dieses Projekt wurde unter Windows vorbereitet. Flutter ist auf dem Entwicklungsrechner noch nicht installiert; deshalb wurden Flutter-Analyse, Widget-Tests und native Builds dort noch nicht ausgeführt. Es gibt noch keinen bestätigten GitHub-Actions-Lauf und keinen Installationstest auf einem iPhone. Eine lauffähige IPA lässt sich erst nach einem erfolgreichen macOS-Build und der anschließenden Signierung auf dem Gerät bestätigen.

Die Flutter-Version ist in `.fvmrc` festgelegt: **3.47.9**. Die Startversion der App ist **0.1.0+1**, die iOS-Mindestversion **15.0**. Installiere diese Flutter-Version über [die offiziellen Windows-Anweisungen](https://docs.flutter.dev/install/manual) beziehungsweise einen Versionsmanager und ergänze `flutter/bin` im PATH. Zusätzlich werden Git, Python **3.10+** und für den Push die [GitHub CLI](https://cli.github.com/) benötigt. Für den ersten lokalen Web-Test reicht Chrome; Android- und Windows-Desktop-Builds benötigen die jeweiligen Flutter-Werkzeuge.

Die nativen Plattformverzeichnisse werden bei der ersten Einrichtung mit `scripts/bootstrap.py` aus den offiziellen Vorlagen der festgelegten Flutter-Version erzeugt. Sie sind anfangs noch nicht enthalten, weil das SDK hier fehlt. Der Generator erhält bereits vorhandene Plattformverzeichnisse. Nach der ersten erfolgreichen Erzeugung sollen diese Verzeichnisse ins Repository aufgenommen werden; spätere native Anpassungen gehören dort hinein. Auch CI ruft den Generator auf und kann das vorbereitete Repository deshalb bereits bauen.

## Projekt an den gewünschten Ort übernehmen

Die aktuelle Umgebung erlaubt das Schreiben nach `C:\Development` nicht. Das vorbereitete Projekt liegt deshalb unter `%LOCALAPPDATA%\Temp\sidestart`. Kopiere es vor der weiteren Arbeit mit einer normalen PowerShell in dein Entwicklungsverzeichnis. Der folgende Befehl bricht ab, falls das Ziel bereits existiert, und überschreibt kein vorhandenes Projekt:

```powershell
$sourcePath = Join-Path $env:LOCALAPPDATA 'Temp\sidestart'
$targetPath = 'C:\Development\sidestart'
if (Test-Path -LiteralPath $targetPath) { throw "Ziel existiert bereits: $targetPath" }
New-Item -ItemType Directory -Path 'C:\Development' -Force | Out-Null
Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Recurse -Force
Set-Location -LiteralPath $targetPath
```

## Lokal starten

Für den ersten IPA-Build brauchst du lokal kein Flutter-SDK: Überspringe diesen Abschnitt und verwende direkt `publish.ps1` im nächsten Abschnitt. Das SDK und die nativen Plattformdateien werden dann auf GitHub eingerichtet.

Für lokale Entwicklung kannst du das gepinnte SDK mit geprüftem Download installieren:

```powershell
.\scripts\install-flutter.ps1
```

Das Skript lädt das Windows-SDK aus dem offiziellen Flutter-Archiv, prüft dessen SHA-256 und zeigt den Befehl für den PATH an. Es benötigt Netzwerkzugriff und mehrere GB freien Speicher. Es verändert den systemweiten PATH nicht. Bereits vorhandene SDK-Zielverzeichnisse werden nicht überschrieben.

```powershell
flutter --version
python --version
.\setup.ps1 -Device chrome
```

Das Setup erzeugt die Plattformdateien und führt Dependency-Auflösung, Analyse und Tests aus, bevor es die App startet. Alternativ einzeln:

```powershell
python scripts/bootstrap.py
flutter pub get
flutter analyze
flutter test
flutter run -d chrome
```

Der Zähler dient als kleiner Funktionstest. Sein Stand wird beim Neustart zurückgesetzt; es gibt kein Konto und keinen Server.

## Repository pushen und IPA bauen

Der kürzeste Weg nach dem Kopieren des Projekts:

```powershell
gh auth login
.\publish.ps1
```

`publish.ps1` verwendet den vorhandenen lokalen Git-Commit beziehungsweise erstellt bei einem entpackten Archiv den Erstcommit, legt ohne vorhandenen `origin` ein **privates** Repository namens `sidestart` an, pusht und wartet auf den Actions-Lauf genau dieses Commits. Danach lädt es die IPA und ihre Prüfsumme nach `downloads/run-<ID>/`. Ein anderer Name ist mit `-Repository mein-app-name` möglich. Bestehende Remotes werden verwendet. Uncommittete Änderungen musst du vorher prüfen und committen. Wenn GitHub Actions für dein Konto deaktiviert ist oder keine macOS-Minuten verfügbar sind, muss das zuerst auf GitHub behoben werden.

Die folgenden Einzelbefehle sind eine Alternative zum Hilfsskript, nicht zusätzlich erforderlich.

Die GitHub-Anmeldung auf diesem Rechner ist aktuell ungültig. Melde dich zunächst selbst an; Apple-Zugangsdaten werden für CI nicht benötigt:

```powershell
gh auth login
gh auth status
git init -b main
git add .
git commit -m "Initial SideStart Flutter app and sideload builds"
gh repo create sidestart --private --source . --remote origin --push
```

Falls du bereits ein Git-Repository eingerichtet hast, überspringe Initialisierung und Erstcommit und verwende gegebenenfalls deinen vorhandenen Remote. Der neue private Repositoryname `sidestart` muss in deinem Account noch frei sein. GitHub Actions muss für das Repository aktiviert sein; bei privaten Repositories können verfügbare Minuten beziehungsweise Abrechnung die macOS-Ausführung begrenzen.

Der Workflow [builds.yml](.github/workflows/builds.yml) startet bei Pushes auf `main` und `master`, bei passenden Versionstags und manuell. Die normale Push-Ausführung liefert die IPA als Actions-Artefakt. Prüfe den tatsächlichen Lauf und lade dessen Artefakte herunter:

```powershell
gh run list --workflow builds.yml --limit 5
gh run watch <RUN_ID> --exit-status
gh run download <RUN_ID> --dir downloads
Get-ChildItem -Path downloads -Recurse -Filter *.ipa
```

Ersetze `<RUN_ID>` durch die numerische ID des gewünschten Laufs. `gh run download` entpackt die Artefaktarchive; die IPA selbst bleibt eine Datei. Bei Bedarf manuell neu starten:

```powershell
gh workflow run builds.yml --ref main
```

Für einen versionierten GitHub Release mit IPA, SHA-256-Prüfsumme und Android-APK:

```powershell
git tag v0.1.0
git push origin v0.1.0
```

Der Tag muss zur Version in `pubspec.yaml` passen. Für Folgeversionen zuerst die Version ändern, committen und pushen; anschließend den passenden neuen Tag anlegen. Releases eines privaten Repositories bleiben privat. Eine öffentliche SideStore-Quelle ist für den direkten Import der heruntergeladenen IPA nicht nötig.

Die CI-Buildnummer kommt aus `github.run_number`; die sichtbare App-Version stammt aus `pubspec.yaml`. Die Android-APK verwendet für diesen Starter eine Entwicklungs-Signierung. Da die CI-Testschlüssel zwischen Läufen wechseln können, kann bei Android-Updates eine Neuinstallation nötig sein. Für dauerhaft verteilte Android-Apps später einen festen eigenen Signierschlüssel konfigurieren.

## Auf dem iPhone installieren

Die erzeugte IPA ist **unsigniert** und kann nicht direkt durch Antippen installiert werden. SideStore oder ein anderer Sideloader signiert sie mit deinem Apple Account. Die Anleitung mit Windows-Einrichtung, Developer Mode und regelmäßiger Erneuerung steht in [docs/SIDELOADING.md](docs/SIDELOADING.md).

Die technischen Quellen und Entscheidungen sind in [docs/RESEARCH.md](docs/RESEARCH.md) dokumentiert. Der tatsächlich ausgeführte Prüfstand steht in [docs/VALIDATION.md](docs/VALIDATION.md).
