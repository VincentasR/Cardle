# Cardle

Cardle is a daily car guessing game built around an automotive knowledge graph. The game is inspired by Wordle, with similar daily guessing mechanics.

Players discover one vehicle per day. Discovered vehicles are added to a persistent visual graph, where relationships such as shared engines, designers, model lineage, body styles, and drivetrains gradually reveal the structure of the automotive world.

## Current stage

The project has moved from manual graph prototyping to an automated data integration pipeline.

Wikipedia vehicle data is scraped into raw JSON and transformed into a canonical automotive schema containing manufacturers, models, variants, versions, engines, body styles, drivetrains, designers, production periods, and vehicle relationships.

The current BMW dataset is used as the first complete prototype. The next step is importing the canonical data into Neo4j and building the playable Cardle game on top of the resulting knowledge graph.

Future work includes supporting additional manufacturers, handling less structured sources, and experimenting with lightweight LLM-assisted information extraction.