import pandas as pd
from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document

def load_cfpb_docs(limit: Optional[int] = None) -> List[Document]:
    """
    Charge les plaintes de consommateurs depuis le fichier CSV du CFPB.

    Args:
        limit: Le nombre maximum de documents à charger (pour le test).

    Returns:
        Une liste d'objets Document prêts pour l'embedding.
    """
    file_path = Path(__file__).parent.parent.parent / "data" / "complaints.csv" / "complaints.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Le fichier de données CFPB n'a pas été trouvé à l'emplacement : {file_path}")

    # Utiliser pandas pour une lecture efficace des gros fichiers CSV
    df = pd.read_csv(file_path, dtype=str, nrows=100)

    # Filtrer les lignes où la narration de la plainte est manquante
    df.dropna(subset=['Consumer complaint narrative'], inplace=True)

    # Appliquer la limite si elle est spécifiée
    if limit:
        df = df.head(limit)

    docs = []
    for index, row in df.iterrows():
        # Le contenu principal du document est la narration de la plainte
        page_content = row['Consumer complaint narrative']
        
        # Préparer les métadonnées
        metadata = {
            "id": row.get("Complaint ID"),
            "product": row.get("Product"),
            "sub_product": row.get("Sub-product"),
            "issue": row.get("Issue"),
            "sub_issue": row.get("Sub-issue"),
            "state_geo": row.get("State"),
            "company": row.get("Company"),
            "company_response": row.get("Company response to consumer"),
            "timely_response": row.get("Timely response?"),
            "consumer_consent": row.get("Consumer consent provided?"),
            "date_received": row.get("Date received"),
            "date_sent_to_company": row.get("Date sent to company"),
            "source": "cfpb",
            "lang": "en"
        }
        
        # Créer l'objet Document
        doc = Document(page_content=page_content, metadata=metadata)
        docs.append(doc)
            
    return docs

if __name__ == "__main__":
    # Ceci est un exemple pour tester le chargement des documents
    # On charge seulement 10 documents pour un test rapide
    try:
        documents = load_cfpb_docs(limit=10)
        print(f"Nombre de documents CFPB chargés : {len(documents)}")
        if documents:
            print("\nExemple de premier document :")
            print("---")
            print(f"Contenu (extrait): {documents[0].page_content[:250]}...")
            print("---")
            print(f"Métadonnées: {documents[0].metadata}")
    except FileNotFoundError as e:
        print(e)

