# wellness-dashboard
SDLN Wellness Dashboard
Persönliches Wellness- und Trainings-Dashboard im SDLN-Design.  
Live unter: flo-ai-web.github.io/wellness-dashboard
---
Was es ist
Eine automatisch aktualisierte Übersichtsseite die Trainings-, Körper- und Ernährungsdaten aus verschiedenen Quellen zusammenführt und auf einen Blick aufbereitet. Zentrale Frage: Bin ich heute auf Kurs — und wo sollte ich den Fokus legen?
Angezeigt werden:
Gewicht (heute + Wochendurchschnitt + Trend vs. Vorwoche)
Schlaf (letzte Nacht)
Schritte (gestern)
Protein & kcal (gestern)
Wochenverlauf als Tabelle und Gewichtstrend als Chart
Dynamische Empfehlung basierend auf Zielabweichungen
---
Datenquellen
Quelle	Daten	Weg
Huawei Watch	Schlaf, Ruhe-HF, Schritte	→ Huawei Health → intervals.icu
Garmin Waage	Gewicht, Körperfett	→ Garmin Connect → intervals.icu
YAZIO	kcal, Protein, Carbs	→ intervals.icu API (via Sync-Script)
Wahoo Kickr / MyWhoosh	Trainingseinheiten	→ Strava → intervals.icu
intervals.icu ist die zentrale Datendrehscheibe — alle Quellen fließen dort zusammen.
---
Wie es funktioniert
```
07:30  YAZIO-Sync (wellness-sync Repo)
       └ Gestrige Ernährungsdaten (kcal, Protein, Carbs) → intervals.icu API

07:45  fetch_data.py (dieses Repo, GitHub Actions)
       └ Liest alle Wellness + Aktivitätsdaten von intervals.icu API
       └ Berechnet Wochendurchschnitte (heute-Metriken vs. gestern-Metriken getrennt)
       └ Schreibt data/data.json ins Repo

10:00  Backup-Run (für Wochenenden / spätes Aufstehen)

Website  flo-ai-web.github.io/wellness-dashboard
       └ Liest data/data.json (statisches JSON, kein Backend)
       └ Rendert Dashboard im Browser
       └ Installierbar als PWA auf dem Android-Homescreen
```
---
Warum zwei getrennte Wochendurchschnitte?
Schlaf, Gewicht, Ruhe-HF → Morgendaten → KW-Ø inkl. heutigem Tag
Schritte, kcal, Protein → Tagesabschlussdaten → KW-Ø nur bis gestern (heute noch nicht vollständig)
---
Repos
Repo	Funktion
`flo-ai-web/wellness-sync`	YAZIO-Sync + Backfill-Scripts (privat)
`flo-ai-web/wellness-dashboard`	Dashboard-Website + Datenpipeline (dieses Repo)
---
Ziele
Metrik	Ziel
Schritte	10.000 / Tag
Schlaf	7:30h / Nacht
Protein	185g / Tag
kcal	~2.600 / Tag (Trainingstag)
---
SDLN · For the ones who show up.
