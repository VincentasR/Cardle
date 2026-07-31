# Cardle

Cardle is a daily car guessing game built around an automotive knowledge graph. The game is inspired by Wordle, and the mechanics are quite similar. 

Players discover one vehicle per day. Discovered vehicles are added to a persistent visual graph, where relationships such as shared engines, designers, model lineage, and many more, gradualy reveal the structure of the automotive world.

## CUrrent stage

The project is currently in the knowledge-model prototyping phase.

The first prototype uses manually modeled BMW vehicles in Neo4j to explore: vehicle hierarchy, what kind of names/generations/trims/variants would be suited for the final game, versions, engines, body styles, drivertain, designers, successor relationships. 

The prototype will later be replaced by an automated integration pipeline combining RDF knowledge graphs, structured datasets and scraped web data.