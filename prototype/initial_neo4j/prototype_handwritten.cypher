// CARDLE — BMW 6 SERIES KNOWLEDGE GRAPH
// Generations covered:
//   E24
//   E63/E64
//   F06/F12/F13
//
// Source-constrained facts only from:
//   https://en.wikipedia.org/wiki/BMW_6_Series_(E24)
//   https://en.wikipedia.org/wiki/BMW_6_Series_(E63)
//   https://en.wikipedia.org/wiki/BMW_6_Series_(F12)
//

MERGE (bmw:Manufacturer {id:"bmw"})
SET bmw.name = "BMW"

MERGE (six:Model {id:"bmw_6_series"})
SET six.name = "6 Series"

MERGE (bmw)-[:PRODUCES]->(six)

MERGE (coupe:BodyStyle {id:"body_style_coupe"})
SET coupe.name = "Coupe"

MERGE (convertible:BodyStyle {id:"body_style_convertible"})
SET convertible.name = "Convertible"

MERGE (sedan:BodyStyle {id:"body_style_sedan"})
SET sedan.name = "Sedan"

MERGE (rwd:Drivetrain {id:"drivetrain_rwd"})
SET rwd.name = "RWD"

MERGE (awd:Drivetrain {id:"drivetrain_awd"})
SET awd.name = "AWD"

MERGE (front:EnginePosition {id:"engine_position_front"})
SET front.name = "Front"

MERGE (paul:Designer {id:"designer_paul_bracq"})
SET paul.name = "Paul Bracq"

MERGE (adrian:Designer {id:"designer_adrian_van_hooydonk"})
SET adrian.name = "Adrian van Hooydonk"

MERGE (nader:Designer {id:"designer_nader_faghihzadeh"})
SET nader.name = "Nader Faghihzadeh"


// ============================================================================
// E24
// ============================================================================

MERGE (e24:Variant {id:"bmw_6_series_e24"})
SET e24.name = "E24",
    e24.manufacturerCode = "E24",
    e24.productionStartYear = 1976,
    e24.productionEndYear = 1982

MERGE (e24f:Variant {id:"bmw_6_series_e24_facelift"})
SET e24f.name = "E24 Facelift",
    e24f.manufacturerCode = "E24",
    e24f.productionStartYear = 1982,
    e24f.productionEndYear = 1989

MERGE (six)-[:HAS_VARIANT]->(e24)
MERGE (six)-[:HAS_VARIANT]->(e24f)
MERGE (e24)-[:SUCCEEDED_BY]->(e24f)

MERGE (e24)-[:DESIGNED_BY]->(paul)
MERGE (e24f)-[:DESIGNED_BY]->(paul)


// E24 engines — exact cc is provided on the page.

MERGE (m30b28:Engine {id:"bmw_engine_m30b28"})
SET m30b28.name = "M30B28",
    m30b28.displacementCc = 2788,
    m30b28.cylinderCount = 6,
    m30b28.cylinderArrangement = "Inline"

MERGE (m30b30v:Engine {id:"bmw_engine_m30b30v"})
SET m30b30v.name = "M30B30V",
    m30b30v.displacementCc = 2986,
    m30b30v.cylinderCount = 6,
    m30b30v.cylinderArrangement = "Inline"

MERGE (m30b32:Engine {id:"bmw_engine_m30b32"})
SET m30b32.name = "M30B32",
    m30b32.displacementCc = 3210,
    m30b32.cylinderCount = 6,
    m30b32.cylinderArrangement = "Inline"

MERGE (m90:Engine {id:"bmw_engine_m90"})
SET m90.name = "M90",
    m90.displacementCc = 3453,
    m90.cylinderCount = 6,
    m90.cylinderArrangement = "Inline"

MERGE (m30b34:Engine {id:"bmw_engine_m30b34"})
SET m30b34.name = "M30B34",
    m30b34.displacementCc = 3430,
    m30b34.cylinderCount = 6,
    m30b34.cylinderArrangement = "Inline"

