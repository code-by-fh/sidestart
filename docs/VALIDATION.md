# Prüfstand der Vorbereitung

Stand: 8. November 2026. Unter Windows ausgeführt:

- `python -m unittest discover -s scripts -p test_*.py -v`: **12 Tests erfolgreich**. Sie prüfen das Erhalten vorhandener Plattformdateien, isolierte Vorlagenerzeugung, iOS-Mindestversion sowie Erkennung unvollständiger, falsch verpackter oder ungeeigneter App-Bundles. Die Test-Bundles sind synthetische Dateien, keine kompilierten iOS-Apps.
- PowerShell-Parser: `setup.ps1`, `publish.ps1` und `scripts/install-flutter.ps1` syntaktisch gültig.
- Workflow-YAML lokal gelesen und Job-Abhängigkeiten geprüft.
- Zwei Sub-Agents haben Recherche und technische Prüfung beigetragen. Es wurde kein konkreter Build-Blocker gefunden.

Noch ausstehend:

- `flutter analyze`, `flutter test`, SDK-Installation und native Plattform-Erzeugung: Flutter ist lokal nicht installiert; Shell-Netzwerkzugriff ist in der Vorbereitung eingeschränkt.
- Echter GitHub-Actions-Lauf mit Xcode und Erzeugung einer IPA: Die vorhandene GitHub-CLI-Anmeldung ist ungültig. Es wurde kein Remote erstellt und nichts gepusht.
- Signierung, Installation und Start auf einem echten iPhone: Dafür muss die erzeugte IPA mit einem persönlichen Sideloader installiert werden.

Der Dateisystemschutz verweigerte das Anlegen von `C:\Development\sidestart` und `C:\Users\flori\Development\sidestart`. Das vollständige Starter-Repository wurde deshalb im schreibbaren `%LOCALAPPDATA%\Temp\sidestart` vorbereitet. Vor dauerhafter Verwendung an den gewünschten Ort kopieren; siehe README.

Eine erfolgreiche Python-Prüfung ist kein Nachweis einer funktionierenden iOS-App. Der erste Actions-Lauf prüft die echte Kompilierung und Paketstruktur; der Gerätetest bestätigt den Start nach dem Signieren.
