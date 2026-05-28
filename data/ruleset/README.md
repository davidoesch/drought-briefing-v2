# Ruleset

Regelwerk für Trockenheitsbulletins pro BAFU-Trockenheitsregion. Jedes Report-Template ist eine YAML-Datei unter `reports/`.

## Aufbau

Eine Report-YAML hat folgende Top-Level-Blöcke:

| Block | Zweck |
|---|---|
| `id`, `title`, `description` | Metadaten |
| `data_sources` | Externe Datenquellen (REST-API, STAC-Collection) mit URL + Feld-Mapping |
| `references` | Externe Dokumente (Terminologie-PDF, Empfehlungs-Webseite) für den Quellennachweis |
| `nomenclature` | Lookup-Tabellen: Indexstufe (1–5) → Textbaustein pro Sprache |
| `trend` | Wiederverwendbare Trend-Logik (Forecast vs. aktuell) |
| `handlungsempfehlungen` | Empfehlungstexte pro BAFU-Gefahrenstufe |
| `lead` | Headline-Block (Warnstufen-Box) direkt unter dem Report-Titel |
| `sections` | Inhaltliche Sektionen des Reports mit Templates und Platzhaltern |

## Datenfluss

```
                 BAFU-Warnkarte API (warnlevel, info_de, valid_from)
                          │
                          ▼
                       lead.warnstufe ────────────────► Headline-Box im Report
                          │
                          ▼
             handlungsempfehlungen[warnlevel] ─────────► Section "Handlungsoptionen"

  BAFU-Trockenheitsdaten (STAC-Collection)
   ├── weekly_current_regions ──┐
   ├── weekly_forecast_regions ─┤
   ├── weekly_current_stations ─┤───► Platzhalter in den Sections (resolved via Region-ID)
   ├── daily_reference_stations ┤
   ├── regions (Stammdaten) ────┤
   └── stations (Stammdaten) ───┘
```

## Nomenklatur

Folgt der BAFU/MeteoSchweiz-Empfehlung (siehe `references.terminologie_bafu`). Wichtigste Regel:

> Die Begriffe „Trockenheit" und „trocken" sind dem **Lead** und der **CDI-Beschreibung** vorbehalten. Für die Einflussfaktoren (Niederschlag, Gewässer/Grundwasser, Bodenfeuchte) werden **Defizit-Begriffe** verwendet.

Pro Indikator (`cdi`, `niederschlag`, `hydro`, `bodenfeuchte`) gibt es einen Lookup mit 5 Stufen × 3 Sprachen, jeweils in Adjektiv- und/oder Substantivform.

**Stilkonvention:** Bei den Defizit-Substantiven (`niederschlag.noun`, `hydro.noun`, `bodenfeuchte.noun`) ist der unbestimmte Artikel "ein" für Stufen 2–5 eingebaut ("ein leichtes Niederschlagsdefizit"). Stufe 1 nutzt "kein oder geringes …" (kein Artikel nötig). Bei `cdi.noun` ist kein Artikel eingebaut — er ergibt sich aus dem umgebenden Satz.

## Trend-Logik

```yaml
trend.defizit:
  rule: "delta = forecast - current"
  stable_tolerance: 0
  increase / decrease / stable  # reine Infinitive pro Sprache
```

Verwendung im Template:

```
… wird in der kommenden Woche voraussichtlich {{ trend(forecast - current, "defizit").de }}.
```

Da die Trend-Begriffe Infinitive sind (`zunehmen`, `abnehmen`, `unverändert bleiben`), passen alle drei in denselben Satzslot — grammatikalisch korrekt unabhängig vom Vorzeichen.

## Platzhalter-Syntax

