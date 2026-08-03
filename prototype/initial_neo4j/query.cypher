// 1. Show BMW model hierarchy
MATCH (m:Manufacturer {name: "BMW"})-[:PRODUCES]->(model:Model)
OPTIONAL MATCH (model)-[:HAS_VARIANT]->(variant:Variant)
OPTIONAL MATCH (variant)-[:HAS_VERSION]->(version:Version)
RETURN m, model, variant, version;


// 2. Find shortest path between 5 Series and 6 Series
MATCH
  (a:Model {name: "5 Series"}),
  (b:Model {name: "6 Series"})
MATCH p = shortestPath((a)-[*..10]-(b))
RETURN p;


// 3. Find versions sharing an engine
MATCH (var1:Variant)-[:HAS_VERSION]->(v1:Version)-[:USES_ENGINE]->(e:Engine)<-[:USES_ENGINE]-(v2:Version)<-[:HAS_VERSION]-(var2:Variant)
WHERE v1 <> v2
RETURN var1, v1, e, v2, var2;


// 4. Show successor chain
MATCH p = (v:Variant)-[:SUCCEEDED_BY*1..]->(next:Variant)
RETURN p;


// 5. Find cars designed by the same person
MATCH (v1:Variant)-[:DESIGNED_BY]->(d:Designer)<-[:DESIGNED_BY]-(v2:Variant)
WHERE v1 <> v2
RETURN v1, d, v2;
