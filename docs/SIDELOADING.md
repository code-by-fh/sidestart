# SideStart auf einem iPhone installieren

## Was der Build liefert

GitHub Actions kompiliert Flutter im **Release-Modus für ein echtes iOS-Gerät** auf einem macOS-Runner. Anschließend wird `Runner.app` unter `Payload/Runner.app` in eine IPA gepackt. Die Datei trägt noch keine verwendbare Apple-Entwicklersignatur. SideStore, AltStore Classic oder Sideloadly übernimmt das Signieren und die Installation mit deinem eigenen Apple Account. Ein Simulator-Build ist dafür ungeeignet.

Der erfolgreiche CI-Build prüft die Erstellung und Paketstruktur; die tatsächliche Installation und Bedienung auf deinem iPhone bleibt ein separater Test. Dieser Test wurde bei der Vorbereitung noch nicht durchgeführt.

## SideStore mit Windows einrichten

Verwende die aktuellen offiziellen Anleitungen für [Voraussetzungen](https://docs.sidestore.io/docs/installation/prerequisites) und [Installation](https://docs.sidestore.io/docs/installation/install). Die hier überprüfte Einrichtung verwendet **iloader und LocalDevVPN**:

1. Bereithalten: iPhone mit Gerätecode und unterstützter iOS-Version, Apple Account, WLAN und einen Windows-Rechner für die Ersteinrichtung. SideStore selbst unterstützt laut Anleitung iOS 15 oder neuer; maßgeblich für SideStart ist zusätzlich die Mindestversion der gebauten IPA.
2. Die in der offiziellen Anleitung genannten Apple-Gerätetreiber beziehungsweise iTunes und iloader unter Windows installieren.
3. LocalDevVPN gemäß SideStore-Anleitung auf dem iPhone installieren.
4. Das iPhone per USB verbinden und dem Rechner vertrauen. In iloader mit dem Apple Account anmelden und „Install SideStore (Stable)“ wählen.
5. Auf dem iPhone unter Einstellungen → Allgemein → VPN und Geräteverwaltung dem Entwicklerprofil vertrauen. Ab iOS 16 zusätzlich unter Datenschutz & Sicherheit den Entwicklermodus aktivieren und den angeforderten Neustart durchführen. Die genauen Dialoge unterscheiden sich nach iOS-Version.
6. WLAN verwenden, LocalDevVPN verbinden, SideStore öffnen und mit demselben Apple Account anmelden.
7. Unter „My Apps“ SideStore einmal manuell aktualisieren, wie in der offiziellen Anleitung beschrieben.

Apple-Zugangsdaten werden ausschließlich in der von dir eingerichteten Signierungssoftware verwendet. Für dieses Projekt kommen sie weder in Quelldateien noch in GitHub Actions Secrets.

## Die IPA importieren

1. Einen erfolgreichen Lauf von `.github/workflows/builds.yml` abwarten.
2. Das IPA-Artefakt aus dem Actions-Lauf herunterladen und das äußere Artefakt-ZIP entpacken. Alternativ die IPA aus dem GitHub Release herunterladen. Bei privaten Repositories ist dafür eine GitHub-Anmeldung erforderlich.
3. Die `.ipa` auf das iPhone in die Dateien-App übertragen, beispielsweise über einen von dir verwendeten Dateitransferdienst.
4. WLAN und LocalDevVPN aktivieren. In SideStore unter „My Apps“ mit „+“ die IPA auswählen beziehungsweise über die angebotene Importfunktion öffnen.
5. Nach erfolgreicher Signierung und Installation SideStart öffnen. Zähler erhöhen und zurücksetzen; Bildschirmdrehen und einen Neustart der App prüfen.

Die IPA muss zum Import nicht öffentlich gehostet werden. Die JSON-Quelle, wie sie NOOP anbietet, ist eine spätere Komfortfunktion für Veröffentlichung und Updates. Für dieses private Starterprojekt genügt der direkte IPA-Import.

## Gültigkeit und Updates

Ein kostenloser Apple Account erlaubt laut [Apple](https://developer.apple.com/help/account/basics/about-your-developer-account) drei installierte Entwicklungsapps pro Gerät sowie zehn App IDs; die Provisionierung läuft nach sieben Tagen ab. Laut [SideStore FAQ](https://docs.sidestore.io/docs/faq) zählt SideStore selbst zu den drei aktiven Apps.

SideStore versucht Apps im Hintergrund rechtzeitig zu erneuern. Prüfe die Restlaufzeit und eine erfolgreiche Erneuerung regelmäßig; WLAN und die von SideStore verlangte lokale VPN-Verbindung müssen verfügbar sein. Vor Ablauf kann man die Erneuerung auch manuell anstoßen. Nach Updates oder Zurücksetzen des iPhones kann die Einrichtung beziehungsweise Pairing-Datei erneuert werden müssen.

Für ein App-Update die neue IPA aus einem erfolgreichen Build importieren. Behalte die Bundle-ID bei, damit die Signierungssoftware das Paket als dieselbe App behandeln kann. Ändere Versions- und Buildnummer in `pubspec.yaml` für neue veröffentlichte Versionen. Die Beispielapp verwendet keine zusätzlichen Apple-Capabilities und keine App-Erweiterungen.

## Bei Problemen

Prüfe zuerst, dass der GitHub-Lauf vollständig erfolgreich war, die Datei wirklich auf `.ipa` endet und das äußere GitHub-Artefaktarchiv entpackt wurde. Kontrolliere anschließend Entwicklerprofil, Entwicklermodus, WLAN, LocalDevVPN, App-Limit und Restgültigkeit. Falls die Signierung scheitert, den konkreten SideStore-Fehler unter [Troubleshooting](https://docs.sidestore.io/docs/troubleshooting) nachschlagen.

AltStore **Classic** oder [Sideloadly](https://sideloadly.io/) sind alternative Signierungswerkzeuge. AltStore PAL verwendet einen anderen Distributionsweg und ist nicht der hier beschriebene Import unsignierter Entwicklungs-IPAs.