MERGE (m88_3:Engine {id:"bmw_engine_m88_3"})
SET m88_3.name = "M88/3",
    m88_3.displacementCc = 3453,
    m88_3.cylinderCount = 6,
    m88_3.cylinderArrangement = "Inline"


// E24 pre-facelift.
// 633CSi: 1976–79 197 hp vs 1979–84 194 hp.
// Within E24 (ending 1982) the two periods tie, so later spec wins: 194 hp.

MERGE (e24_630cs:Version {id:"bmw_6_series_e24_630cs"})
SET e24_630cs.name = "630CS",
    e24_630cs.productionStartYear = 1976,
    e24_630cs.productionEndYear = 1979,
    e24_630cs.powerHp = 182

MERGE (e24_633csi:Version {id:"bmw_6_series_e24_633csi"})
SET e24_633csi.name = "633CSi",
    e24_633csi.productionStartYear = 1976,
    e24_633csi.productionEndYear = 1982,
    e24_633csi.powerHp = 194

MERGE (e24_628csi:Version {id:"bmw_6_series_e24_628csi"})
SET e24_628csi.name = "628CSi",
    e24_628csi.productionStartYear = 1979,
    e24_628csi.productionEndYear = 1982,
    e24_628csi.powerHp = 181

MERGE (e24_635csi:Version {id:"bmw_6_series_e24_635csi"})
SET e24_635csi.name = "635CSi",
    e24_635csi.productionStartYear = 1978,
    e24_635csi.productionEndYear = 1982,
    e24_635csi.powerHp = 215

FOREACH (v IN [e24_630cs,e24_633csi,e24_628csi,e24_635csi] |
    MERGE (e24)-[:HAS_VERSION]->(v)
    MERGE (v)-[:HAS_BODY_STYLE]->(coupe)
    MERGE (v)-[:HAS_DRIVETRAIN]->(rwd)
    MERGE (v)-[:HAS_ENGINE_POSITION]->(front)
)

MERGE (e24_630cs)-[:USES_ENGINE]->(m30b30v)
MERGE (e24_633csi)-[:USES_ENGINE]->(m30b32)
MERGE (e24_628csi)-[:USES_ENGINE]->(m30b28)
MERGE (e24_635csi)-[:USES_ENGINE]->(m90)


// E24 facelift.
// 635CSi: ordinary European non-catalytic M30B34/215 hp is canonical.
// M635CSi: European M88/3 / 282 hp is canonical.

MERGE (e24f_628csi:Version {id:"bmw_6_series_e24_facelift_628csi"})
SET e24f_628csi.name = "628CSi",
    e24f_628csi.productionStartYear = 1982,
    e24f_628csi.productionEndYear = 1987,
    e24f_628csi.powerHp = 181

MERGE (e24f_633csi:Version {id:"bmw_6_series_e24_facelift_633csi"})
SET e24f_633csi.name = "633CSi",
    e24f_633csi.productionStartYear = 1982,
    e24f_633csi.productionEndYear = 1984,
    e24f_633csi.powerHp = 194

MERGE (e24f_635csi:Version {id:"bmw_6_series_e24_facelift_635csi"})
SET e24f_635csi.name = "635CSi",
    e24f_635csi.productionStartYear = 1982,
    e24f_635csi.productionEndYear = 1989,
    e24f_635csi.powerHp = 215

MERGE (e24f_m635csi:Version {id:"bmw_6_series_e24_facelift_m635csi"})
SET e24f_m635csi.name = "M635CSi",
    e24f_m635csi.productionStartYear = 1984,
    e24f_m635csi.productionEndYear = 1989,
    e24f_m635csi.powerHp = 282

FOREACH (v IN [e24f_628csi,e24f_633csi,e24f_635csi,e24f_m635csi] |
    MERGE (e24f)-[:HAS_VERSION]->(v)
    MERGE (v)-[:HAS_BODY_STYLE]->(coupe)
    MERGE (v)-[:HAS_DRIVETRAIN]->(rwd)
    MERGE (v)-[:HAS_ENGINE_POSITION]->(front)
)

