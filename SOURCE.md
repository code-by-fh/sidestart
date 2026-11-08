# App und Source im selben Repository

SideStart veröffentlicht die IPA und die AltStore-/SideStore-Source direkt unter den Releases von `code-by-fh/sidestart`:

```text
https://github.com/code-by-fh/sidestart/releases/latest/download/altstore-source.json
```

In einer Template-Kopie werden automatisch deren eigener GitHub-Owner und Repositoryname verwendet. Die Source-URL bleibt über alle Releases gleich; die enthaltenen IPA-Links sind versionsgebunden.

Ein Push auf `main` oder `master` erzeugt zuerst einen Geräte-Release-Build ohne Apple-Signierung. Danach erzeugt `make_source.py` JSON, Icon und Prüfsumme aus der IPA. Der Release-Job veröffentlicht diese Dateien mit dem bereitgestellten `GITHUB_TOKEN`. Zusätzliche Zugangsdaten oder ein separates Download-Repository entfallen.

Für lokale Veröffentlichung mit der vorhandenen GitHub-CLI-Anmeldung:

```powershell
python scripts/publish_source.py --ipa downloads/run-123/sidestart-ios-unsigned.ipa
```

Das Repository muss öffentlich sein. Der Publisher verändert dessen Sichtbarkeit nicht. Eine schon veröffentlichte Version/Build-Kombination mit anderen IPA-Bytes wird abgewiesen; für neue Builds eine höhere Buildnummer verwenden. Ältere Versionen werden nicht über neuere gesetzt.

Schema: [AltStore: Make a Source](https://faq.altstore.io/developers/make-a-source). Vorbild: [NOOP source](https://github.com/ryanbr/noop/blob/main/altstore-source.json).
