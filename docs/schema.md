# Cardle Canonical Automotive Schema — v1

**Status:** Frozen for the playable BMW Cardle prototype  
**Date frozen:** 2026-08-14

---

## 1. Purpose

The canonical layer converts inconsistent Wikipedia-derived data into a stable, normalized representation that can be consumed by the rest of Cardle.

```text
Wikipedia
    ↓
Raw extraction JSON
    ↓
Canonicalization
    ↓
Canonical JSON v1
    ↓
Neo4j / Cardle
```

The **raw JSON preserves extracted source information**. The **canonical JSON is Cardle's internal source of truth**: entities have stable IDs, terminology is normalized, duplicate concepts are reused, relationships are resolved where possible, and values are converted into consistent types.

The canonical layer does **not** attempt to reconstruct facts that are not clearly supported by the source.

---

## 2. Core hierarchy

The primary automotive hierarchy is:

```text
Manufacturer
     │
     ▼
   Model
     │
     ▼
  Variant
     │
     ▼
  Version
     │
     ▼
EngineFamily
```

Example:

```text
BMW
└── 6 Series
    └── E24
        ├── 628CSi
        ├── 630CS
        ├── 635CSi
        ├── M635CSi
        └── M6
```

A **Variant** represents a chassis, generation, or equivalent vehicle-level variant such as `E24`, `E39`, `F10`, `G20`, etc.

A **Version** represents the marketed/configuration-level vehicle designation such as `635CSi`, `325i`, `M5`, `530d xDrive`, etc.

---

## 3. Entities

### Manufacturer

Represents a vehicle manufacturer.

| Property | Type | Meaning |
|---|---|---|
| `id` | string | Stable canonical identifier |
| `name` | string | Canonical manufacturer name |

Example:

```json
{
  "id": "bmw",
  "name": "BMW"
}
```

---

### Model

Represents a named vehicle family within a manufacturer.

| Property | Type | Meaning |
|---|---|---|
| `id` | string | Stable canonical identifier |
| `name` | string | Model name |
| `manufacturer_id` | string | Owning Manufacturer |

Example:

```json
{
  "id": "bmw_6_series",
  "name": "6 Series",
  "manufacturer_id": "bmw"
}
```

`No Model` is currently permitted as a placeholder for vehicles for which the present extraction/modeling rules do not identify a meaningful higher-level Model.

This is an accepted v1 limitation rather than a blocker.

---

### Variant

Represents a chassis, generation, or equivalent vehicle-level variant.

Examples:

```text
E24
E39
F10
G20
G21
G28
```

| Property | Type | Meaning |
|---|---|---|
| `id` | string | Stable canonical identifier |
| `name` | string | Variant/chassis designation |
| `model_id` | string | Parent Model |
| `source_url` | string/null | Wikipedia source page |
| `production_start` | integer/null | First production year |
| `production_end` | integer/null | Final production year; null may mean ongoing/unknown |
| `body_style_ids` | list[string] | Associated body styles |
| `vehicle_class_ids` | list[string] | Associated vehicle classes |
| `engine_position_ids` | list[string] | Engine positions |
| `drivetrain_ids` | list[string] | Available drivetrain types |
| `designer_ids` | list[string] | Associated designers |
| `predecessors` | list[object] | Extracted predecessor relationships |
| `successors` | list[object] | Extracted successor relationships |

A relationship record currently contains:

```json
{
  "name": "BMW E9",
  "url": "https://en.wikipedia.org/wiki/BMW_E9",
  "target_id": "bmw_new_six_coupes_e9"
}
```

`target_id` may remain `null` when the target cannot be resolved confidently.

That is intentional.

---

### Version

Represents a marketed vehicle configuration/designation belonging to a Variant.

| Property | Type | Meaning |
|---|---|---|
| `id` | string | Stable canonical identifier |
| `name` | string | Canonical version designation |
| `variant_id` | string | Parent Variant |
| `power_hp` | integer/null | Representative power in horsepower |
| `engines` | list[object] | Engine usages associated with this Version |

Example:

```json
{
  "id": "bmw_6_series_e24_635csi",
  "name": "635CSi",
  "variant_id": "bmw_6_series_e24",
  "power_hp": 208,
  "engines": [
    {
      "engine_family_id": "m30b34",
      "displacement_l": null
    },
    {
      "engine_family_id": "m30b35",
      "displacement_l": null
    }
  ]
}
```

A Version may use more than one EngineFamily over its lifetime.

