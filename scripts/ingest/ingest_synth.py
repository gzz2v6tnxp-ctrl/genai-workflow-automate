import json
from pathlib import Path
from typing import List

from langchain_core.documents import Document

def load_synth_docs() -> List[Document]:
    """Charge les documents synthétiques à partir du fichier JSONL."""
    file_path = Path(__file__).parent.parent.parent / "data" / "synth" / "synth_docs.jsonl"
    docs = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            
            # Le contenu principal du document sera le sujet et le corps
            page_content = f"{data['subject']}\n\n{data['body']}"
            
            # Préparer les métadonnées
            metadata = data.get("metadata", {})
            metadata["id"] = data.get("id")
            metadata["lang"] = data.get("lang")
            metadata["type"] = data.get("type")
            metadata["source"] = "synth"
            
            # Créer l'objet Document
            doc = Document(page_content=page_content, metadata=metadata)
            docs.append(doc)
            
    return docs

# if __name__ == "__main__":
#     # Ceci est un exemple pour tester le chargement des documents
#     documents = load_synth_docs()
#     print(f"Nombre de documents chargés : {len(documents)}")
#     if documents:
#         print("\nExemple de premier document :")
#         print(documents[0])