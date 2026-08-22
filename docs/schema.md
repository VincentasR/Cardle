# Cardle Canonical Automotive Schema — v1.1

**Status:** Current schema for the playable BMW Cardle prototype  
**v1 frozen:** 2026-08-14  
**v1.1 engine hierarchy refinement:** 2026-08-22

---

## 1. Purpose

The canonical layer converts inconsistent Wikipedia-derived data into a stable, normalized representation consumed by the rest of Cardle.

```text
Wikipedia
    ↓
Raw extraction JSON
    ↓
Canonicalization
    ↓
Canonical JSON v1.1
    ↓
Neo4j / Cardle
```

The **raw JSON preserves extracted source information**. The **canonical JSON is Cardle's internal source of truth**: entities have stable IDs, terminology is normalized, duplicate concepts are reused, relationships are resolved where possible, and values are converted into consistent types.

The canonical layer does **not** attempt to reconstruct facts that are not clearly supported by the source.

v1.1 keeps the original vehicle hierarchy intact and refines engine modeling so that broad engine series, comparison-friendly engine families, and exact engine codes are no longer conflated.

---

## 2. Core hierarchy

The primary vehicle hierarchy is:

```text
Manufacturer
     ↓
   Model
     ↓
  Variant
     ↓
  Version
```

The reusable engine hierarchy is:

```text
Manufacturer
     ↓
EngineSeries
     ↓
EngineFamily
     ↓
   Engine
```

A Version references the most precise engine identity supported by the source.

```text
Exact engine known:

Version ──USES_ENGINE──► Engine
                          ▲
                          │ HAS_ENGINE
                    EngineFamily
                          ▲
                          │ HAS_ENGINE_FAMILY
                    EngineSeries
```

```text
Only family known:

Version ──USES_ENGINE_FAMILY──► EngineFamily
```

Example:

```text
BMW
└── B
    └── B48
        ├── B48B20M0
        └── B48B20O1
```

If the source only states `B48`, Cardle stores `B` and `B48` but does **not** invent a specific Engine.

A **Variant** represents a chassis/generation such as `E24`, `E39`, `F10`, or `G20`.

A **Version** represents a marketed/configuration-level designation such as `635CSi`, `325i`, `M5`, or `530d xDrive`.

---

## 3. Entities

### Manufacturer

| Property | Type | Meaning |
|---|---|---|
| `id` | string | Stable canonical identifier |
| `name` | string | Canonical manufacturer name |

```json
{
  "id": "bmw",
  "name": "BMW"
}
```

### Model

| Property | Type | Meaning |
|---|---|---|
| `id` | string | Stable canonical identifier |
| `name` | string | Model name |
| `manufacturer_id` | string | Owning Manufacturer |

```json
{
  "id": "bmw_6_series",
  "name": "6 Series",
  "manufacturer_id": "bmw"
}
```

`No Model` remains permitted as a canonical placeholder when no meaningful higher-level Model is identified.

### Variant

| Property | Type | Meaning |
|---|---|---|
| `id` | string | Stable canonical identifier |
| `name` | string | Variant/chassis designation |
| `model_id` | string | Parent Model |
| `source_url` | string/null | Wikipedia source page |
| `production_start` | integer/null | First production year |
| `production_end` | integer/null | Final production year |
| `body_style_ids` | list[string] | Associated body styles |
| `vehicle_class_ids` | list[string] | Associated vehicle classes |
| `engine_position_ids` | list[string] | Engine positions |
| `drivetrain_ids` | list[string] | Available drivetrain types |
| `designer_ids` | list[string] | Associated designers |
| `predecessors` | list[object] | Extracted predecessor relationships |
| `successors` | list[object] | Extracted successor relationships |

A relationship record can contain:

```json
{
  "name": "BMW E9",
  "url": "https://en.wikipedia.org/wiki/BMW_E9",
  "target_id": "bmw_new_six_coupes_e9"
}
```

`target_id` may remain `null` when the target cannot be resolved confidently.

### Version

