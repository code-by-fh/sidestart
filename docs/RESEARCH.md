# Technische Recherche

Recherche am 8. November 2026. Die folgenden Links sind die Quellen der technischen Entscheidungen. Die Dokumentation und Workflow-Dateien wurden gelesen; eine erfolgreiche Ausführung dieses Projekts auf GitHub oder einem iPhone ist damit noch nicht nachgewiesen.

## Flutter unter Windows und iOS in der Cloud

[Flutter: iOS deployment](https://docs.flutter.dev/deployment/ios) beschreibt die iOS-Build- und Distributionswerkzeuge. Xcode und macOS bleiben für das Kompilieren des iOS-Targets erforderlich. Ein GitHub-gehosteter macOS-Runner übernimmt diesen Schritt; die Bearbeitung des Dart-Projekts findet unter Windows statt. Für den Sideload-Weg wird eine Geräte-App im Release-Modus ohne Apple-Signierung erstellt und anschließend als IPA verpackt.

Das Projekt legt die SDK-Version in `.fvmrc` fest und erzeugt fehlende Plattformverzeichnisse mit dem installierten SDK aus offiziellen Flutter-Vorlagen. Damit wird kein von Hand nachgebautes Xcode-Projekt als angeblich geprüft ausgeliefert. Solange das SDK fehlt, bleiben lokale Flutter-Prüfungen ausdrücklich ausstehend.

## NOOP als konkretes Vorbild

Das vom Nutzer genannte [NOOP-Repository](https://github.com/ryanbr/noop) dokumentiert den direkten IPA-Download und den Import mit AltStore beziehungsweise SideStore. NOOP selbst verwendet native Swift-Targets; der Distributionsweg ist trotzdem auf eine Flutter-Geräte-App übertragbar.

Die überprüfte [Release-Pipeline `fork-release.yml`](https://github.com/ryanbr/noop/blob/main/.github/workflows/fork-release.yml) baut das iOS-Target auf macOS im Release-Modus mit deaktivierter Code-Signierung, verpackt die App in einem `Payload`-Verzeichnis und lädt die IPA als Release-Datei hoch. Dessen `app-build.yml` ist dagegen primär eine Compile-/Testprüfung. NOOPs zusätzliche Behandlung für Widgets, HealthKit und App Groups ist für die minimale SideStart-App ohne diese Fähigkeiten nicht erforderlich. Einzelne Aussagen oder Fehlerdiagnosen in NOOPs Dokumentation ersetzen keinen Gerätetest unseres Projekts.

## Signieren mit einem kostenlosen Apple Account

[Apples Entwicklerkontoübersicht](https://developer.apple.com/help/account/basics/about-your-developer-account) bestätigt die Personal-Team-Grenzen: zehn App IDs, drei Geräte, drei Apps pro Gerät und sieben Tage Gültigkeit der Provisionierung. Dieses Projekt benötigt für den CI-Build weder einen kostenpflichtigen Apple-Developer-Account noch Zertifikate oder Apple-Zugangsdaten in GitHub. Die nachgelagerte persönliche Signierung erfolgt beim Sideloader.

[SideStore FAQ](https://docs.sidestore.io/docs/faq) beschreibt das erneute Signieren mit persönlichen Entwicklungszertifikaten und regelmäßige Hintergrundaktualisierung. SideStore selbst belegt einen der drei App-Plätze. Die aktuelle [Windows-Ersteinrichtung](https://docs.sidestore.io/docs/installation/prerequisites) verwendet iloader und LocalDevVPN; WLAN sowie die lokale VPN-Verbindung sind für Installation, Updates und Erneuerung erforderlich. [Die Installationsanleitung](https://docs.sidestore.io/docs/installation/install) erläutert das Vertrauen des Profils, den Entwicklermodus und die erste manuelle Erneuerung.

## GitHub-Artefakte und Releases

[GitHub: Artefakte speichern](https://docs.github.com/en/actions/how-tos/writing-workflows/choosing-what-your-workflow-does/storing-and-sharing-data-from-a-workflow) beschreibt Build-Artefakte und deren Aufbewahrung. Ein Push-Build kann dadurch eine IPA zum angemeldeten Download bereitstellen. [GitHub: Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases) beschreibt versionierte Veröffentlichungen und angehängte Dateien. Die Releases dieses Projekts werden durch Versionstags ausgelöst und enthalten neben der IPA eine Prüfsumme und eine Android-APK.

[GitHub: gehostete Runner](https://docs.github.com/en/actions/concepts/runners/github-hosted-runners) dokumentiert die verfügbaren Betriebssysteme und Abrechnung. Für private Repositories müssen verfügbare Minuten beziehungsweise die jeweilige Abrechnung berücksichtigt werden. Ohne gültige GitHub-Anmeldung wurde hier noch kein Remote angelegt oder gepusht.

## Eine eigene SideStore-/AltStore-Quelle ist optional

[AltStore: Make a Source](https://faq.altstore.io/developers/make-a-source) dokumentiert ein JSON-Format mit App-Metadaten und Versionsliste. Bundle-ID, Version, Buildnummer, Dateigröße und Berechtigungen müssen zum tatsächlich gebauten Paket passen. Eine öffentliche Quelle benötigt ohne Anmeldung erreichbare Metadaten-, Icon- und IPA-URLs. Private GitHub-Dateien sind dafür kein geeigneter öffentlicher Endpunkt.

Für den ersten funktionsfähigen Build genügt der direkte IPA-Download mit anschließendem Import. Eine Quelle wird deshalb noch nicht mit Platzhalter-Downloadlinks ausgeliefert. Sie kann ergänzt werden, sobald ein öffentlicher Release-Endpunkt und dessen tatsächliche Paketmetadaten vorhanden sind.
