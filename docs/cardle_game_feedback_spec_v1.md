# Cardle Game Feedback Specification v1

This document defines the first version of the Cardle guessing and feedback rules.

The goal is to keep the game logic independent from the internal knowledge-graph structure while still using the graph to provide meaningful proximity feedback.

---

## 1. Guessable car

A player always guesses a **car**, not individual graph levels.

### Standard hierarchy

```text
Manufacturer → Model → Variant → Version
```

The guessable entity is the **Version**.

Example:

```text
BMW → 3 Series → E46 → 330i
```

Displayed to the player as one complete vehicle identity, for example:

```text
BMW 3 Series E46 330i
```

### Cars without a Model

Some vehicles do not have a meaningful Model level.

```text
Manufacturer → Variant → Version
```

The Version is still guessable.

Example:

```text
BMW → E9 → 3.0 CSi
```

Displayed as:

```text
BMW E9 3.0 CSi
```

### Variants without Versions

If a Variant genuinely has no Version entities beneath it, the Variant itself may be guessable.

The game UI should not ask the player to separately guess Manufacturer, Model, Variant, and Version.

The hierarchy is used internally to identify the vehicle and calculate structural proximity.

---

## 2. Guess feedback row

Each submitted guess returns the following feedback:

| Attribute | Feedback type |
|---|---|
| Car | Structural closeness |
| Manufacturer | Geographic categorical similarity |
| Production years | Ordered comparison |
| Vehicle class | Semantic categorical similarity |
| Body style | Set overlap |
| Engine family | Set overlap |
| Power | Ordered comparison |
| Drivetrain | Set overlap |

---

# 3. Car closeness

Car closeness represents how structurally close the guessed vehicle is to the target vehicle.

Only **vehicle identity hierarchy and lineage** affect this value.

Mechanical or descriptive similarities such as engine, drivetrain, body style, vehicle class, power, engine position, or designer do **not** affect car closeness.

## Closeness levels

The highest applicable level is used.

| Priority | Relationship | Feedback |
|---:|---|---|
| 1 | Same exact guessable entity | **Match** |
| 2 | Same Variant | **Very close** |
| 3 | Direct predecessor/successor Variant | **Close** |
| 4 | Same Model | **Related** |
| 5 | Same Manufacturer | **Far** |
| 6 | Different Manufacturer and no stronger lineage relation | **Cold** |

Conceptually:

```text
Match
  ↓
Very close
  ↓
Close
  ↓
Related
  ↓
Far
  ↓
Cold
```

### Example

Target:

```text
BMW 3 Series E46 330i
```

Possible guesses:

```text
BMW 3 Series E46 325i
→ Very close
```

```text
BMW 3 Series E36 328i
→ Close if E36 and E46 are direct predecessor/successor Variants
```

```text
BMW 3 Series E30 325i
→ Related if it shares the Model but is not a direct predecessor/successor
```

```text
BMW 5 Series E39 530i
→ Far
```

```text
Toyota Supra A80
→ Cold
```

### Successor/predecessor relationships

A direct Variant lineage relation can upgrade structural proximity.

For example:

```text
E9 → E24
```

may be considered **Close** even if the vehicles do not share a Model.

Successor/predecessor direction should **not** be used to tell the player whether the target is newer or older.

That information belongs exclusively to the production-year feedback.

---

# 4. Manufacturer

Manufacturer feedback uses manually maintained manufacturer-origin metadata.

Example metadata:

```text
BMW         → Germany → Europe
Ferrari     → Italy   → Europe
Lamborghini → Italy   → Europe
Toyota      → Japan   → Asia
```

Manufacturer **origin** is used, not current corporate ownership.

## Feedback

| Relationship | Color |
|---|---|
| Same manufacturer | Green |
| Different manufacturer, same country | Yellow |
| Different country, same continent | Orange |
| Different continent | Black |

Example with Ferrari as the target:

```text
Ferrari     → Green
Lamborghini → Yellow
BMW         → Orange
Toyota      → Black
```

---

# 5. Production years

Production years use the Variant production range currently available in canonical JSON v1.

Both values are compared independently:

```text
production_start — production_end
```

## Start year

| Comparison | Feedback |
|---|---|
| Same start year | Green |
| Target starts later | ↑ |
| Target starts earlier | ↓ |

## End year

| Comparison | Feedback |
|---|---|
| Same end year | Green |
| Target ends later | ↑ |
| Target ends earlier | ↓ |