| Property | Type | Meaning |
|---|---|---|
| `id` | string | Stable canonical identifier |
| `name` | string | Canonical version designation |
| `variant_id` | string | Parent Variant |
| `power_hp` | integer/null | Representative Version-level power |
| `engines` | list[object] | Engine usages associated with this Version |

Exact-engine example:

```json
{
  "id": "bmw_4_series_g22_430i_430i_xdrive",
  "name": "430i 430i xDrive",
  "variant_id": "bmw_4_series_g22",
  "power_hp": 255,
  "engines": [
    {
      "engine_series_id": "bmw_b",
      "engine_family_id": "bmw_b48",
      "engine_id": "bmw_b48b20o1",
      "displacement_l": 2.0,
      "cylinder_count": 4,
      "arrangement": "Inline"
    }
  ]
}
```

Family-only example:

```json
{
  "engine_series_id": "bmw_b",
  "engine_family_id": "bmw_b48",
  "engine_id": null,
  "displacement_l": 2.0,
  "cylinder_count": 4,
  "arrangement": "Inline"
}
```

A Version may have more than one engine usage. Power remains a representative Version-level value rather than an Engine property.

### EngineSeries

Represents a broad manufacturer-specific engine series.

Examples for BMW:

```text
B
M
N
S
```

| Property | Type | Meaning |
|---|---|---|
| `id` | string | Stable manufacturer-scoped identifier |
| `name` | string | Series designation |
| `manufacturer_id` | string | Owning Manufacturer |

```json
{
  "id": "bmw_b",
  "name": "B",
  "manufacturer_id": "bmw"
}
```

### EngineFamily

Represents a reusable, comparison-friendly engine family.

Examples:

```text
B48
B58
N55
M30
S63
```

| Property | Type | Meaning |
|---|---|---|
| `id` | string | Stable manufacturer-scoped identifier |
| `name` | string | Canonical family designation |
| `engine_series_id` | string/null | Parent EngineSeries when known |

```json
{
  "id": "bmw_b48",
  "name": "B48",
  "engine_series_id": "bmw_b"
}
```

EngineFamily is the level currently used by the Cardle engine-family comparison clue.

### Engine

Represents the most specific engine code explicitly supported by the source.

Examples:

```text
B48B20M0
B48B20O1
B58B30O1
M30B35
N55B30M0
```

| Property | Type | Meaning |
|---|---|---|
| `id` | string | Stable manufacturer-scoped identifier |
| `code` | string | Exact normalized engine code |
| `engine_family_id` | string/null | Parent EngineFamily when known |

```json
{
  "id": "bmw_b48b20o1",
  "code": "B48B20O1",
  "engine_family_id": "bmw_b48"
}
```

Specific Engine nodes are created only when the source provides more detail than the family itself.

```text
Source says B48B20O1
→ B → B48 → B48B20O1

Source says B48
→ B → B48 → no specific Engine
```

### Engine usage properties

Application-specific values remain on the Version's engine usage:

| Property | Type | Meaning |
|---|---|---|
| `engine_series_id` | string/null | Series identity when known |
| `engine_family_id` | string/null | Family identity when known |
| `engine_id` | string/null | Exact engine identity when known |
| `displacement_l` | number/null | Reported displacement |
| `cylinder_count` | integer/null | Reported cylinder count |
| `arrangement` | string/null | Reported cylinder arrangement |

This avoids forcing source/application-specific data onto reusable engine entities.

---

## 4. Controlled vocabulary entities

| Entity | Example values |
|---|---|
| `BodyStyle` | Sedan, Wagon, Coupe, Convertible, Hatchback, Fastback, Roadster, SUV, Pickup |
| `VehicleClass` | Executive car, Grand tourer, Compact executive car |
| `EnginePosition` | Front, Mid, Rear |
| `Drivetrain` | FWD, RWD, AWD |
| `Designer` | Paul Bracq, Chris Bangle, Joji Nagashima |

Each uses a simple reusable structure such as:

```json
{
  "id": "coupe",
  "name": "Coupe"
}
```

---

## 5. Conceptual / Neo4j relationships

```text
(:Manufacturer)
      │
      ├── PRODUCES ───────────────► (:Model)
      │                                │
      │                                └── HAS_VARIANT ──► (:Variant)
      │                                                     │
      │                                                     ├── HAS_VERSION ──► (:Version)
      │                                                     │                     │
      │                                                     │                     ├── USES_ENGINE ───────► (:Engine)
      │                                                     │                     └── USES_ENGINE_FAMILY ► (:EngineFamily)
      │                                                     │
      │                                                     ├── HAS_BODY_STYLE ─────► (:BodyStyle)
      │                                                     ├── HAS_CLASS ──────────► (:VehicleClass)
      │                                                     ├── HAS_ENGINE_POSITION ► (:EnginePosition)
      │                                                     ├── HAS_DRIVETRAIN ─────► (:Drivetrain)
      │                                                     ├── DESIGNED_BY ────────► (:Designer)
      │                                                     └── SUCCEEDED_BY ───────► (:Variant)
      │
      └── HAS_ENGINE_SERIES ──────► (:EngineSeries)
                                        │
                                        └── HAS_ENGINE_FAMILY ──► (:EngineFamily)
                                                                      │
                                                                      └── HAS_ENGINE ──► (:Engine)
```

`USES_ENGINE` means an exact Engine is known.

`USES_ENGINE_FAMILY` means the source supports only an EngineFamily.

No fake Engine node is created merely to force both cases into the same graph shape.

---

## 6. Stable ID policy

Vehicle examples:

```text
BMW → bmw
6 Series → bmw_6_series
E24 → bmw_6_series_e24
M6 → bmw_6_series_e24_m6
Paul Bracq → paul_bracq
```

Engine IDs are manufacturer-scoped:

```text
BMW B series → bmw_b
BMW B48 family → bmw_b48
BMW B48B20O1 engine → bmw_b48b20o1
```

Conceptually:

```text
Manufacturer: manufacturer
Model: manufacturer + model
Variant: manufacturer + model + variant
Version: manufacturer + model + variant + version
EngineSeries: manufacturer + series
EngineFamily: manufacturer + family
Engine: manufacturer + exact engine code
```

IDs use deterministic slugification and Unicode-aware normalization.

Once persisted, changing ID semantics is a migration rather than a parser cleanup.

---

## 7. Canonicalization rules

- **Normalize structure, not history.**
- **Reuse canonical entities.**
- **Never invent missing facts.**
- **Preserve source precision.** Family-only data stays family-only.
- **Prefer conservative relationships.**
- **Preserve meaningful distinctions** such as market qualifiers.
- **Normalize obvious presentation noise** such as footnote markers.
- **Allow multiple values where reality requires them.**
- **Allow multiple engine usages per Version.**
- **Treat missing source data as valid canonical data.**
- **Keep the schema generic but parsing rules manufacturer-aware.**

Engine hierarchy resolution is deliberately manufacturer-specific. For BMW, common codes can often be resolved structurally:

```text
B48B20O1 → B → B48 → B48B20O1
N55B30M0 → N → N55 → N55B30M0
M30B35   → M → M30 → M30B35
```

Historical or ambiguous codes are handled conservatively rather than through blind prefix truncation.

Manufacturers whose exact codes do not encode their family may require explicit mappings or source associations.

---

## 8. Variant ↔ Version policy

Wikipedia often provides one version/engine table for several closely related chassis variants.

Cardle does not reconstruct exact body-style-specific availability unless the source supports it explicitly.

For example:

```text
G20 = sedan
G21 = wagon
```

may share generic Version records from the same source table.

Explicit BMW long-wheelbase distinctions are handled when clear, such as:

```text
318i / 320Li
320i / 325Li
320d / 320Ld
```

Ambiguous generic availability may remain shared.

---

## 9. Source and provenance policy

Wikipedia is currently the primary extraction source.

