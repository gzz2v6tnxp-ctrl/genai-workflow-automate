import sys
from pathlib import Path
import requests
from qdrant_client import QdrantClient

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from scripts import config


def create_snapshot(collection_name: str, output_dir: str = "./snapshots") -> str:
    """
    Crée un snapshot de la collection locale et le télécharge en fichier .snapshot.

    Returns:
        str: Chemin du fichier snapshot téléchargé
    """
    client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📸 Création du snapshot pour '{collection_name}'...")

    # 1) Créer le snapshot côté Qdrant local
    try:
        snapshot_info = client.create_snapshot(
            collection_name=collection_name,
            wait=True,  # attendre la fin de la création
        )
        # snapshot_info.name (nouveau client) ou snapshot_info["name"]
        snap_name = getattr(snapshot_info, "name", None) or snapshot_info["name"]
        print(f"✅ Snapshot créé : {snap_name}")
    except Exception as e:
        print(f"❌ Erreur création snapshot : {e}")
        return ""

    # 2) Télécharger le snapshot via HTTP (pas de client.download_snapshot)
    try:
        download_url = (
            f"http://{config.QDRANT_HOST}:{config.QDRANT_PORT}"
            f"/collections/{collection_name}/snapshots/{snap_name}"
        )
        local_path = out_dir / f"{collection_name}-{snap_name}"

        print(f"⬇️  Téléchargement du snapshot depuis {download_url}")
        resp = requests.get(download_url, stream=True)
        resp.raise_for_status()

        with open(local_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        size_mb = local_path.stat().st_size / 1024 / 1024
        print(f"� Snapshot téléchargé : {local_path.name} ({size_mb:.2f} MB)")

        return str(local_path)
    except Exception as e:
        print(f"❌ Erreur lors du téléchargement : {e}")
        return ""