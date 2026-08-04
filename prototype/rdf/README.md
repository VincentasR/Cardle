# RDF/SHACL step of the pipeline

So, this is the part where RDF gets generated and validated by SHACL. 

# What is not in this prototype/what is still to be done

Even though I got the barebones working I still need to decide:
-Which entities exist
-Which values are reusable nodes
-Which values are literals
-Which fields are required
-Which identifiers stay stable
-Which entities need to be linked to external sources like DBpedia

Another thing to be decided is how rich the RDF is going to be: is it going to display multiple values when multiple sources disagree? What kind of domains, ranges and other things need to be used (and which of these actually make sense in this project). 