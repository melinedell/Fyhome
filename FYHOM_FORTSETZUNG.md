# FYHOM – Projekt fortsetzen (Stand 22. Oktober 2026)

## Einstieg in einem neuen Chat
Die Benutzerin kann sagen: **„Wir machen mit der FYHOM-Website aus GitHub melinedell/Fyhome weiter. Lies zuerst FYHOM_FORTSETZUNG.md.“** Die wichtigsten Dateien liegen in diesem Repository auf `main`.

- Cloudflare Pages: https://fyhome-e0f.pages.dev/
- FYHOM-Admin: https://fyhome-e0f.pages.dev/admin/
- Repository: https://github.com/melinedell/Fyhome
- Öffentliche Domain `fyhom.es` zeigt möglicherweise noch auf das alte System – DNS-/Mailumzug ist nicht abgeschlossen. Bestehende IONOS-/Gmail-E-Mail-Einträge nicht verändern.
- E-Mail-Formularfunktion `functions/api/contact.js` benötigt noch Resend-Einrichtung (eigene Mail-Domain, Secret, Testversand). Bis dahin nur explizit manuelles Mailto als Fallback, keine Erfolgsmeldung ohne Zustellung.

## Immobilien
- `content/properties.json` enthält aktuell **40 importierte echte Objekte (36 available, 4 sold)** plus eine **hidden Testimmobilie**, sofern die Benutzerin keine späteren Änderungen im Admin vorgenommen hat.
- Die Startseite zeigt nur verfügbare Angebote. In `#properties` erscheinen die verkauften am Ende, mit einem dunklen champagnerfarbenen „Verkauft“-Schild und ohne Kaufanfrage.
- Immobilienart, Ort, Preise und Fläche müssen bei einzelnen importierten Angeboten noch kontrolliert werden. Bei fehlendem Preis wird „Preis auf Anfrage“ angezeigt.
- Jede Immobilie verfügt über individuelle Titel und Beschreibungstexte in **DE/ES/EN/FR/NL/RU**. Alle sechs Sprachfelder wurden auf Vollständigkeit geprüft. Keine automatische Wort-für-Wort-Ersetzung verwenden: `solárium` meint im Immobilienkontext oft eine **Sonnen-/Dachterrasse**, niemals ein deutsches Sonnenstudio. Für die Doppelhaushälfte `20597` wurde `title_de` bereits auf „Moderne Doppelhaushälfte mit privatem Pool und Sonnenterrasse in Els Poblets“ korrigiert, und entsprechend in den übrigen Sprachen.
- Die wichtigsten Anzeigeelemente sind in `fyhom-app.js` (`propertyTitle`, `openProperty`, `renderCards`). Bearbeitbare Felder werden in `admin/config.yml` definiert.
- **Wichtiges Importproblem:** Die ursprüngliche Funktion `photos(soup)` in `scripts/import_old_fyhom.py` hat irrtümlich auch Fotos aus verlinkten „ähnlichen Immobilien“ und Grundriss-Anlagen gesammelt; einzelne Immobilien hatten deshalb fremde Fotos.

## Fotos – geprüfte Reparatur
- **ID 20678**, „Terreno urbano en la Marina Alta con vistas despejadas“, war mit 12 Fotos einschließlich fremder Wohnanlagen und Balkonfotos gespeichert. Die ursprüngliche WordPress-Galerie zeigt genau drei Grundstücksfotos. Am 22.10.2026 wurden nur die geprüften `02.jpg`, `03.jpg`, `04.jpg` als Hauptbild/Galerie belassen; neun falsche Zuordnungen wurden aus `content/properties.json` entfernt (Dateien selbst aus Sicherheitsgründen nicht gelöscht).
- Ein GitHub-Actions-Workflow **`FYHOM - Verify and Repair Every Property Photo Gallery`** liegt in `.github/workflows/fyhom-rebuild-verified-galleries.yml`, zugehöriges Skript `scripts/rebuild_verified_fyhom_galleries.py`. Er durchläuft alle 40 Immobilien, prüft die tatsächliche WordPress-Referenznummer und verwendet **ausschließlich Bilder aus `.lightbox-gallery #lightbox-slider-js img`** statt der gesamten alten Seite. Er lädt lokale geprüfte Bilder nach `images/properties/verified/<ID>/` und setzt Hauptbild/Galerie um. Status, Preise, Titel und Übersetzungen sollen dabei unverändert bleiben. 
- **Ergebnis/Abweichungen unbedingt prüfen**: nach Abschluss `content/verified-property-photos-review.json` lesen (Anzahl geprüfter/fehlgeschlagener Galerien, pro Objekt).
- Quell-Diagnose `content/source-gallery-diagnostic.json`: WordPress-`.lightbox-gallery` enthält für 20678 genau 3, für 20597 9 und für 21191 4 Bilder. In Seitenabschnitten darunter tauchen fremde Immobilienfotos auf.

## Rechtliches
- Eigenständige Website-Texte unter `#legal`, `#privacy`, `#cookies` und bearbeitbar im Admin (Rechtstexte in sechs Sprachen), Dateien `content/legal/<language>.json`.
- Ausführliche Entwürfe sind **noch nicht juristisch freigegeben**. Zu prüfen: Handelsregisterdaten und RAICV-Nummer, Versicherungsnachweise, tatsächliche Drittanbieter, Log-/E-Mail-Aufbewahrungsfristen, Cookie- und externe Ressourcen-Konfiguration sowie Datenschutzverträge.
- Der neue Webauftritt enthält keine Links zu den alten Rechtstexten auf der WordPress-Seite; das alte System ist von den neuen CMS-Rechtstexten unabhängig.

## Aktuelle Prioritäten
1. Bericht des Galerie-Reparatur-Workflows lesen, etwaige Fehler/fehlende Angebote manuell behandeln und die Bilder aller 40 Objekte stichprobenartig mit dem bisherigen Original vergleichen.
2. Die fachgerechte Übersetzung und die sechs Sprachen (Titel und Beschreibungen) im Frontend überprüfen; kein falsches „Solarium“ im Deutschen, keine spanischen Einträge bei einer anderen ausgewählten Sprache.
3. E-Mail-Versand mit Resend erst nach DNS-Zugang und ohne Änderung bestehender IONOS-E-Mail-Einträge abschließen.
4. Fehlende Grundstücks-/Flächen-/Preisangaben auf Grundlage bestätigter Objektinformationen ergänzen; keine Fantasiewerte.

Dieser Status ist eine Dokumentation, kein automatischer Beleg über eine abgeschlossene Galerie-Action. Datum und neue Änderungen bitte gegen GitHub prüfen.