MERGE (e24f_628csi)-[:USES_ENGINE]->(m30b28)
MERGE (e24f_633csi)-[:USES_ENGINE]->(m30b32)
MERGE (e24f_635csi)-[:USES_ENGINE]->(m30b34)
MERGE (e24f_m635csi)-[:USES_ENGINE]->(m88_3)


// ============================================================================
// E63 / E64
// ============================================================================

MERGE (e63:Variant {id:"bmw_6_series_e63"})
SET e63.name = "E63",
    e63.manufacturerCode = "E63",
    e63.productionStartYear = 2003,
    e63.productionEndYear = 2007,
    e63.segment = "S"

MERGE (e64:Variant {id:"bmw_6_series_e64"})
SET e64.name = "E64",
    e64.manufacturerCode = "E64",
    e64.productionStartYear = 2004,
    e64.productionEndYear = 2007,
    e64.segment = "S"

MERGE (e63f:Variant {id:"bmw_6_series_e63_facelift"})
SET e63f.name = "E63 Facelift",
    e63f.manufacturerCode = "E63",
    e63f.productionStartYear = 2007,
    e63f.productionEndYear = 2010,
    e63f.segment = "S"

MERGE (e64f:Variant {id:"bmw_6_series_e64_facelift"})
SET e64f.name = "E64 Facelift",
    e64f.manufacturerCode = "E64",
    e64f.productionStartYear = 2007,
    e64f.productionEndYear = 2010,
    e64f.segment = "S"

FOREACH (v IN [e63,e64,e63f,e64f] |
    MERGE (six)-[:HAS_VARIANT]->(v)
    MERGE (v)-[:DESIGNED_BY]->(adrian)
)

MERGE (e63)-[:SUCCEEDED_BY]->(e63f)
MERGE (e64)-[:SUCCEEDED_BY]->(e64f)


// E63/E64 engine families.
// The page gives nominal litres, not exact cc, so displacementCc is omitted.

MERGE (n52:Engine {id:"bmw_engine_n52_3_0l"})
SET n52.name = "N52",
    n52.cylinderCount = 6,
    n52.cylinderArrangement = "Inline"

MERGE (n62_44:Engine {id:"bmw_engine_n62_4_4l"})
SET n62_44.name = "N62 4.4 L",
    n62_44.cylinderCount = 8,
    n62_44.cylinderArrangement = "V"

MERGE (n62_48:Engine {id:"bmw_engine_n62_4_8l"})
SET n62_48.name = "N62 4.8 L",
    n62_48.cylinderCount = 8,
    n62_48.cylinderArrangement = "V"

MERGE (s85:Engine {id:"bmw_engine_s85_5_0l"})
SET s85.name = "S85",
    s85.cylinderCount = 10,
    s85.cylinderArrangement = "V"

MERGE (m57:Engine {id:"bmw_engine_m57_3_0l"})
SET m57.name = "M57",
    m57.cylinderCount = 6,
    m57.cylinderArrangement = "Inline"


// Pre-facelift E63 — Coupe.

MERGE (e63_630ci:Version {id:"bmw_6_series_e63_630ci"})
SET e63_630ci.name = "630Ci",
    e63_630ci.productionStartYear = 2003,
    e63_630ci.productionEndYear = 2007,
    e63_630ci.powerHp = 255

MERGE (e63_645ci:Version {id:"bmw_6_series_e63_645ci"})
SET e63_645ci.name = "645Ci",
    e63_645ci.productionStartYear = 2003,
    e63_645ci.productionEndYear = 2005,
    e63_645ci.powerHp = 329

MERGE (e63_650i:Version {id:"bmw_6_series_e63_650i"})
SET e63_650i.name = "650i",
    e63_650i.productionStartYear = 2005,
    e63_650i.productionEndYear = 2007,
    e63_650i.powerHp = 362

MERGE (e63_m6:Version {id:"bmw_6_series_e63_m6"})
SET e63_m6.name = "M6",
    e63_m6.productionStartYear = 2005,
    e63_m6.productionEndYear = 2007,
    e63_m6.powerHp = 500