| Ausdruck | Beispiel |
|---|---|
| `{{ dataset.column }}` | `{{ weekly_current_regions.precip_sum_1m }}` |
| `{{ resolved.field }}` | `{{ region.name_de }}` (resolved via Join in `placeholders`) |
| `{{ nomenclature.<key>.<form>[<value>].<lang> }}` | `{{ nomenclature.niederschlag.noun[weekly_current_regions.precip_1m_index].de }}` |
| `{{ trend(<expr>, "<key>").<lang> }}` | `{{ trend(forecast - current, "defizit").de }}` |
| `{{ format_date(<iso_date>, "<pattern>") }}` | `{{ format_date(warnkarte.valid_from, 'DD.MM.YYYY') }}` |
| `{{#each <collection>}} … {{ this.x }} {{/each}}` | Iteration über Empfehlungsliste oder Datenquellen |

## Sections

| Section | Inhalt | Datenbasis |
|---|---|---|
| `allgemeine-lage` | Niederschlag → Abfluss → Seen → Bodenfeuchte. Reihenfolge folgt der Trockenheitskaskade Atmosphäre → Hydrosphäre → Pedosphäre. | `weekly_current_regions`, `weekly_forecast_regions`, Stations-Aggregate |
| `handlungsoptionen` | Bullet-Liste der BAFU-Empfehlungen für die aktuelle Warnstufe | `warnkarte.warnlevel` → `handlungsempfehlungen` |
| `datenquellen` | Auto-generierte Liste aus `data_sources` + `references` | YAML selbst |

## Stations-Aggregate (Abfluss, Seen)

Die Platzhalter `abfluss` und `seen` in `allgemeine-lage` sind vom Typ `aggregate`. Sie filtern `weekly_current_stations` nach `label` (Abfluss / Wasserstand) und `unit` (`masl` bei Seen), joinen mit `daily_reference_stations` über `hydro_station_id` und `doy`, und zählen Stationen, deren aktueller Wert strikt unter `threshold1` bzw. `q347` liegt.

**Externe Abhängigkeit:** Das Mapping `hydro_station_id → drought_region_id` ist nicht Teil des BAFU-Datasets — es wird vom Renderer extern bereitgestellt (siehe Filter-Block `region: "{{ aktuelle_region }}"`).

## Handlungsempfehlungen — Fallback

BAFU veröffentlicht nur für Stufen 1, 2 und 4 explizite Empfehlungen. Stufen 3 und 5 fallen über `fallback: 2` bzw. `fallback: 4` auf die jeweils niedrigere Stufe zurück. Der Renderer muss das Fallback selbständig auflösen.

## Einen Report rendern

1. **Eingabe:** `drought_region_id` (z.B. 34 für Berner Mittelland)
2. **API-Call:** `data_sources.warnkarte.url` mit eingesetzter `drought_region_id` → liefert `warnlevel`, `info_de`, `valid_from`
3. **CSV-Lookups:** Neueste Zeile aus `weekly_current_regions` + erste Forecast-Zeile aus `weekly_forecast_regions` für die Region
4. **Joins:** `regions` (Name), `weekly_current_stations` + `daily_reference_stations` (Aggregate, sofern Stations-Mapping vorhanden)
5. **Rendering:** Lead-Box, dann Sektionen in deklarierter Reihenfolge

## Beispiel-Output

`reports/example-region-34.html` ist ein gerenderter Beispiel-Report (Region 34, Stand 28.05.2026). Aggregat-Blöcke sind als Platzhalter markiert, da das Stations-Mapping in diesem Repo nicht vorliegt.

## Offene Punkte

- **Aggregat-Mapping:** Stations-zu-Region-Zuordnung muss vom Renderer geliefert werden — Format und Speicherort noch festzulegen.
- **Renderer-Engine:** Templates mischen Handlebars-Syntax (`{{#each}}`) und Funktionsaufrufe (`format_date()`, `trend()`). Konkrete Engine-Wahl (z.B. Nunjucks / Liquid + Custom Filter) steht noch aus.
- **Fehlerfall API:** Was passiert, wenn die BAFU-Warnkarte nicht erreichbar ist? Aktuell nicht spezifiziert (Annahme: Fail fast).
- **FR/IT Vollständigkeit:** Sections-Templates sind aktuell nur in `de` ausformuliert. Der Lead und die Nomenklatur sind dreisprachig vorbereitet.