Power is deliberately represented as a **single representative value** in v1 rather than modeling every historical power revision.

---

### EngineFamily

Represents a reusable engine family/code.

| Property | Type | Meaning |
|---|---|---|
| `id` | string | Stable normalized engine identifier |
| `name` | string | Canonical engine family/code |
| `cylinder_count` | integer/null | Number of cylinders |
| `arrangement` | string/null | Cylinder arrangement |

Example:

```json
{
  "id": "n62",
  "name": "N62",
  "cylinder_count": 8,
  "arrangement": "V"
}
```

#### Why displacement is not an EngineFamily property

Displacement belongs to the **Version → EngineFamily usage**, not necessarily the EngineFamily itself.

```text
Version ──USES_ENGINE──> EngineFamily
              │
              └── displacement_l
```

Example:

```json
{
  "engine_family_id": "n62",
  "displacement_l": 4.8
}
```

This avoids incorrectly forcing one displacement onto an entire reusable engine family.

---

## 4. Controlled vocabulary entities

The following concepts are represented as reusable canonical entities rather than repeated free text:

| Entity | Example values |
|---|---|
| `BodyStyle` | Sedan, Wagon, Coupe, Convertible, Hatchback, Fastback, Roadster, SUV, Pickup |
| `VehicleClass` | Executive car, Grand tourer, Compact executive car |
| `EnginePosition` | Front, Mid, Rear |
| `Drivetrain` | FWD, RWD, AWD |
| `Designer` | Paul Bracq, Chris Bangle, Joji Nagashima |

Each currently has the simple structure:

```json
{
  "id": "coupe",
  "name": "Coupe"
}
```

This lets many Variants reuse the same canonical entity rather than storing inconsistent strings repeatedly.

---

## 5. Conceptual relationships

The schema can be represented graphically as:

```text
(:Manufacturer)
      │
      │ PRODUCES
      ▼
   (:Model)
      │
      │ HAS_VARIANT
      ▼
  (:Variant)
      │
      ├──────── HAS_VERSION ──────────────► (:Version)
      │                                         │
      │                                         │ USES_ENGINE
      │                                         ▼
      │                                   (:EngineFamily)
      │
      ├──────── HAS_BODY_STYLE ───────────► (:BodyStyle)
      │
      ├──────── HAS_CLASS ────────────────► (:VehicleClass)
      │
      ├──────── HAS_ENGINE_POSITION ──────► (:EnginePosition)
      │
      ├──────── HAS_DRIVETRAIN ───────────► (:Drivetrain)
      │
      ├──────── DESIGNED_BY ──────────────► (:Designer)
      │
      └──────── SUCCEEDED_BY / PRECEDED_BY ► (:Variant)
```

The exact Neo4j relationship names can still be chosen when implementing the importer.

**The semantics above are what are frozen**, not necessarily the spelling of every Cypher relationship type.

---

## 6. Stable ID policy

Every entity receives a deterministic canonical ID.

Examples:

```text
BMW
→ bmw

6 Series
→ bmw_6_series

E24
→ bmw_6_series_e24

M6
→ bmw_6_series_e24_m6

Paul Bracq
→ paul_bracq
```

Vehicle IDs include their hierarchy so that identical names in different contexts do not collide.

Conceptually:

```text
Manufacturer:
    manufacturer

Model:
    manufacturer + model

Variant:
    manufacturer + model + variant

Version:
    manufacturer + model + variant + version
```

IDs are normalized using slugification and Unicode-aware transliteration.

### v1 freeze rule

From this point onward, existing ID-generation behavior should not be changed casually.

Once Neo4j starts using these IDs, changing them becomes a data migration rather than a simple parser cleanup.

---

## 7. Canonicalization rules

Canonicalization follows several general principles:

- **Normalize structure, not history.** The canonicalizer converts extracted values into a consistent schema; it does not attempt to become an automotive-history inference engine.
- **Reuse entities.** Identical manufacturers, models, engines, body styles, designers, etc. should resolve to the same canonical entity.
- **Never invent missing facts.** Unknown or ambiguous information remains `null`, `[]`, or unresolved.
- **Prefer conservative relationships.** A predecessor/successor is resolved only when a target can be identified confidently.
- **Preserve meaningful distinctions.** Market qualifiers such as `(US)` or `(EU)` are not blindly removed.
- **Normalize obvious presentation noise.** Wikipedia footnote markers and similar annotations may be removed from canonical names.
- **Allow multiple values where reality requires them.** Variants may have multiple body styles, drivetrains, designers, classes, predecessors, successors, etc.
- **Allow multiple engines per Version.** A marketed Version can use several engine families during its production life.
- **Missing source data is valid canonical data.** An empty field is preferable to a fabricated one.