FOREACH (v IN [e63_630ci,e63_645ci,e63_650i,e63_m6] |
    MERGE (e63)-[:HAS_VERSION]->(v)
    MERGE (v)-[:HAS_BODY_STYLE]->(coupe)
    MERGE (v)-[:HAS_DRIVETRAIN]->(rwd)
)

MERGE (e63_630ci)-[:USES_ENGINE]->(n52)
MERGE (e63_645ci)-[:USES_ENGINE]->(n62_44)
MERGE (e63_650i)-[:USES_ENGINE]->(n62_48)
MERGE (e63_m6)-[:USES_ENGINE]->(s85)


// Pre-facelift E64 — Convertible.
// The page gives the generation-wide engine table, while E64 body production
// begins in 2004. The version period is bounded by the body-code availability.

MERGE (e64_630ci:Version {id:"bmw_6_series_e64_630ci"})
SET e64_630ci.name = "630Ci",
    e64_630ci.productionStartYear = 2004,
    e64_630ci.productionEndYear = 2007,
    e64_630ci.powerHp = 255

MERGE (e64_645ci:Version {id:"bmw_6_series_e64_645ci"})
SET e64_645ci.name = "645Ci",
    e64_645ci.productionStartYear = 2004,
    e64_645ci.productionEndYear = 2005,
    e64_645ci.powerHp = 329

MERGE (e64_650i:Version {id:"bmw_6_series_e64_650i"})
SET e64_650i.name = "650i",
    e64_650i.productionStartYear = 2005,
    e64_650i.productionEndYear = 2007,
    e64_650i.powerHp = 362

MERGE (e64_m6:Version {id:"bmw_6_series_e64_m6"})
SET e64_m6.name = "M6",
    e64_m6.productionStartYear = 2006,
    e64_m6.productionEndYear = 2007,
    e64_m6.powerHp = 500

FOREACH (v IN [e64_630ci,e64_645ci,e64_650i,e64_m6] |
    MERGE (e64)-[:HAS_VERSION]->(v)
    MERGE (v)-[:HAS_BODY_STYLE]->(convertible)
    MERGE (v)-[:HAS_DRIVETRAIN]->(rwd)
)

MERGE (e64_630ci)-[:USES_ENGINE]->(n52)
MERGE (e64_645ci)-[:USES_ENGINE]->(n62_44)
MERGE (e64_650i)-[:USES_ENGINE]->(n62_48)
MERGE (e64_m6)-[:USES_ENGINE]->(s85)


// E63/E64 facelift.
// 630i is intentionally incomplete:
// N53/268 hp in low-sulphur-fuel countries, N52/255 hp elsewhere.
// The page does not resolve one Europe-wide canonical specification.

MERGE (e63f_630i:Version {id:"bmw_6_series_e63_facelift_630i"})
SET e63f_630i.name = "630i",
    e63f_630i.productionStartYear = 2007,
    e63f_630i.productionEndYear = 2010

MERGE (e63f_635d:Version {id:"bmw_6_series_e63_facelift_635d"})
SET e63f_635d.name = "635d",
    e63f_635d.productionStartYear = 2007,
    e63f_635d.productionEndYear = 2010,
    e63f_635d.powerHp = 282

MERGE (e63f_650i:Version {id:"bmw_6_series_e63_facelift_650i"})
SET e63f_650i.name = "650i",
    e63f_650i.productionStartYear = 2007,
    e63f_650i.productionEndYear = 2010,
    e63f_650i.powerHp = 362

MERGE (e63f_m6:Version {id:"bmw_6_series_e63_facelift_m6"})
SET e63f_m6.name = "M6",
    e63f_m6.productionStartYear = 2007,
    e63f_m6.productionEndYear = 2010,
    e63f_m6.powerHp = 500