Example:

Target:

```text
1998–2006
```

Guess:

```text
1995–2009
```

Feedback:

```text
1995 ↑ — 2009 ↓
```

The target therefore started later but ended earlier.

Arrow semantics should remain consistent throughout Cardle:

```text
↑ = target value is higher / later
↓ = target value is lower / earlier
```

---

# 6. Vehicle class

Vehicle class uses a manually maintained game-specific similarity map.

It is not intended to be a formal automotive ontology.

## Feedback

| Relationship | Color |
|---|---|
| Exact same class | Green |
| Closely related class | Yellow |
| Same broad class family | Orange |
| Not meaningfully related | Black |

If either vehicle has multiple classes, compare every guessed class against every target class and return the **best matching level**.

Example:

Target:

```text
Grand tourer
Executive car
```

Guess:

```text
Executive car
```

Result:

```text
Green
```

because at least one exact class match exists.

The current canonical class vocabulary contains:

```text
Subcompact luxury crossover SUV
Compact luxury crossover SUV
Mid-size luxury crossover SUV
Full-size luxury car
Subcompact executive car
Compact executive car
Small family car
Mid-size car
Executive car
Luxury car
Grand tourer
Sports car
City car
Roadster
```

The exact Yellow/Orange class-pair mapping should live in the game-logic layer rather than the canonicalization layer.

---

# 7. Body style

Body style is treated as a set.

Examples:

```text
{Sedan, Coupe, Convertible, Wagon}
```

or:

```text
{Coupe}
```

## Feedback

| Comparison | Color |
|---|---|
| Exact same body-style set | Green |
| At least one body style overlaps, but sets differ | Yellow |
| No overlap | Black |

Example:

```text
Guess:  {Sedan, Coupe, Convertible, Wagon}
Target: {Coupe}
```

Result:

```text
Yellow
```

because the sets overlap but are not identical.

Order does not matter.

Unknown or missing data should not count as a match.

---

# 8. Engine family

Engine family is also treated as a set because a Version may be associated with multiple engine families.

## Feedback

| Comparison | Color |
|---|---|
| Exact same engine-family set | Green |
| At least one engine family overlaps, but sets differ | Yellow |
| No overlap | Black |

Example:

```text
Guess:  {M52, M54}
Target: {M54}
```

Result:

```text
Yellow
```

No extra similarity should be inferred merely because engines share an architecture, cylinder count, manufacturer, or other mechanical characteristic.

---

# 9. Power

Power is an ordered numerical clue.

## Feedback

| Comparison | Feedback |
|---|---|
| Same power | Green |
| Target has more power | ↑ |
| Target has less power | ↓ |

Example:

```text
Guess:  189 hp
Target: 228 hp
```

Result:

```text
189 hp ↑
```

No additional color scale is needed for how numerically close two power values are.

---

# 10. Drivetrain

Drivetrain is treated as a set.

Examples may include:

```text
{RWD}
```

or:

```text
{RWD, AWD}
```

## Feedback

| Comparison | Color |
|---|---|
| Exact same drivetrain set | Green |
| At least one drivetrain overlaps, but sets differ | Yellow |
| No overlap | Black |

Example:

```text
Guess:  {RWD, AWD}
Target: {AWD}
```

Result:

```text
Yellow
```

No semantic similarity is inferred between drivetrain types.

For example, RWD should not receive partial credit against AWD merely because they may be considered mechanically more similar than FWD.

---

# 11. Attributes excluded from car closeness

The following attributes may exist in the graph but do not affect structural car closeness:

```text
Engine family
Body style
Drivetrain
Engine position
Vehicle class
Power
Designer
Production year
```

These either have their own feedback column or are not currently part of the Wordle-style interface.

---

# 12. Design principle

Cardle separates two different ideas:

## Structural proximity

> How closely related are these two vehicle identities?

Derived from:

```text
Manufacturer
Model
Variant
Version
Predecessor/successor lineage
```

## Attribute similarity

> In what ways are the guessed car and target car similar or different?

Derived from:

```text
Manufacturer origin
Production years
Vehicle class
Body style
Engine family
Power
Drivetrain
```

This distinction prevents generic shared properties such as RWD, front-engine layout, or a shared engine family from making two otherwise unrelated cars appear structurally close.

---

## Status

**Game feedback specification v1: frozen for the BMW prototype.**

The next implementation stage is to build the query/game-logic layer that returns this comparison data for a guessed vehicle and a target vehicle.
