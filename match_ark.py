'''
SCRIPT 2 POUR ALIGNEMENT DE L'INDEXATION BnF-RAMEAU DES NOTICES DE FONDS COLLEX DU CCFR SUR IDREF
###############
@date: 25 mars 2026
@author: Anne Bugner (BULAC)
@license: Etalab Open License 2.0
###############

OPÉRATIONS :
- Pour chaque élément indexé avec Rameau BnF (@source="BnF") : récupération de l'identifiant ark (@authfilenumber)
- Interrogation de data.bnf pour récupération du PPN de la notice IDRef liée
- Si succès, intégration du PPN et de la forme normalisée IdRef dans l'élément ; enregistrement du fichier xml-ead modifié
'''
# Pour traitement fichiers xml
from lxml import etree as ET
# Pour requêtage SPARQL de data.idref
from SPARQLWrapper import SPARQLWrapper, JSON

# Pour ouvrir un par un les fichiers xml téléchargés
import os.path
from glob import iglob

# Et pour garder traces d'éventuels indices Rameau sans correspondance dans IDRef
import csv

def main():
    
    path = "./Dump_xmlead"
    extension = "*.xml" 
    
    indices_absents_idref = []
    
    # Compteurs
    script_counter = 0
    elements_réindexés_bnf = []
    elements_corriges_idref = []
    erreurs_http = []
    
    # Ouverture fichiers
    for ead in iglob(os.path.join(path, extension)):
        xml_parser = ET.XMLParser(remove_blank_text=True)
        tree = ET.parse(ead, xml_parser)
        notice = tree.getroot()
        
        # Identification du fichier source et du producteur de la notice
        filename = informations_generales_fonds(ET.XPath("//eadid"), notice)

        # Correction des mentions d'IdRef erronées en @source
        fix_idref_sourcing(notice, filename, elements_corriges_idref)
        
        # Fonction centrale de réindexation
        reindexation(notice, '//*[@source="BnF"]', indices_absents_idref, filename, elements_réindexés_bnf)
        
        ### Enregistrer l'arborescence modifiée dans un nouveau fichier 
        make_xml(notice, filename) 
        ### Visualiser la progression du script
        script_counter += 1
        print(f"Fichier : {script_counter}/1243", end='\r') # Remplacer "1243" par le nombre total de fichiers dans notices_collex, s'il a changé
    
    if indices_absents_idref != []:
        with open("databnf_sans_idref.csv", mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, delimiter='\t')
            writer.writerow(["Nom du fichier source", "Provenance", "Nom du fonds", "URI index", "Label"])
            writer.writerows(indices_absents_idref)
        print(f"{len(indices_absents_idref} éléments catalogués dans data.bnf n'ont pas l'air d'avoir de lien vers IdRef !")  
        
    if erreurs_http != []:
        with open("erreurs_requetes_databnf.csv", mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, delimiter='\t')
            writer.writerows(erreurs_http)    
        print(f"{len(erreurs_http)} identifiants ARK ont renvoyé une erreur de requête sur data.bnf")
    
    print("")
    print(f"Nombre d'éléments @source='BnF' réindexés avec succès : {len(elements_réindexés_bnf)}")
    print(f"Nombre de mentions 'idref' baroques corrigées : {len(elements_corriges_idref)}")
    print(f"Nombre d'éléments @source='BnF' laissés tels quels : {len(indices_absents_idref)}")
    
def fix_idref_sourcing(notice, filename, elements_corriges_idref):
    indexes = notice.xpath("//*[@source='Sudoc' or @source='SUDOC' or @source='idRef' or @source='idref' or @source='Idref']")
    if indexes != []:
        for index in indexes:
            index.set('source', 'IdRef')
            ppn = index.get("authfilenumber") 
            if len(ppn) == 9:
                ppn = "https://www.idref.fr/" + ppn
                index.set('authfilenumber', ppn)
            else:
                ppn = ppn.replace("http:", "https:") 
            index.set('authfilenumber', ppn)   
            elements_corriges_idref.append(ppn)    
    return notice, elements_corriges_idref    

def reindexation(notice, expression, indices_absents_idref, filename, elements_réindexés_bnf):
    
    ### Chercher les indexations BnF
    elements_index_BnF = notice.xpath(expression)
    if elements_index_BnF != []:
    
        for element in elements_index_BnF:
            ## Récupération de l'ark
            ark = element.get('authfilenumber').strip() # On est pas à l'abri de trailing spaces inopinés

            # Vérifier qu'on ne se trouve pas en présence d'erreurs qui inscrivent ensemble @source="BnF" et @authfilenumber = PPN IdRef
            if "www.idref.fr/" in ark:
                element.set("source", "IdRef")
                ppn_idref = ark.replace("http:", "https:")
                element.set("authfilenumber", ppn_idref)
            elif "http://ark.bnf.fr/" in ark:
                uri_ark = ark.replace("http://ark.bnf.fr/", "http://data.bnf.fr/")    
            elif "data.bnf.fr" in ark:
                uri_ark = ark  
            else:
                uri_ark = "http://data.bnf.fr/" + ark

                ### Récupération de la notice dans data.bnf

                sparql_endpoint = "https://data.bnf.fr/sparql"

                sparql_query = f"""
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                SELECT ?idrefUri
                WHERE {{
                <{uri_ark}> skos:exactMatch|skos:closeMatch ?idrefUri .
                FILTER(STRSTARTS(STR(?idrefUri), "http://www.idref.fr/"))
                }}
                """
                sparql = SPARQLWrapper(sparql_endpoint)
                sparql.setQuery(sparql_query)
                sparql.setReturnFormat(JSON)

                try:
                    result = sparql.query().convert()
                    
                    if result["results"]["bindings"]:
                            
                        uri_idref = result["results"]["bindings"][0]["idrefUri"]["value"]
                        ## Nettoyage valeur
                        ppn_idref = uri_idref.strip("/id")
                        ppn_idref = ppn_idref.replace("http:", "https:")
                            
                        ### Ajout du résultat dans l'élément d'origine
                        element.set("authfilenumber", ppn_idref)
                        element.set("source", "IdRef")
                        elements_réindexés_bnf.append(uri_idref)
                    # Traitement des index absents d'IDRef (ex : Hanoi, dont la notice IDRef 027291502 est associée à ark:/12148/cb15292667g, et non pas ark:/12148/cb11936556x, choisi par CollEx)
                    else:
                        # Infos tableur de suivi : nom du fichier, ark concerné, label, nom du fonds, nom établissement
                        nom_fonds = informations_generales_fonds(ET.XPath("//unittitle"), notice)
                        provenance = informations_generales_fonds(ET.XPath("//repository/corpname"), notice)
                        label = element.get("normal")
                        if label is None:
                            label = element.text
                        indices_absents_idref.append([filename, provenance, nom_fonds, uri_ark, label])
                except:
                    erreurs_http.append([filename, uri_ark])
                    continue
                           
    return notice, indices_absents_idref, elements_réindexés_bnf    

def informations_generales_fonds(XPath, notice):
    find_info = XPath(notice)
    information = find_info[0].text
    return information

def make_xml(notice, filename):
    with open('Dump_xmlead/' + filename, "w", encoding="utf-8") as f:
        ccfr_new = f.write(ET.tostring(notice, xml_declaration=True, doctype='<!DOCTYPE ead PUBLIC "+//ISBN 1-931666-00-8//DTD ead.dtd (Encoded Archival Description (EAD) Version 2002)//EN" "ead.dtd">', pretty_print=True, encoding='utf-8').decode('utf-8')) 

main()