FOREACH (v IN [e63f_630i,e63f_635d,e63f_650i,e63f_m6] |
    MERGE (e63f)-[:HAS_VERSION]->(v)
    MERGE (v)-[:HAS_BODY_STYLE]->(coupe)
    MERGE (v)-[:HAS_DRIVETRAIN]->(rwd)
)

MERGE (e63f_635d)-[:USES_ENGINE]->(m57)
MERGE (e63f_650i)-[:USES_ENGINE]->(n62_48)
MERGE (e63f_m6)-[:USES_ENGINE]->(s85)


MERGE (e64f_630i:Version {id:"bmw_6_series_e64_facelift_630i"})
SET e64f_630i.name = "630i",
    e64f_630i.productionStartYear = 2007,
    e64f_630i.productionEndYear = 2010

MERGE (e64f_635d:Version {id:"bmw_6_series_e64_facelift_635d"})
SET e64f_635d.name = "635d",
    e64f_635d.productionStartYear = 2007,
    e64f_635d.productionEndYear = 2010,
    e64f_635d.powerHp = 282

MERGE (e64f_650i:Version {id:"bmw_6_series_e64_facelift_650i"})
SET e64f_650i.name = "650i",
    e64f_650i.productionStartYear = 2007,
    e64f_650i.productionEndYear = 2010,
    e64f_650i.powerHp = 362

MERGE (e64f_m6:Version {id:"bmw_6_series_e64_facelift_m6"})
SET e64f_m6.name = "M6",
    e64f_m6.productionStartYear = 2007,
    e64f_m6.productionEndYear = 2010,
    e64f_m6.powerHp = 500

FOREACH (v IN [e64f_630i,e64f_635d,e64f_650i,e64f_m6] |
    MERGE (e64f)-[:HAS_VERSION]->(v)
    MERGE (v)-[:HAS_BODY_STYLE]->(convertible)
    MERGE (v)-[:HAS_DRIVETRAIN]->(rwd)
)

MERGE (e64f_635d)-[:USES_ENGINE]->(m57)
MERGE (e64f_650i)-[:USES_ENGINE]->(n62_48)
MERGE (e64f_m6)-[:USES_ENGINE]->(s85)


// ============================================================================
// F06 / F12 / F13
// ============================================================================

MERGE (f12:Variant {id:"bmw_6_series_f12"})
SET f12.name = "F12",
    f12.manufacturerCode = "F12",
    f12.productionStartYear = 2011,
    f12.productionEndYear = 2015,
    f12.segment = "S"

MERGE (f13:Variant {id:"bmw_6_series_f13"})
SET f13.name = "F13",
    f13.manufacturerCode = "F13",
    f13.productionStartYear = 2011,
    f13.productionEndYear = 2015,
    f13.segment = "S"

MERGE (f06:Variant {id:"bmw_6_series_f06"})
SET f06.name = "F06",
    f06.manufacturerCode = "F06",
    f06.productionStartYear = 2012,
    f06.productionEndYear = 2015,
    f06.segment = "E"

MERGE (f12f:Variant {id:"bmw_6_series_f12_facelift"})
SET f12f.name = "F12 Facelift",
    f12f.manufacturerCode = "F12",
    f12f.productionStartYear = 2015,
    f12f.productionEndYear = 2018,
    f12f.segment = "S"

MERGE (f13f:Variant {id:"bmw_6_series_f13_facelift"})
SET f13f.name = "F13 Facelift",
    f13f.manufacturerCode = "F13",
    f13f.productionStartYear = 2015,
    f13f.productionEndYear = 2017,
    f13f.segment = "S"

MERGE (f06f:Variant {id:"bmw_6_series_f06_facelift"})
SET f06f.name = "F06 Facelift",
    f06f.manufacturerCode = "F06",
    f06f.productionStartYear = 2015,
    f06f.productionEndYear = 2018,
    f06f.segment = "E"

FOREACH (v IN [f12,f13,f06,f12f,f13f,f06f] |
    MERGE (six)-[:HAS_VARIANT]->(v)
    MERGE (v)-[:DESIGNED_BY]->(nader)
)

