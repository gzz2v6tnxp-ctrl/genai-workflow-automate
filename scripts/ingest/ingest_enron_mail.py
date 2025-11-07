import email
from email.message import Message
from email.policy import default            
from pathlib import Path
from typing import List, Optional

from langchain_core.documents import Document

def get_email_body(msg: Message) -> str:
    """
    Extrait le corps du message en texte brut d'un objet email.
    Gère les messages multipart et les différents types de contenu.
    """
    body = ""
    # On itère sur toutes les parties du message.
    for part in msg.walk():
        # Obtenir le type de contenu de la partie
        content_type = part.get_content_type()
        
        # Vérifier si la partie est un attachement (pièce jointe)
        # On évite de traiter le texte des pièces jointes comme le corps du message
        content_disposition = str(part.get("Content-Disposition"))
        if "attachment" in content_disposition:
            continue

        # Traiter les parties en texte brut
        if content_type == "text/plain":
            try:
                # Récupérer la charge utile (payload) décodée en octets
                payload = part.get_payload(decode=True)
                
                # S'assurer que le payload est bien des octets avant de le décoder
                if isinstance(payload, bytes):
                    # Tenter de décoder en utilisant le charset spécifié, ou par défaut en utf-8
                    charset = part.get_content_charset() or 'utf-8'
                    return payload.decode(charset, errors='ignore')
            except Exception:
                # Gérer les erreurs de décodage silencieusement
                continue

    return body

def load_enron_docs(limit: Optional[int] = None) -> List[Document]:
    """
    Charge les emails du dataset Enron.

    Args:
        limit: Le nombre maximum d'emails à charger.

    Returns:
        Une liste d'objets Document.
    """
    data_dir = Path(__file__).parent.parent.parent / "data" / "enron_mail_20150507" / "maildir"
    
    if not data_dir.exists():
        raise FileNotFoundError(f"Le répertoire de données Enron n'a pas été trouvé à l'emplacement : {data_dir}")

    # Utiliser glob pour trouver tous les fichiers (les emails n'ont pas d'extension)
    email_files = [f for f in data_dir.glob("**/*") if f.is_file()]

    docs = []
    count = 0
    for file_path in email_files:
        if limit and count >= limit:
            break
        
        try:
            with open(file_path, "r", encoding="latin-1") as f:
                msg_text = f.read()
            
            msg = email.message_from_string(msg_text, policy=default)
            
            subject = msg.get("Subject", "")
            body = get_email_body(msg)

            # Ignorer les emails sans corps de message
            if not body or not body.strip():
                continue

            page_content = f"Subject: {subject}\n\n{body}"
            
            metadata = {
                "id": msg.get("Message-ID"),
                "subject": subject,
                "from": msg.get("From"),
                "to": msg.get("To"),
                "date": msg.get("Date"),
                "file_path": str(file_path.relative_to(data_dir)),
                "source": "enron",
                "lang": "en"
            }
            
            doc = Document(page_content=page_content, metadata=metadata)
            docs.append(doc)
            count += 1

        except Exception as e:
            # Ignorer les fichiers qui ne peuvent pas être parsés
            # print(f"Erreur lors du traitement du fichier {file_path}: {e}")
            continue
            
    return docs

# if __name__ == "__main__":
#     # Ceci est un exemple pour tester le chargement des documents
#     try:
#         documents = load_enron_docs(limit=20)
#         print(f"Nombre de documents Enron chargés : {len(documents)}")
#         if documents:
#             print("\nExemple de premier document chargé :")
#             print("---")
#             print(documents[0].page_content)
#             print("---")
#             print(f"Métadonnées: {documents[0].metadata}")
#     except FileNotFoundError as e:
#         print(e)
