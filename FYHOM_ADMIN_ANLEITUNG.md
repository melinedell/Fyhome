# FYHOM – Website selbst bearbeiten

## 1. Immobilien ergänzen oder ändern
Nach Veröffentlichung: https://starlit-starburst-dd7d19.netlify.app/admin/
Mit dem berechtigten GitHub-Konto anmelden (über den bestehenden Cloudflare-OAuth-Dienst).
**Immobilien → Immobilienübersicht** öffnen, ein Objekt hinzufügen und die Felder ausfüllen. Die Typen umfassen Haus/Villa, Wohnung, Reihenhaus, Neubau, Ladenlokal (retail), Büro/Praxis (office), Gewerbeobjekt (commercial) und Lager/Industrie (warehouse). Bilder über die Bildfelder hochladen. Status „available“ sichtbar, „sold“ verkauft, „hidden“ ausblenden; „reserved“ bleibt derzeit außerhalb der öffentlichen Trefferliste. Mit **Veröffentlichen/Speichern** übertragen. Änderungen werden auf der `main`-Branch gespeichert und lösen einen Netlify-Build aus.

## 2. Texte auf der Website ändern
**Website-Texte → Texte in allen Sprachen bearbeiten** aufrufen. Dort lassen sich die Hauptüberschrift, die einleitenden Texte der Immobilienübersicht, Über uns, Kontakt und der FYHOM-Service in Deutsch, Spanisch, Englisch, Französisch und Niederländisch ändern. Änderungen speichern/veröffentlichen und einige Augenblicke auf Netlify warten.

## 3. Startseitenbilder ersetzen
Im Bereich Website-Texte gibt es Bildfelder für Hauptbild, Über-uns-Bild und Immobilienbewertungs-Bild. Neue passende Bilder hochladen und speichern. Die Bilder dienen als Darstellung und dürfen nur mit entsprechenden Nutzungsrechten hochgeladen werden.

## 4. Was nur im Code geändert werden kann
Navigation, komplette Seitenstruktur, Farben, Animationen, Layout und neue Funktionen lassen sich im aktuellen Decap CMS noch **nicht** per Drag-and-drop bearbeiten. Dafür GitHub (Repository melinedell/Fyhome) oder einen Webentwickler nutzen. Vor Änderungen am Design am besten einen Branch und eine Netlify-Deploy-Preview erstellen.

## 5. Sicherheits- und Veröffentlichungshinweise
Der neue Entwurf liegt auf der Branch `fyhom-final-oktober-2026`. Das Admin-CMS schreibt auf `main`, also zunächst die geprüfte Website veröffentlichen/mergen, bevor darüber die neuen Felder bearbeitet werden. 
Bitte echten Formularversand mit einer Testanfrage prüfen. 
Impressum/Datenschutz an Netlify-Hosting, externe Bilder/Schriften, Cookies/Local Storage und die tatsächlichen Aufbewahrungszeiten anpassen; vor dem öffentlichen Launch rechtlich prüfen.
Die bisherige Testimmobilie ist ausgeblendet. Es erscheinen erst nach Anlage echte verfügbare Objekte.
