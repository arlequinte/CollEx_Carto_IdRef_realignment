# CollEx_Carto_IdRef_realignment
==============================

Context : Cartographie – CollEx-Persée Project

Python scripts to apply to the XML-EAD Dump of the [CCFR-Répertoire de fonds](https://ccfr.bnf.fr/portailccfr/jsp/public/index.jsp?action=public_formsearch_fonds) catalog to investigate whether the [IdRef](https://www.idref.fr/autorites.jsp) referential is being called upon while indexing subjects, people, collectivities and places. First script narrows down the dump to the "Fonds CollEx" records. Second one checks up indexing. If the BnF Rameau system is being used instead of IdRef, retrieves the IdRef identifier from the [data.bnf](https://data.bnf.fr/sparql/) SPARQL endpoint. Third one looks for exact match in [data.idref](https://data.idref.fr/sparql) on concept labels, if no external reference has been provided at all. Last one checks up W3C syntax for dates.

Those scripts use Python 3 with lxml and SPARQLWrapper.
Sample data provided by Bnf on March, 2026
