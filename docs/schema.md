CANONICAL AUTOMOTIVE SCHEMA — v1
To be updated!!!!!!

Manufacturer
- id
- name
- country of origin
- PRODUCES -> Model


Model
- id
- name
- HAS_VARIANT -> Variant


Variant
- id
- name / manufacturer designation
- manufacturer/internal code
- production start year
- production end year
- DESIGNED_BY -> Designer
- SUCCEEDED_BY -> Variant
- HAS_VERSION -> Version


Version
- id
- name
- production start year
- production end year
- power (canonical: hp)

- USES_ENGINE -> Engine
- HAS_BODY_STYLE -> BodyStyle
- HAS_DRIVETRAIN -> Drivetrain
- HAS_ENGINE_POSITION -> EnginePosition [optional]
- HAS_CLASS -> VehicleClass


Engine
- id
- name/code
- displacement (cc)
- cylinder count
- cylinder arrangement


BodyStyle
- id
- name
- canonical examples:
  Sedan, Coupe, Wagon, Hatchback, Convertible, SUV, Pickup


Drivetrain
- id
- name
- FWD, RWD, AWD, 4WD



EnginePosition
- id
- name
- Front, Mid, Rear


VehicleClass
- id
- name
- use the classification explicitly given by the accepted source
- examples:
  Compact car
  Executive car
  Grand tourer
  Sports car
  S-segment
  E-segment


CANONICAL / PLAYABLE VERSION MUST HAVE

- Manufacturer
    - Model
        - Variant
            - Vehicle class
            - Version name
                - Production period
                - Body style
                - Engine
                - Power
                - Drivetrain

Engine position, designer, successor, etc. may be missing.


CORE RULES

- Every canonical entity has a globally unique stable id.
- Names are display values, not identifiers.
- Reuse existing canonical entities.
- Hierarchy is represented exclusively through relationships.
- One marketed Version name per Variant.
- Facelifts are separate Variants.
- Distinct manufacturer body/model codes are separate Variants.
- Store SUCCEEDED_BY only when explicitly supported by an accepted source.
- Missing data means unknown, not false.
- Never infer unsupported facts during source-constrained ingestion.
- BMW/non-American cars use European-market specifications; American cars use US-market specifications.
-Canonical entities represent real-world concepts, not source records.

CHANGE!!! Changed from using specific engines to using engine family.

A Version may reference multiple valid engine families. power_hp stores one canonical power figure, chosen from the final scraped power entry, and is treated as a Version-level gameplay attribute rather than a precise engine-specific specification.