MERGE (f12)-[:SUCCEEDED_BY]->(f12f)
MERGE (f13)-[:SUCCEEDED_BY]->(f13f)
MERGE (f06)-[:SUCCEEDED_BY]->(f06f)


// F-generation engines — exact cc is not given on the page.

MERGE (n55:Engine {id:"bmw_engine_n55_3_0l"})
SET n55.name = "N55",
    n55.cylinderCount = 6,
    n55.cylinderArrangement = "Inline"

MERGE (n63:Engine {id:"bmw_engine_n63_4_4l"})
SET n63.name = "N63",
    n63.cylinderCount = 8,
    n63.cylinderArrangement = "V"

MERGE (s63:Engine {id:"bmw_engine_s63_4_4l"})
SET s63.name = "S63",
    s63.cylinderCount = 8,
    s63.cylinderArrangement = "V"

MERGE (n57:Engine {id:"bmw_engine_n57_3_0l"})
SET n57.name = "N57",
    n57.cylinderCount = 6,
    n57.cylinderArrangement = "Inline"


// Standard RWD versions.
// 650i changed from 402 hp (2011–2013) to 444 hp (2013–2018).
// Per canonicalization, later/longer spec is used: 444 hp.


// F12 Convertible
MERGE (f12_640i:Version {id:"bmw_6_series_f12_640i"})
SET f12_640i.name="640i", f12_640i.productionStartYear=2011, f12_640i.productionEndYear=2015, f12_640i.powerHp=315
MERGE (f12_650i:Version {id:"bmw_6_series_f12_650i"})
SET f12_650i.name="650i", f12_650i.productionStartYear=2011, f12_650i.productionEndYear=2015, f12_650i.powerHp=444
MERGE (f12_640d:Version {id:"bmw_6_series_f12_640d"})
SET f12_640d.name="640d", f12_640d.productionStartYear=2011, f12_640d.productionEndYear=2015, f12_640d.powerHp=308
MERGE (f12_m6:Version {id:"bmw_6_series_f12_m6"})
SET f12_m6.name="M6", f12_m6.productionStartYear=2012, f12_m6.productionEndYear=2015, f12_m6.powerHp=553

FOREACH (v IN [f12_640i,f12_650i,f12_640d,f12_m6] |
    MERGE (f12)-[:HAS_VERSION]->(v)
    MERGE (v)-[:HAS_BODY_STYLE]->(convertible)
    MERGE (v)-[:HAS_DRIVETRAIN]->(rwd)
)

MERGE (f12_640i)-[:USES_ENGINE]->(n55)
MERGE (f12_650i)-[:USES_ENGINE]->(n63)
MERGE (f12_640d)-[:USES_ENGINE]->(n57)
MERGE (f12_m6)-[:USES_ENGINE]->(s63)


// F13 Coupe
MERGE (f13_640i:Version {id:"bmw_6_series_f13_640i"})
SET f13_640i.name="640i", f13_640i.productionStartYear=2011, f13_640i.productionEndYear=2015, f13_640i.powerHp=315
MERGE (f13_650i:Version {id:"bmw_6_series_f13_650i"})
SET f13_650i.name="650i", f13_650i.productionStartYear=2011, f13_650i.productionEndYear=2015, f13_650i.powerHp=444
MERGE (f13_640d:Version {id:"bmw_6_series_f13_640d"})
SET f13_640d.name="640d", f13_640d.productionStartYear=2011, f13_640d.productionEndYear=2015, f13_640d.powerHp=308
MERGE (f13_m6:Version {id:"bmw_6_series_f13_m6"})
SET f13_m6.name="M6", f13_m6.productionStartYear=2012, f13_m6.productionEndYear=2015, f13_m6.powerHp=553

FOREACH (v IN [f13_640i,f13_650i,f13_640d,f13_m6] |
    MERGE (f13)-[:HAS_VERSION]->(v)
    MERGE (v)-[:HAS_BODY_STYLE]->(coupe)
    MERGE (v)-[:HAS_DRIVETRAIN]->(rwd)
)