---

## 8. Variant ↔ Version policy

Wikipedia frequently provides one version/engine table for several closely related chassis variants.

v1 deliberately does **not** attempt to reconstruct exact body-style-specific availability when Wikipedia does not explicitly provide it.

For example:

```text
G20 = sedan
G21 = wagon
```

may share generic Version records extracted from the same Wikipedia table.

Explicit BMW long-wheelbase distinctions are handled where the source makes them obvious, such as:

```text
318i / 320Li
320i / 325Li
320d / 320Ld
```

The LWB chassis can receive the explicit `Li`/`Ld` designation, while ambiguous generic availability is allowed to remain shared.

This is an intentional v1 simplification.

---

## 9. Source and provenance policy

Wikipedia is currently the primary extraction source.

The raw dataset preserves source-oriented information, while canonical Variant entities retain:

```text
source_url
```

for traceability.

Canonicalization does not overwrite the raw data. Therefore the whole canonical dataset can be regenerated later if the schema changes.

```text
Wikipedia
    ↓
raw JSON          ← preserved
    ↓
canonical JSON    ← regeneratable
```

This distinction is important:

> **Raw data is evidence; canonical data is Cardle's interpretation of that evidence.**

---

## 10. Validation policy

Before producing the final canonical dataset, the pipeline checks structural integrity.

Important invariants include:

```text
IDs must be unique.

Every Model must reference an existing Manufacturer.

Every Variant must reference an existing Model.

Every Version must reference an existing Variant.

Every engine usage must reference an existing EngineFamily.

Vocabulary references must point to existing canonical entities.

Resolved predecessor/successor target IDs must point to existing Variants.

Duplicate canonical entities with conflicting data are rejected.
```

The pipeline should fail on contradictory duplicate canonical entities rather than silently merging them.

---

## 11. Explicit v1 limitations

These are **known limitations, not unfinished Day-1 tasks**.

| Limitation | v1 decision |
|---|---|
| Some vehicles appear under `No Model` | Accepted |
| Facelifts are not consistently modeled as separate Variants | Deferred |
| Some Wikipedia fields are missing/ambiguous | Leave null/empty |
| Exact Version availability by body style is sometimes unknown | Share page-level data conservatively |
| Some predecessor/successor targets remain unresolved | Keep `target_id: null` |
| Version production periods are not modeled canonically | Deferred |
| Detailed historical power changes are not modeled | One representative power value |
| Electric motor architecture is not modeled like combustion EngineFamily | Deferred |
| Toyota/Audi-style multi-generation pages are not generalized yet | Future scraper work |
| Prose-only extraction using LLMs | Future ingestion extension |
| RDF/SHACL representation | Future semantic extension |

None of these prevents the BMW Cardle prototype from being built.

---

## 12. What is frozen in v1

From this point forward, the following conceptual schema is considered stable:

```text
Manufacturer
Model
Variant
Version
EngineFamily
BodyStyle
VehicleClass
EnginePosition
Drivetrain
Designer
```

with the primary hierarchy:

```text
Manufacturer
   ↓
Model
   ↓
Variant
   ↓
Version
   ↓
EngineFamily
```

and Variant-level descriptive relationships for:

```text
BodyStyle
VehicleClass
EnginePosition
Drivetrain
Designer
Predecessor
Successor
```

New information can be added later, but **existing meanings should not be changed unless a genuine structural problem is discovered**.

> **Canonical Schema v1 is now frozen for the playable BMW Cardle prototype.**

The next development step should consume this schema rather than continue redesigning it:

```text
Canonical JSON v1
       ↓
     Neo4j
       ↓
     Cardle
```

---

## 13. Future extensions

The following are intentionally outside the v1 freeze and can be added later without invalidating the current schema:

- More manufacturers and cross-brand generalization
- Multi-generation model-page extraction
- Lightweight LLM-assisted prose extraction
- More detailed version-production histories
- More detailed EV/motor modeling
- Facelift-specific modeling
- RDF export
- SHACL validation
- External knowledge graph linking
- SPARQL support
- Additional provenance metadata

These are extensions to the system, not prerequisites for the playable BMW Cardle prototype.