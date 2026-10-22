# FYHOM – Website verwalten (Cloudflare Pages)

## Website und Login
- Website: https://fyhome-e0f.pages.dev/
- Adminbereich: https://fyhome-e0f.pages.dev/admin/
- Hosting: Cloudflare Pages, automatisches Deployment aus GitHub `melinedell/Fyhome`, Branch `main`.
- Der Admin verwendet GitHub-OAuth über die Cloudflare-Pages-Funktionen `/api/auth` und `/api/callback`.
- GitHub-OAuth-Werte `GITHUB_CLIENT_ID` und `GITHUB_CLIENT_SECRET` gehören **nur** in die Cloudflare-Secrets, nie in den Repository-Code.

## Immobilien
Unter **Immobilien → Immobilienübersicht** können Angebote verändert werden.
- `available`: online und regulär zu verkaufen.
- `sold`: online und deutlich als verkauft gekennzeichnet; Anfrage nach ähnlichen Immobilien.
- `hidden`: nicht öffentlich sichtbar.
- `reserved`: derzeit nicht in den öffentlich angezeigten Ergebnissen.
- Hauptbild und weitere Bilder sind über die Bildfelder bearbeitbar.
- Der einmalige Import aus dem alten System liegt unter `content/properties.json`; Bilder liegen lokal unter `images/properties/imported/`. Die neue Website lädt diese Fotos **nicht** von der alten Website.
- Stand 22. Oktober 2026: 36 `available`, 4 `sold`, 1 `hidden` (Testimmobilie). Alle 40 importierten Objekte werden öffentlich angezeigt. Zwei verfügbaren Angeboten fehlt derzeit ein bestätigter Preis (dort erscheint „Preis auf Anfrage“). Bei neun verfügbaren Angeboten ist keine verifizierte Wohn-/Nutzfläche hinterlegt. Diese Werte müssen noch überprüft und ergänzt werden.
- Einige importierte Flächen, Preise, Städte, Objektarten und Bildzuordnungen brauchen noch eine abschließende Prüfung. Grundrisse wurden bei einer automatischen Sortierung soweit erkennbar nach hinten geschoben. Bilder im Admin vor Freischaltung stichprobenartig prüfen.
- Das Veröffentlichen im Admin schreibt nach GitHub und löst den Cloudflare-Deploy automatisch aus.

## Website-Texte, Design, Team
- **Website-Texte**: Seitentexte, Titelbilder, vorbereitete Farbvarianten und Sichtbarkeit einzelner Abschnitte bearbeiten.
- **Teammitglieder**: Name, Foto, Sichtbarkeit, Berufsbezeichnung und Biografie in **DE, ES, EN, FR, NL, RU** bearbeiten.
- **Zusätzliche Leistungen & Ideen**: weitere Servicekarten anlegen, bearbeiten oder verstecken.
- **Stand 22.10.2026: Alle 40 veröffentlichten Immobilien besitzen eigenständige Titel und Beschreibungen in DE, ES, EN, FR, NL und RU.** Die Texte in EN/FR/NL/RU sind redaktionell verdichtete fremdsprachige Beschreibungen auf Basis der bisherigen Objektdaten; sie müssen bei Änderungen des Objekts ebenfalls aktualisiert werden. Projektnamen (z. B. Blue Gardens Jávea) bleiben als Eigennamen erhalten.
- **Neue Immobilien:** Im Admin für jeden der sechs Sprachcodes sowohl `title_...` als auch `description_...` ausfüllen, bevor der Status `available` oder `sold` gewählt wird. Die automatische Übersetzung später ergänzter Angebote ist noch nicht eingerichtet. Fehlende Felder erzeugen auf der Website einen sprachlich passenden Hinweis statt fälschlich deutschen oder spanischen Text anzuzeigen.
- Änderungen an Seitenstruktur und freiem Layout erfordern weiterhin Codebearbeitung.

