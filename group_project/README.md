# Galičica capstone group project

## From evidence to a management briefing

The capstone reuses outputs from the six practical notebooks. It is **not** a new large coding exercise.

The common question is:

> **What does the available geospatial evidence tell us about wildfire history, the August 2024 event, recovery, fire-conducive conditions, and future management priorities in Galičica?**

The class works in five teams. With about 30 participants, this gives roughly 5–7 people per team.

## Shared rules

Each team should:

- reuse results already produced in the practicals;
- check that every claim is supported by a map, graph, table or clearly identified external source;
- separate **observation** from **interpretation**;
- include uncertainty and limitations;
- avoid upgrading screening indicators into stronger claims than they support;
- finish with a management-relevant implication.

Do **not** spend the group session rebuilding the notebooks from scratch.

## Team A — Fire history and event context

Primary source: `notebooks/02_historical_fires.ipynb`

Question:

> **How unusual was the 2024 Galičica event in the recent fire history of the area?**

Suggested evidence:

- EFFIS fire-history map;
- annual number of fires and/or burned area;
- the 2024 event footprint;
- the annual NBR trajectory if useful.

Focus on:

- temporal pattern of recorded fires;
- size/context of the 2024 event;
- what EFFIS can and cannot tell us.

## Team B — Burned area and severity

Primary source: `notebooks/03_burned_area_severity.ipynb`

Question:

> **Where did the 2024 fire produce the strongest remotely sensed surface change?**

Suggested evidence:

- pre/post Sentinel-2 imagery;
- dNBR map;
- burn-severity class areas;
- comparison with EFFIS.

Focus on:

- spatial pattern;
- strong vs moderate change;
- uncertainty in dNBR thresholds;
- implications for field inspection or restoration prioritization.

## Team C — Post-fire recovery

Primary source: `notebooks/04_recovery.ipynb`

Question:

> **What spectral recovery is visible one year after the fire, and where is recovery slower?**

Suggested evidence:

- impact-zone map;
- NBR recovery trajectory;
- NDVI or NDMI trajectory;
- recovery-fraction table.

Focus on:

- difference between stronger and weaker impact zones;
- whether different indices tell the same story;
- why spectral recovery is not identical to ecological recovery.

## Team D — Fire weather and fuel condition

Primary source: `notebooks/05_fire_weather_fuels.ipynb`

Question:

> **Were the conditions before and during the 2024 fire unusually fire-conducive?**

Suggested evidence:

- 2024 weather vs 1991–2020 climatology;
- fire-start percentile table;
- compound weather-stress flags;
- pre-fire NDMI / land-cover condition summary.

Focus on the distinction:

**fire weather ≠ fuel condition ≠ fuel load ≠ ignition probability ≠ risk**

## Team E — Landscape susceptibility and management priorities

Primary source: `notebooks/06_fire_susceptibility.ipynb`

Question:

> **Which parts of the landscape appear relatively more susceptible under the transparent weighted-overlay assumptions, and how robust is that pattern?**

Suggested evidence:

- factor layers;
- susceptibility map;
- AOI vs EFFIS plausibility check;
- weight-sensitivity result.

Focus on:

- robust hotspots rather than one exact score;
- sensitivity to assumptions;
- what the map can support for management;
- why this is not a probability-of-fire map.

## Required team output

Prepare a **very short management briefing** with:

1. **one main map**;
2. **one graph or table** where useful;
3. **three defensible findings**;
4. **one important limitation**;
5. **one management implication**;
6. **one additional dataset or field observation** that would most improve confidence.

Use the template in `group_project/presentation_template.md`.

## Presentation format

Recommended default:

- **4 minutes** presentation;
- **2 minutes** questions;
- one speaker is enough, but the whole group should be able to defend the conclusions.

If the course schedule changes, the trainers can shorten or extend this without changing the task.

## What counts as a strong finding?

Strong:

> “The strongest 2024 dNBR changes are spatially concentrated within the mapped EFFIS fire footprint, but the class thresholds remain context-dependent.”

Weak:

> “The red area is dangerous.”

Strong:

> “Several weather and antecedent-drying indicators were unusually fire-conducive around the event, but this does not establish ignition probability or cause.”

Weak:

> “The weather caused the fire.”

## Final synthesis discussion

After all five teams present, the class should reconstruct the wildfire evidence chain:

**past fire history → 2024 disturbance → post-fire recovery → weather and vegetation condition → landscape susceptibility → management**

The final class discussion should answer:

- What do we know with relatively high confidence?
- Which conclusions are only screening-level?
- Where do the datasets disagree or leave gaps?
- What should park managers monitor next?
- Which questions require field data or operational fire-management information?
