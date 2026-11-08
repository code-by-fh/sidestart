# SideStore-Quelle

Die Source-URL nach der ersten erfolgreichen Veröffentlichung:

```text
https://github.com/code-by-fh/sidestart-downloads/releases/latest/download/altstore-source.json
```

Diese Adresse in SideStore unter **Sources / Quellen → + / Add Source** eintragen. SideStore lädt die IPA direkt aus dem öffentlichen Download-Repository und signiert sie mit dem eigenen Apple Account. WLAN und die von SideStore verlangte lokale VPN-Verbindung werden weiterhin gebraucht.

Das separate öffentliche Repository `code-by-fh/sidestart-downloads` enthält ausschließlich die IPA, die Source-JSON, ein Icon, eine Prüfsumme und eine kurze README. Das Quellcode-Repository wird nicht öffentlich gemacht. Es werden keine GitHub-Tokens in Dateien oder Actions-Secrets kopiert.

## Neue Version veröffentlichen

Zuerst wie bisher bauen und herunterladen:

```powershell
.\publish.ps1
```

Danach die neueste lokal heruntergeladene IPA veröffentlichen:

```powershell
python scripts/publish_source.py
```

Eine bestimmte IPA oder ein anderes öffentliches Download-Repository:

```powershell
python scripts/publish_source.py --ipa downloads/run-123/sidestart-ios-unsigned.ipa --repository code-by-fh/sidestart-downloads
```

`publish_source.py` verwendet die vorhandene GitHub-CLI-Anmeldung. Es legt das öffentliche Download-Repository bei Bedarf an, erzeugt die Metadaten aus der IPA und veröffentlicht einen Release wie `v0.1.0-build.3`. Ein vorhandenes privates Repository wird niemals automatisch öffentlich gemacht. Ein identischer Release kann erneut geprüft werden; eine bereits veröffentlichte Version/Build-Kombination mit anderen IPA-Bytes wird abgewiesen. Neue Builds benötigen eine höhere Buildnummer beziehungsweise App-Version.

Die vorhandene Versionshistorie bleibt erhalten. Die IPA-Links sind versionsgebunden, die Source-URL bleibt gleich. Die Veröffentlichung erfolgt zunächst als Entwurf, damit die Quelle erst nach vollständigem Upload angeboten wird. Anschließend werden JSON, IPA-Prüfsumme und Icon über öffentliche HTTPS-Adressen ohne Anmeldung geprüft.

## GitHub Actions

Der iOS-Job erzeugt künftig `altstore-source.json`, `icon.png` und Release-Metadaten zusammen mit der IPA als Build-Artefakt. Die öffentliche Veröffentlichung aus dem privaten Quellcode-Repository erfolgt mit dem obigen lokalen Befehl. Dafür wird kein zusätzliches Token in GitHub Actions benötigt. Nur ein Push allein aktualisiert das öffentliche Download-Repository noch nicht.

Die Einrichtung speichert das Download-Repository in `source-config.json` und setzt die Actions-Variable `PUBLIC_DOWNLOAD_REPOSITORY`. Für einen späteren Wechsel beide Werte anpassen. Ohne Variable wird in CI `<GitHub-Owner>/sidestart-downloads` verwendet.

## Prüfen und lokal erzeugen

```powershell
python -m unittest discover -s scripts -p test_*.py -v
python scripts/make_source.py --ipa downloads/run-123/sidestart-ios-unsigned.ipa --repository code-by-fh/sidestart-downloads --output-dir dist/source
```

Bundle-ID, Version, Buildnummer, Mindest-iOS-Version, Dateigröße und Berechtigungen stammen aus der tatsächlichen IPA. Der Generator unterstützt die minimale ARM64-App ohne App-Erweiterungen oder eingebettete Provisioning-Profile; zusätzliche native Fähigkeiten müssen vor einer späteren Erweiterung geprüft werden.

Schema: [AltStore: Make a Source](https://faq.altstore.io/developers/make-a-source). Vorbild: [NOOP source](https://github.com/ryanbr/noop/blob/main/altstore-source.json).