MERGE (f13_640i)-[:USES_ENGINE]->(n55)
MERGE (f13_650i)-[:USES_ENGINE]->(n63)
MERGE (f13_640d)-[:USES_ENGINE]->(n57)
MERGE (f13_m6)-[:USES_ENGINE]->(s63)


// F06 Gran Coupe, normalized to Sedan
MERGE (f06_640i:Version {id:"bmw_6_series_f06_640i"})
SET f06_640i.name="640i", f06_640i.productionStartYear=2012, f06_640i.productionEndYear=2015, f06_640i.powerHp=315
MERGE (f06_650i:Version {id:"bmw_6_series_f06_650i"})
SET f06_650i.name="650i", f06_650i.productionStartYear=2012, f06_650i.productionEndYear=2015, f06_650i.powerHp=444
MERGE (f06_640d:Version {id:"bmw_6_series_f06_640d"})
SET f06_640d.name="640d", f06_640d.productionStartYear=2012, f06_640d.productionEndYear=2015, f06_640d.powerHp=308
MERGE (f06_m6:Version {id:"bmw_6_series_f06_m6"})
SET f06_m6.name="M6", f06_m6.productionStartYear=2012, f06_m6.productionEndYear=2015, f06_m6.powerHp=553

FOREACH (v IN [f06_640i,f06_650i,f06_640d,f06_m6] |
    MERGE (f06)-[:HAS_VERSION]->(v)
    MERGE (v)-[:HAS_BODY_STYLE]->(sedan)
    MERGE (v)-[:HAS_DRIVETRAIN]->(rwd)
)

MERGE (f06_640i)-[:USES_ENGINE]->(n55)
MERGE (f06_650i)-[:USES_ENGINE]->(n63)
MERGE (f06_640d)-[:USES_ENGINE]->(n57)
MERGE (f06_m6)-[:USES_ENGINE]->(s63)


// Facelift versions.
// Page explicitly says all facelift models were available with xDrive.
// To avoid inventing a second marketed Version name where the page does not
// provide a body-specific lineup table, the canonical Version node records
// both RWD and AWD availability for standard facelift versions.
// M6 stays RWD only because the page explicitly describes M6 as rear-wheel drive.


// F12 Facelift — Convertible
MERGE (f12f_640i:Version {id:"bmw_6_series_f12_facelift_640i"})
SET f12f_640i.name="640i", f12f_640i.productionStartYear=2015, f12f_640i.productionEndYear=2018, f12f_640i.powerHp=315
MERGE (f12f_650i:Version {id:"bmw_6_series_f12_facelift_650i"})
SET f12f_650i.name="650i", f12f_650i.productionStartYear=2015, f12f_650i.productionEndYear=2018, f12f_650i.powerHp=444
MERGE (f12f_640d:Version {id:"bmw_6_series_f12_facelift_640d"})
SET f12f_640d.name="640d", f12f_640d.productionStartYear=2015, f12f_640d.productionEndYear=2018, f12f_640d.powerHp=308
MERGE (f12f_m6:Version {id:"bmw_6_series_f12_facelift_m6"})
SET f12f_m6.name="M6", f12f_m6.productionStartYear=2015, f12f_m6.productionEndYear=2018, f12f_m6.powerHp=553

FOREACH (v IN [f12f_640i,f12f_650i,f12f_640d,f12f_m6] |
    MERGE (f12f)-[:HAS_VERSION]->(v)
    MERGE (v)-[:HAS_BODY_STYLE]->(convertible)
    MERGE (v)-[:HAS_DRIVETRAIN]->(rwd)
)
FOREACH (v IN [f12f_640i,f12f_650i,f12f_640d] |
    MERGE (v)-[:HAS_DRIVETRAIN]->(awd)
)
MERGE (f12f_640i)-[:USES_ENGINE]->(n55)
MERGE (f12f_650i)-[:USES_ENGINE]->(n63)
MERGE (f12f_640d)-[:USES_ENGINE]->(n57)
MERGE (f12f_m6)-[:USES_ENGINE]->(s63)


