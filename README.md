![](pyTARQL-250.png)

# pyTARQL
Python implementation of [TARQL](https://tarql.github.io/), based on 
[RDFLib](https://github.com/RDFLib/rdflib).

```
usage: pytarql [-h] [-d DELIMITER | -t] [-p ESCAPECHAR]
               [--quotechar QUOTECHAR] [--dedup DEDUP] [--ntriples] [-H]
               query [input]

pyTARQL CSV to RDF converter (Table SPARQL).

positional arguments:
  query                 File containing a SPARQL query to be applied to an
                        input file
  input                 CSV to be processed, omit to use STDIN

optional arguments:
  -h, --help            show this help message and exit
  -d DELIMITER, --delimiter DELIMITER
                        Delimiting character of the input file
  -t, --tab             Input is tab-separated (TSV)
  -p ESCAPECHAR, --escapechar ESCAPECHAR
                        Escape character of the input file
  --quotechar QUOTECHAR
                        Quote character of the input file
  --dedup DEDUP         Window size in which to remove duplicate triples
  --ntriples            Emit N-Triples (default is turtle)
  -H, --no-header-row   Input file has no header row; use variable names ?a,
                        ?b, ...
```