## Rechtstexte selbst bearbeiten
In **Rechtstexte · Impressum / AGB / Datenschutz / Cookies** gibt es eigenständige Dateien für Deutsch, Spanisch, Englisch, Französisch, Niederländisch und Russisch. Für jede Sprache stehen drei bearbeitbare Listen zur Verfügung:
1. Impressum und allgemeine Website-Nutzungsbedingungen
2. Datenschutzerklärung
3. Cookie-Richtlinie

Texte über **Publish** im Admin speichern; sie werden über `content/legal/<sprache>.json` auf der entsprechenden Website-Seite ausgegeben. Das öffentliche Menü enthält keine Links zur alten FYHOM-WordPress-Seite. Wichtig: Die Dokumente sind **ausführliche Entwürfe**, keine rechtsanwaltliche Endprüfung. Prüfen: RAICV-Registrierungsnummer und Versicherungsnachweise, konkrete Auftragsverarbeitungsvereinbarungen, Drittländer, technische Log- und E-Mail-Aufbewahrungsfristen, Cookie-/Tracking-Bestand sowie vollständige Unternehmensdaten.

## Kontaktformulare: wichtige offene Einrichtung
Die vier Formulare (Suchauftrag, Verkaufen, Bewertung, Kontakt) senden POST an die eigene Cloudflare-Pages-Funktion `/api/contact`. **Automatischer Versand ist erst aktiv, wenn der E-Mail-Dienst eingerichtet und ein echter Eingangstest erfolgreich war.**

Für den vorbereiteten Resend-Versand:
1. Bestehende E-Mail-Adresse `info@fyhom.es` **bei IONOS** behalten; Gmail kann weiterhin als Oberfläche für dieses Postfach verwendet werden.
2. Bei Resend eine **eigene Versand-Subdomain**, beispielsweise `mailer.fyhom.es`, verifizieren. Die dafür angegebenen DNS-Einträge genau übernehmen, aber **keine bestehenden IONOS-MX-Records, SPF-/DKIM-Records für `fyhom.es` löschen oder überschreiben**. Nameserver-Zustand vor der Umstellung prüfen.
3. In Cloudflare Pages → `fyhome` → Settings → Variables and Secrets (Production) hinterlegen:
   - `RESEND_API_KEY` als verschlüsseltes Secret
   - `FYHOM_FROM_EMAIL` als Text, z. B. `FYHOM Website <anfragen@mailer.fyhom.es>` (nur mit verifizierter Subdomain)
4. Cloudflare neu deployen, **eine echte Testanfrage** mit eigener E-Mail-Adresse schicken und Eingang bei `info@fyhom.es` prüfen.
5. Solange die Versand-Variablen fehlen oder der Dienst eine Anfrage ablehnt, zeigt das Formular ausdrücklich an, dass es **nicht gesendet** wurde und bietet stattdessen eine vorausgefüllte `mailto:`-Nachricht an. Diese muss ein Besucher selbst absenden.

**Keine IONOS-, Gmail-, GitHub- oder Resend-Passwörter in Chats oder den Repository-Code kopieren.**

## Rechtliches und Domain
- Eigenständige Seiten unter `#legal`, `#privacy` und `#cookies` – keine Links zur bisherigen Website.
- Rechtliche Inhalte vor endgültiger Nutzung von Unternehmensunterlagen und einem fachkundigen Prüfer abgleichen (insbesondere spanisches Recht, DSGVO, Auftragsverarbeitung, Drittinhalte, Löschfristen, Cookies).
- Wenn `fyhom.es` zu Cloudflare umgestellt wird, müssen die bestehenden IONOS-E-Mail-DNS-Einträge unverändert korrekt bestehen bleiben. Vor Änderungen an Nameservern/MX vorher prüfen.
- Solange die eigene Domain nicht auf Cloudflare Pages zeigt, die `pages.dev`-Adresse verwenden.