// F13 Facelift — Coupe
MERGE (f13f_640i:Version {id:"bmw_6_series_f13_facelift_640i"})
SET f13f_640i.name="640i", f13f_640i.productionStartYear=2015, f13f_640i.productionEndYear=2017, f13f_640i.powerHp=315
MERGE (f13f_650i:Version {id:"bmw_6_series_f13_facelift_650i"})
SET f13f_650i.name="650i", f13f_650i.productionStartYear=2015, f13f_650i.productionEndYear=2017, f13f_650i.powerHp=444
MERGE (f13f_640d:Version {id:"bmw_6_series_f13_facelift_640d"})
SET f13f_640d.name="640d", f13f_640d.productionStartYear=2015, f13f_640d.productionEndYear=2017, f13f_640d.powerHp=308
MERGE (f13f_m6:Version {id:"bmw_6_series_f13_facelift_m6"})
SET f13f_m6.name="M6", f13f_m6.productionStartYear=2015, f13f_m6.productionEndYear=2017, f13f_m6.powerHp=553

FOREACH (v IN [f13f_640i,f13f_650i,f13f_640d,f13f_m6] |
    MERGE (f13f)-[:HAS_VERSION]->(v)
    MERGE (v)-[:HAS_BODY_STYLE]->(coupe)
    MERGE (v)-[:HAS_DRIVETRAIN]->(rwd)
)
FOREACH (v IN [f13f_640i,f13f_650i,f13f_640d] |
    MERGE (v)-[:HAS_DRIVETRAIN]->(awd)
)
MERGE (f13f_640i)-[:USES_ENGINE]->(n55)
MERGE (f13f_650i)-[:USES_ENGINE]->(n63)
MERGE (f13f_640d)-[:USES_ENGINE]->(n57)
MERGE (f13f_m6)-[:USES_ENGINE]->(s63)


// F06 Facelift — Sedan / Gran Coupe
MERGE (f06f_640i:Version {id:"bmw_6_series_f06_facelift_640i"})
SET f06f_640i.name="640i", f06f_640i.productionStartYear=2015, f06f_640i.productionEndYear=2018, f06f_640i.powerHp=315
MERGE (f06f_650i:Version {id:"bmw_6_series_f06_facelift_650i"})
SET f06f_650i.name="650i", f06f_650i.productionStartYear=2015, f06f_650i.productionEndYear=2018, f06f_650i.powerHp=444
MERGE (f06f_640d:Version {id:"bmw_6_series_f06_facelift_640d"})
SET f06f_640d.name="640d", f06f_640d.productionStartYear=2015, f06f_640d.productionEndYear=2018, f06f_640d.powerHp=308
MERGE (f06f_m6:Version {id:"bmw_6_series_f06_facelift_m6"})
SET f06f_m6.name="M6", f06f_m6.productionStartYear=2015, f06f_m6.productionEndYear=2018, f06f_m6.powerHp=553

FOREACH (v IN [f06f_640i,f06f_650i,f06f_640d,f06f_m6] |
    MERGE (f06f)-[:HAS_VERSION]->(v)
    MERGE (v)-[:HAS_BODY_STYLE]->(sedan)
    MERGE (v)-[:HAS_DRIVETRAIN]->(rwd)
)
FOREACH (v IN [f06f_640i,f06f_650i,f06f_640d] |
    MERGE (v)-[:HAS_DRIVETRAIN]->(awd)
)
MERGE (f06f_640i)-[:USES_ENGINE]->(n55)
MERGE (f06f_650i)-[:USES_ENGINE]->(n63)
MERGE (f06f_640d)-[:USES_ENGINE]->(n57)
MERGE (f06f_m6)-[:USES_ENGINE]->(s63)

MERGE (e24f)-[:SUCCEEDED_BY]->(e63)
MERGE (e63f)-[:SUCCEEDED_BY]->(f13)
MERGE (e64f)-[:SUCCEEDED_BY]->(f12)
