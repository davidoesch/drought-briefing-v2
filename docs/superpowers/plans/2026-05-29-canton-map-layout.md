# Canton Map Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the canton view so the map (with a current/forecast tab switcher) is on the right and the warnlevel badge + overview text is on the left.

**Architecture:** Single-file change confined to the `view_tab == "canton"` block in `app.py`. Replace the existing two-side-by-side-maps layout with a two-column hero: left column holds the warnlevel badge and the `allgemeine-lage` section; right column holds `st.tabs()` built from `doc.lead_maps`. Remaining sections render full-width below as before.

**Tech Stack:** Streamlit `st.columns`, `st.tabs`, existing `build_canton_map` / `st.components.v1.html`. No new dependencies.

---

### Task 1: Restructure the canton view layout in `app.py`

**Files:**
- Modify: `app.py:121-169`

This task replaces the entire canton view block. No new files. No unit tests (pure Streamlit rendering — no testable logic).

- [ ] **Step 1: Open `app.py` and locate the canton view block**

  It starts at line 121 (`if view_tab == "canton":`) and ends at line 169 (after the sections loop). You are replacing everything inside this `if` block.

- [ ] **Step 2: Replace the canton view block**

  Replace from `if view_tab == "canton":` down to (but not including) `# ── Tab 2: Regionale Lage` with the following:

  ```python
  # ── Tab 1: Allgemeine Lage (Kanton) ────────────────────────────────────────
  if view_tab == "canton":
      st.title(f"{t('export_doc_title', lang)} {canton_label}")

      # ── Two-column hero: overview text left, map tabs right ────────────────
      left_col, right_col = st.columns([1, 1])

      with left_col:
          bg, text_colour = _warnstufe_palette(canton.max_warnlevel)
          st.markdown(
              f"""<div style="background:{bg};border-radius:8px;padding:18px;color:{text_colour};">
              <div style="font-size:11px;opacity:.85;">{t("current_warnlevel", lang)}</div>
              <div style="font-size:28px;font-weight:700;">{doc.lead_headline}</div>
              <div style="font-size:12px;opacity:.85;">{doc.lead_meta}</div>
              </div>""",
              unsafe_allow_html=True,
          )
          allg_sec = next((s for s in rs.sections if s.id == "allgemeine-lage"), None)
          if allg_sec:
              title = allg_sec.title.get(lang, allg_sec.title.get("de", allg_sec.id))
              st.markdown(f"## {title}")
              st.markdown(doc.sections["allgemeine-lage"])

      with right_col:
          tab_labels = [
              (map_spec.title_de if lang == "de" else map_spec.title_fr)
              for map_spec in doc.lead_maps
          ]
          tabs = st.tabs(tab_labels)
          for tab, map_spec in zip(tabs, doc.lead_maps):
              with tab:
                  m = build_canton_map(canton, map_spec)
                  st.components.v1.html(m._repr_html_(), height=300)

      # ── CDI legend (full width) ────────────────────────────────────────────
      labels = DROUGHT_LEGEND[lang]
      items_html = "".join(
          f"""<span style="display:inline-flex;align-items:center;margin-right:18px;white-space:nowrap;">
              <span style="display:inline-block;width:14px;height:14px;background:{colour};
                           border-radius:2px;margin-right:6px;flex-shrink:0;"></span>
              <span style="font-size:13px;">{label}</span>
          </span>"""
          for colour, label in zip(DROUGHT_COLOURS, labels)
      )
      st.markdown(
          f'<div style="display:flex;flex-wrap:wrap;align-items:center;'
          f'margin-top: 10px; padding: 0; gap: 8px;">'
          f'{items_html}</div>',
          unsafe_allow_html=True,
      )

      st.divider()

      for sec in rs.sections:
          if sec.id in ("regionen", "allgemeine-lage"):
              continue

          title = sec.title.get(lang, sec.title.get("de", sec.id))
          st.markdown(f"## {title}")
          st.markdown(doc.sections[sec.id])
          st.write("")
  ```

  Key differences from the old block:
  - The `st.divider()` between the badge and the maps is **removed** (those elements are now in columns).
  - `allgemeine-lage` is rendered inside `left_col`, not in the sections loop.
  - The sections loop now skips `"allgemeine-lage"` in addition to `"regionen"`.
  - The two-column map loop (`map_cols = st.columns(2)` + `for col, map_spec`) is replaced by `st.tabs()` inside `right_col`.

- [ ] **Step 3: Commit**

  ```bash
  git add app.py
  git commit -m "feat: two-column canton view with map tab switcher"
  ```

---

### Task 2: Manual verification

**Files:** none (read-only verification)

- [ ] **Step 1: Start the app**

  ```bash
  make up
  ```

  Open http://localhost:8501 in your browser.

- [ ] **Step 2: Verify the canton view layout**

  With any canton selected and "Allgemeine Lage" (canton) tab active:

  - [ ] The page title spans full width.
  - [ ] Below the title, two equal columns appear side-by-side.
  - [ ] **Left column** shows the coloured warnlevel badge, then a `## Allgemeine Lage` heading and its text.
  - [ ] **Right column** shows two tabs: the first tab label is "Aktueller CDI" (de) or "CDI actuel" (fr); the second is "CDI-Prognose Woche 2" (de) or "Prévision CDI semaine 2" (fr).
  - [ ] Clicking each tab renders a folium map (the map may take a moment to load due to WMS requests).
  - [ ] The CDI colour legend appears below the two columns, full-width.
  - [ ] A divider separates the legend from the remaining sections.
  - [ ] `## Handlungsoptionen` and `## Datenquellen` sections appear full-width below the divider.
  - [ ] The `## Allgemeine Lage` section does **not** appear a second time in the lower sections.

- [ ] **Step 3: Verify language switching**

  Switch the language selector in the sidebar to "Français":

  - [ ] Tab labels update to "CDI actuel" and "Prévision CDI semaine 2".
  - [ ] The `## Allgemeine Lage` heading and text render in French.

- [ ] **Step 4: Verify the Regions view is unaffected**

  Click the "Regionale Lage" navigation option in the sidebar — the regions table should appear exactly as before.

- [ ] **Step 5: Stop the app**

  ```bash
  make down
  ```
