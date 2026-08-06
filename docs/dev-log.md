
# Development Log

## 2026-08-06

### Goals 
- Try to finish the whole pipline for at least all BMW wikipedia cars.

### Progress
- Got 80% of the requiret instances down (so quite good).

### Decisions
- Decided to go implement a unique "link scraper" for every car manufacturer and try to make a generic scraper for a vehicle.

### Next Steps
- Finish scraping the data, start making ontology.

## 2026-08-04

### Goals
- Build at least some part of the proper dataset.

### Progress
- Made a scraper for wikipedia (still not finished).

### Decisions
- Finding proper datasets was way harder than I thought, so I had to go with wikipedia. Wikipedia contains all the data, however, the formating is not the same everywhere so it makes it quite hard to scrape and use. 
- Ditched all the other datasets, maybe will use them to fact check the one that I make from wikipedia.
- Decided to not code all the extraction for all the possible variants, but build the extraction pipeline gradualy.

### Next steps
- Would really like to get the game running by Friday evening, so I decided to stick with BMW 6 series while extracting, so I can quickly check if my methods even work and then proceed with everything else. 
- Finishing extracting data, then polishing the ontology, then the whole JSON -> RDF -> SHACL -> Neo4j pipeline.
- Making at least a simple UI for the game so it can be tested (not for tomorrow, probably for Thursday),

## 2026-08-03

### Goals

- Build an initial prototype of an ontology.
- Refine hierarchy and.
- Establish minimum requirements for a cannonical/playable car.

### Progress
- Designed high level architecture:
-- Source extraction (structured, unstructured, and LLM assisted).
-- Entity resolution and cannonization.
-- RDF representation using a custom ontology.
-- SHACL validation.
- Researched potential automotive data sources and identified several promising datasets for future evaluation and integration.
- Started writing this journal (to better track my progress).

### Decisions
- Decided to use rdflib for working with rdf in python and pyshacl for SHACL validation.
- Decided to use .json as an input source
- Decided on the whole data aquiring pipeline (description will be in the README file)


### Next steps
- Finalize the SHACL validation and decide what kind of things and relationships will be represented in the ontology.
- What kind of information needs to get through to this current step (how to format my .json file).
- Finding more and better sources.

## 2026-08-01

### Goals
- Build an initial prototype of the Cardle knowledge graph.
- Evaluate suitable database technologies.

### Progress
- Created the first property graph prototype in Neo4j.
- Modeled the initial entities:
  - Manufacturer
  - Model
  - Variant
  - Version
- Added example data using several BMW models to validate the structure.

### Decisions
- Chose Neo4j as the graph database.
- Decided to use the Property Graph model instead of RDF for the game backend because:
  - Cypher is expressive for traversing relationships.
  - The graph structure naturally represents successor/predecessor and other vehicle relationships.
  - Neo4j has excellent visualization and tooling for development.
- RDF may still be used later as an intermediate representation for integrating external data sources.

### Challenges
- Determining the correct level of granularity (generation vs. variant vs. version).
- Avoiding duplicate entities when importing data from multiple sources.

### Next Steps
- Finalize the canonical graph schema.
- Define uniqueness constraints.

## 2026-07-29
Started working on the idea after playing wordle
