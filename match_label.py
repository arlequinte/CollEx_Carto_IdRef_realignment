'''
SCRIPT 3 POUR ALIGNEMENT DE L'INDEXATION BnF-RAMEAU DES NOTICES DE FONDS COLLEX DU CCFR SUR IDREF
###############
@date: 31 mars 2026
@author: Anne Bugner (BULAC)
@license: Etalab Open License 2.0
###############

OPÉRATIONS :
- Pour chaque élément indexé restant (<subject>, <*name>) qui ne propose aucun rebond vers un référentiel externe : récupération du contenu textuel
- Nettoyage de cette valeur texte (suppression de l'indice Dewey le cas échéant)
- Requête dans data.idref à la recherche de la notice dont le label est *exactement* cette valeur texte
- Si succès, intégration du PPN et de la forme normalisée IdRef dans l'élément ; enregistrement du fichier xml-ead modifié
'''
# Pour traitement fichiers xml
from lxml import etree as ET
# Pour requêtage SPARQL de data.idref
from SPARQLWrapper import SPARQLWrapper, JSON

# Pour ouvrir un par un les fichiers xml téléchargés
import os.path
from glob import iglob

# Et pour les indices Rameau hors IDRef
import csv

# Pour le nettoyage des valeurs texte
import re

def main():
    
    path = "./Dump_xmlead"
    extension = "*.xml" 
    
    indices_absents_idref = []
    script_counter = 0
    elements_reindexés = []
    
    for ead in iglob(os.path.join(path, extension)):
        xml_parser = ET.XMLParser(remove_blank_text=True)
        tree = ET.parse(ead, xml_parser)
        notice = tree.getroot()
        
        filename = notice.find("./eadheader/eadid")
        filename = filename.text
        
        ## Réindexation <subject>
        reindexation(notice, "//subject[not(@source='IdRef')]", indices_absents_idref, filename, elements_reindexés)
        ## Réindexation <persname>
        reindexation(notice, "//persname[not(@source='IdRef')]", indices_absents_idref, filename, elements_reindexés) 
        ## Reindexation <corpname>
        reindexation(notice, "//corpname[not(@source='IdRef') and not(@source='Répertoire_des_Centres_de_Ressources')]", indices_absents_idref, filename, elements_reindexés)
        ## Réindexation <geogname>
        reindexation(notice, "//geogname[not(@source='IdRef')]", indices_absents_idref, filename, elements_reindexés) 
        ## Réindexation <famname>
        reindexation(notice, "//famname[not(@source='IdRef')]", indices_absents_idref, filename, elements_reindexés) 
        
        ### Enregistrer l'arborescence modifiée dans un nouveau fichier
        make_xml(notice, filename) 
        ### Visualiser la progression du script
        script_counter += 1
        print(f"Fichier : {script_counter}/1243", end='\r') # Remplacer "1243" par le nombre total de fichiers dans notices_collex, s'il a changé
    
    if indices_absents_idref != []:
        make_csv_indices_absents(indices_absents_idref)
        print(f"{len(indices_absents_idref} index n'ont pas pu être identifiés dans IdRef !")        
    
    print("")
    print(f"Nombre d'éléments réindexés avec succès : {len(elements_reindexés)}")
    print(f"Nombre d'éléments laissés tels quels : {len(indices_absents_idref)}")         

def reindexation(notice, xPath, indices_absents_idref, filename, elements_reindexés):
    
    ### Cibler les éléments d'indexation intéressants : ceux qui n'ont pas de rebond vers un référentiel externe
    elements_index_bruts = notice.xpath(xPath)
    if elements_index_bruts != []:
    
        for element in elements_index_bruts:

            #### Récupération de la forme nominale
            ## Nettoyer la valeur : supprimer les éventuels indices Dewey au début
            forme_nominale = element.get("normal")
            if forme_nominale is None:
                forme_nominale = element.text
            forme_nominale = forme_nominale.strip()
            forme_nominale = re.sub(r"(\d{3}(\.\d{1,3})?\s)(?=\w)", "", forme_nominale)

            ##### Requête sur data.idref
            sparql_endpoint = "https://data.idref.fr/sparql/"

            sparql_query = f"""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            select ?concept
            where {{
            ?concept skos:prefLabel "{forme_nominale}" .
            }}
            """
            sparql = SPARQLWrapper(sparql_endpoint)
            sparql.setQuery(sparql_query)
            sparql.setReturnFormat(JSON)
            ## Exécution de la requête
            try:
                result = sparql.query().convert()        
                if result["results"]["bindings"]:
                                    
                    uri_idref = result["results"]["bindings"][0]["concept"]["value"]
                    ## Nettoyage valeur
                    ppn_idref = uri_idref.strip("/id")
                    ppn_idref = ppn_idref.replace("http:", "https:")
                                    
                    ### Ajout du résultat dans l'élément d'indexation initial
                    element.set("authfilenumber", ppn_idref)
                    element.set("source", "IdRef")
                    element.set("normal", forme_nominale)
                    elements_reindexés.append(ppn_idref)
                else:
                    # Tableur de récupération des erreurs
                    valeur = element.get("normal")
                    if valeur is None:
                        valeur = element.text
                    liste_indices_absents(indices_absents_idref, notice, filename, element)
            except:
                liste_indices_absents(indices_absents_idref, notice, filename, element)

    return notice, indices_absents_idref, elements_reindexés                

def liste_indices_absents(indices_absents_idref, notice, filename, element):
    nom_fonds = informations_generales_fonds(ET.XPath("//unittitle"), notice)
    provenance = informations_generales_fonds(ET.XPath("//repository/corpname"), notice)
    label = element.get("normal")
    if label is None:
        label = element.text
    indices_absents_idref.append([filename, provenance, nom_fonds, label])    
    return indices_absents_idref

def informations_generales_fonds(XPath, notice):
    find_info = XPath(notice)
    information = find_info[0].text
    return information
                
def make_xml(notice, filename):
    with open('Dump_xmlead/' + filename, "w", encoding="utf-8") as f:
        ccfr_new = f.write(ET.tostring(notice, xml_declaration=True, doctype='<!DOCTYPE ead PUBLIC "+//ISBN 1-931666-00-8//DTD ead.dtd (Encoded Archival Description (EAD) Version 2002)//EN" "ead.dtd">', pretty_print=True, encoding='utf-8').decode('utf-8')) 

def make_csv_indices_absents(indices_absents_idref):
    with open("formes_nominales_à_créer_dans_idref.csv", mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter='\t')
        writer.writerow(["Nom du fichier source", "Établissement", "Nom du fonds", "Index"])
        writer.writerows(indices_absents_idref)
        return csvfile
main() 
