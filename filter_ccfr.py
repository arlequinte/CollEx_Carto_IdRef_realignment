'''
SCRIPT 1 POUR SÉLECTIONNER LES NOTICES DE FONDS COLLEX DANS UN DUMP DE NOTICES DU CCFR
###############
@date: 25 mars 2026
@author: Anne Bugner (BULAC)
@license: Etalab Open License 2.0
###############
OPÉRATION :
Se contente d'ouvrir un dossier rempli de fichiers xml-ead, et de copier ceux de type "Fonds CollEx" dans un autre dossier
'''

# Pour traitement fichiers xml
from lxml import etree as ET
# Pour ouvrir un par un les fichiers xml téléchargés
import os.path
from glob import iglob

def main():
    # Chemin vers le dossier local où le dump de fichiers xml a été enregistré et dézippé
    path = "./Dump_mars2026"
    extension = "*.xml" 
    
    # Liste d'atterrisage
    notices_collex = []

    # Ouverture et traitement de chaque fichier xml-ead
    for ead in iglob(os.path.join(path, extension)):
        xml_parser = ET.XMLParser(remove_blank_text=True)
        tree = ET.parse(ead, xml_parser)
        notice = tree.getroot()

        ### Sélection des fichiers traitant de fonds CollEx
        find_types_fonds = ET.XPath('//genreform[@type="type de fonds"]')
        types_fonds = find_types_fonds(notice)
        for type_fonds in types_fonds:
            if type_fonds.text == "Fonds CollEx":
                if notice not in notices_collex:
                    filename = notice.find("./eadheader/eadid")
                    filename = filename.text
                    notices_collex.append(notice)
                    # Copie du fichier dans dossier indépendant, si retenu
                    copy_xml(notice, filename)
    print("Total fichiers créés : " + str(len(notices_collex)))                    
      
def copy_xml(notice, filename):
    with open('notices_collex/' + filename, "w", encoding="utf-8") as f:
        ccfr_new = f.write(ET.tostring(notice, xml_declaration=True, doctype='<!DOCTYPE ead PUBLIC "+//ISBN 1-931666-00-8//DTD ead.dtd (Encoded Archival Description (EAD) Version 2002)//EN" "ead.dtd">', pretty_print=True, encoding='utf-8').decode('utf-8')) 
       
                    
main()                    
