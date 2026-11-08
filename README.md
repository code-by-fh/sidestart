# SideStart

Flutter-Starter und GitHub-Template für eigene iOS-, Android-, Windows- und Web-Apps. GitHub Actions baut eine unsignierte iOS-Geräte-App, veröffentlicht IPA und Source-JSON direkt in diesem Repository und hängt die Android-APK an denselben Release an. Lizenz: [MIT](LICENSE).

## SideStart installieren

Nach erfolgreicher Veröffentlichung diese Quelle in SideStore unter **Sources → + / Add Source** hinzufügen:

```text
https://github.com/code-by-fh/sidestart/releases/latest/download/altstore-source.json
```

Die IPA wird mit deinem eigenen Apple Account signiert. SideStore benötigt seine übliche Einrichtung, WLAN und die lokale VPN-Verbindung. Bei kostenloser Signierung muss die App regelmäßig erneuert werden. Details: [Sideloading](docs/SIDELOADING.md).

## Für eine neue App verwenden

Auf GitHub **Use this template → Create a new repository** wählen und das neue App-Repository öffentlich anlegen. Alternativ mit GitHub CLI:

```powershell
gh repo create meine-app --template code-by-fh/sidestart --public --clone
cd meine-app
python scripts/configure_app.py --name meine_app --organization dev.meinname --display-name "Meine App"
git add app-config.json pubspec.yaml lib test
git commit -m "Configure new app"
git push
```

`dev.meinname` und `meine_app` für jede App passend wählen. Flutter erzeugt daraus deren Plattformkennungen. Einzigartige Kennungen ermöglichen die parallele Installation mehrerer Apps. `app-config.json` enthält Projektname, Organisation und Anzeigename. Der Einrichtungsbefehl passt auch Paketimporte, `pubspec.yaml` und die Titel der Beispielapp an.

**Vor dem ersten Erzeugen nativer Plattformverzeichnisse konfigurieren.** Bei bereits vorhandenen nativen Projekten bricht das Skript ab, damit keine alten Bundle-IDs bestehen bleiben. Unveränderte Template-Kopien führen zunächst nur Checks aus. iOS-/Android-Builds und Veröffentlichung starten nach dem Commit eines eigenen Projektnamens oder einer eigenen Organisation.

Nach dem erfolgreichen Build lautet die neue Source-URL:

```text
https://github.com/DEIN-ACCOUNT/DEIN-REPOSITORY/releases/latest/download/altstore-source.json
```

Die Pipeline übernimmt automatisch den Namen des neuen GitHub-Repositories und die Metadaten der gebauten IPA. Ein zusätzliches Download-Repository oder Apple-Zertifikat in GitHub ist nicht nötig.

## Lokal entwickeln

Benötigt werden Python 3.10+, Git und das Flutter-SDK aus `.fvmrc`. Für einen ersten Test unter Windows reicht Chrome. Das SDK kann mit geprüftem Download installiert werden:

```powershell
.\scripts\install-flutter.ps1
# Den vom Skript ausgegebenen PATH-Befehl ausführen, dann:
.\setup.ps1 -Device chrome
```

`bootstrap.py` erzeugt fehlende Plattformprojekte aus den offiziellen Vorlagen des gepinnten SDKs und erhält bestehende Dateien. Erzeugte native Verzeichnisse können für spätere eigene Anpassungen mit ins Repository aufgenommen werden.

Prüfungen:

```powershell
python -m unittest discover -s scripts -p test_*.py
flutter pub get
flutter analyze
flutter test
```

## Builds und Releases

Jeder Push auf `main` oder `master` baut und veröffentlicht die App. Manuelle Läufe sind ebenfalls möglich. Pull Requests veröffentlichen nichts. Die erzeugten Release-Tags wie `v0.1.0-build.3` lösen keine weiteren Builds aus. Die Buildnummer stammt aus `github.run_number`, die sichtbare Version aus `pubspec.yaml`.

Die Source-JSON übernimmt Bundle-ID, App-Name, Version, Buildnummer, Mindest-iOS-Version, Größe und Berechtigungen aus der tatsächlichen IPA. Die Versionshistorie bleibt erhalten. Ein Release wird zunächst als Entwurf mit vollständigen Dateien vorbereitet und erst danach freigeschaltet. Ein Android-Fehler verhindert die iOS-Veröffentlichung nicht.

Das Repository muss öffentlich sein; die Pipeline verwendet ausschließlich das automatisch bereitgestellte `GITHUB_TOKEN` mit Schreibrechten im Release-Job. Für erste Template-Kopien können GitHub Actions beziehungsweise deren Schreibrechte einmalig aktiviert werden müssen.

Die Android-APK verwendet eine Entwicklungs-Signierung für persönliche Tests. Für dauerhafte Android-Updates später einen festen eigenen Schlüssel einrichten.

## Vorhandene IPA manuell veröffentlichen

```powershell
python scripts/publish_source.py --ipa downloads/run-123/sidestart-ios-unsigned.ipa
```

Das Ziel wird aus dem aktuellen GitHub-Repository ermittelt. Ein anderes Ziel lässt sich explizit mit `--repository owner/repo` angeben. Bestehende private Repositories werden vom Publisher nicht eigenständig öffentlich gemacht.