Raw data is preserved, while canonical Variants retain `source_url` for traceability.

```text
Wikipedia
    ↓
raw JSON          ← preserved evidence
    ↓
canonical JSON    ← regeneratable interpretation
```

> **Raw data is evidence; canonical data is Cardle's interpretation of that evidence.**

---

## 10. Validation policy

Important invariants include:

```text
IDs must be unique.

Every Model must reference an existing Manufacturer.
Every Variant must reference an existing Model.
Every Version must reference an existing Variant.

Every EngineSeries must reference an existing Manufacturer.
Every EngineFamily.engine_series_id, when present,
must reference an existing EngineSeries.
Every Engine.engine_family_id, when present,
must reference an existing EngineFamily.

Every Version engine usage must identify at least an
EngineFamily or an exact Engine.

Engine usage references must point to existing entities.

If a usage contains series/family/engine IDs,
their hierarchy must be mutually consistent.

Vocabulary references must point to existing entities.
Resolved predecessor/successor target IDs must point to existing Variants.
Contradictory duplicate canonical entities are rejected.
```

Usage-level values are validated conservatively:

```text
displacement_l > 0 when present
cylinder_count > 0 when present
arrangement is string/null
```

---

## 11. Explicit v1.1 limitations

| Limitation | v1.1 decision |
|---|---|
| Some vehicles appear under `No Model` | Accepted |
| Facelifts are not consistently separate Variants | Deferred |
| Some Wikipedia fields are missing/ambiguous | Leave null/empty |
| Exact Version availability by body style is sometimes unknown | Share conservatively |
| Some predecessor/successor targets remain unresolved | Keep `target_id: null` |
| Version production periods are not modeled canonically | Deferred |
| Detailed historical power changes are not modeled | One representative Version-level value |
| Some source rows expose only EngineFamily | Preserve family-only knowledge |
| Historical BMW engine hierarchy has ambiguous/special cases | Keep conservative; explicit mappings only when justified |
| Engine-family inference outside BMW is incomplete | Add brand-specific resolvers as needed |
| Electric motor architecture is not modeled like combustion engines | Deferred |
| Multi-generation model-page extraction is not generalized yet | Future scraper work |
| Prose-only LLM extraction | Future ingestion extension |
| RDF/SHACL representation | Future semantic extension |

---

## 12. What is stable in v1.1

Current entities:

```text
Manufacturer
Model
Variant
Version
EngineSeries
EngineFamily
Engine
BodyStyle
VehicleClass
EnginePosition
Drivetrain
Designer
```

Vehicle hierarchy:

```text
Manufacturer
   ↓
Model
   ↓
Variant
   ↓
Version
```

Engine hierarchy:

```text
Manufacturer
   ↓
EngineSeries
   ↓
EngineFamily
   ↓
Engine
```

Version engine usage preserves source precision:

```text
Version → Engine
```

when an exact engine is known, or:

```text
Version → EngineFamily
```

when only a family is known.

> **Canonical Schema v1.1 is the current schema for the playable BMW Cardle prototype.**

---

## 13. Cardle game interpretation

The knowledge graph stores more engine detail than the current game needs.

The graph can distinguish:

```text
B → B48 → B48B20M0
B → B48 → B48B20O1
```

while the current game compares both at:

```text
EngineFamily = B48
```

The repository resolves both exact-engine and family-only graph paths into:

```text
GameVehicle.engine_families
```

This preserves rich graph semantics without complicating the current comparer.

---

## 14. Future extensions

- More manufacturers and brand-specific engine resolvers
- Explicit mappings for ambiguous historical engine codes
- Multi-generation model-page extraction
- Lightweight LLM-assisted prose extraction
- More detailed version-production histories
- More detailed EV/motor modeling
- Facelift-specific modeling
- Exact-engine clues or richer engine similarity
- RDF export
- SHACL validation
- External knowledge graph linking
- SPARQL support
- Additional provenance metadata

These are extensions, not prerequisites for the playable BMW Cardle prototype.