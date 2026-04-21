'''
SCRIPT ANNEXE DE VÉRIFICATION DE LA SYNTAXE DES DATES DANS LES NOTICES COLLEX DU CCFR
###############
@date: 31 mars 2026
@author: Anne Bugner (BULAC)
@license: Etalab Open License 2.0
###############

OPÉRATIONS :
- Pour chaque élément <unitdate>, vérification de la présence d'un attribut @normal ; récupération des dates qui l'ont omis
- Vérification de la syntaxe YYYY | YYYY/YYYY | YYYY-MM-DD | YYYY-MM-DD/YYYY-MM-DD de la valeur de cet attribut @normal
- Si l'on se trouve spécifiquement dans le cas d'une date en YYYY-YYYY : remplacement du tiret par un slash
- Liste de l'ensemble des dates à reprendre manuellement
'''

# Pour traitement fichiers xml
from lxml import etree as ET

# Pour ouvrir un par un les fichiers xml téléchargés
import os.path
from glob import iglob

import re
import csv

def main():
    
    path = "./Dump_xmlead"
    extension = "*.xml"
    
    dates_sans_normal = []
    dates_incorrectes_retouchées = []
    dates_incorrectes_non_retouchées = []
    total_dates = []
    
    for ead in iglob(os.path.join(path, extension)):
        xml_parser = ET.XMLParser(remove_blank_text=True)
        tree = ET.parse(ead, xml_parser)
        notice = tree.getroot()
        
        filename = informations_generales_fonds(ET.XPath("//eadid"), notice)
        nom_fonds = informations_generales_fonds(ET.XPath("//unittitle"), notice)
        provenance = informations_generales_fonds(ET.XPath("//repository/corpname"), notice)
        
        find_dates = ET.XPath("//unitdate")
        dates = find_dates(notice)
        
        for date in dates:
            total_dates.append(date)
            
            att_normal = date.get("normal")
            att_type = date.get("type")
            if att_normal is not None and att_normal != "":
                
                # Vérifier que la date suit bien un pattern YYYY ou YYYY/YYYY ; enregistrer les incorrectes  
                # Matcher les dates en "YYYY, YYYY/YYYY, YYYYMMDD/YYYYMMDD, etc"
                match_date = re.search(r"^[0-9]{4,}($|(\/[0-9]{4,}))", att_normal)
                # ... Qui peuvent aussi être des YYYY-MM-DD/YYYY-MM-DD
                if match_date is None:
                    match_date2 = re.search(r"\d{4}\-\d{2}\-\d{2}\/\d{4}\-\d{2}\-\d{2}", att_normal)
                    if match_date2 is None:
                        # Corriger les dates en YYYY-YYYY
                        match_date3 = re.search(r"\d{4}\-\d{4}", att_normal)
                        if match_date3:
                            att_normal = att_normal.replace('-', '/')
                            dates_incorrectes_retouchées.append(att_normal)
                        # Abandonner les autres modifs
                        else:    
                            dates_incorrectes_non_retouchées.append([filename, nom_fonds, provenance, date.text, att_normal])
                            
            # S'il n'y a pas d'attribut @normal    
            else:  
                dates_sans_normal.append([filename, nom_fonds, provenance, date.text, "Pas d'attribut @normal"])
                
        # Réécrire xml
        with open('Dates_corrigees/' + filename, "w", encoding="utf-8") as f:
            ccfr_new = f.write(ET.tostring(notice, xml_declaration=True, doctype='<!DOCTYPE ead PUBLIC "+//ISBN 1-931666-00-8//DTD ead.dtd (Encoded Archival Description (EAD) Version 2002)//EN" "ead.dtd">', pretty_print=True, encoding='utf-8').decode('utf-8'))          
    
    print("Vérif terminée.")
    # Garder l'oeil sur les dates à réécrire           
    if len(dates_incorrectes_non_retouchées) > 0 or dates_sans_normal > 0:
        make_csv_dates_incorrectes(dates_incorrectes_non_retouchées, dates_sans_normal) 
        print("CSV des dates à retoucher OK")  
    if len(dates_incorrectes_non_retouchées) > 0 :
        print(f"Nombre de dates à reprendre : {len(dates_incorrectes_non_retouchées)}")   
    if len(dates_sans_normal) > 0:
        print(f"Nombre de dates sans attribut @normal : {len(dates_sans_normal)}")     
    if len(dates_incorrectes_retouchées) > 0:
        print(f"Nombre de dates retouchées : {len(dates_incorrectes_retouchées)}")          
             
    print(len(total_dates))        

def informations_generales_fonds(XPath, notice):
    find_info = XPath(notice)
    information = find_info[0].text
    return information

def make_csv_dates_incorrectes(dates_incorrectes_non_retouchées, dates_sans_normal):
    with open("dates_incorrectes_non_retouchées.csv", mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter='\t')
        writer.writerow(["Nom du fichier source", "Nom du fonds", "Provenance", "Date affichée", "Date normalisée"])
        writer.writerows(dates_incorrectes_non_retouchées)
        writer.writerows(dates_sans_normal)
        return csvfile
        
main()        
