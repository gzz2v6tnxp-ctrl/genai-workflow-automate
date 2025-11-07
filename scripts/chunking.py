from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List

def chunk_documents(
    documents: List[Document], 
    chunk_size: int = 600,  # 384 tokens ≈ 600 caractères pour all-mpnet-base-v2
    chunk_overlap: int = 100,
    min_chunk_size: int = 50  # Ne pas créer de chunks trop petits
) -> List[Document]:
    """
    Découpe intelligemment les documents longs pour éviter la truncation.
    
    Args:
        documents: Documents à découper
        chunk_size: Taille max en caractères (600 ≈ 384 tokens pour MPNet)
        chunk_overlap: Chevauchement entre chunks (préserve le contexte)
        min_chunk_size: Taille minimale d'un chunk (évite les fragments)
    
    Returns:
        Liste de documents découpés avec métadonnées préservées
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", "! ", "? ", ", ", " ", ""],
    )
    
    chunked_docs = []
    stats = {"kept_whole": 0, "chunked": 0, "total_chunks": 0}
    
    for doc in documents:
        if len(doc.page_content) <= chunk_size:
            # Document court : pas de chunking nécessaire
            chunked_docs.append(doc)
            stats["kept_whole"] += 1
        else:
            # Document long : découper en chunks
            chunks = text_splitter.split_text(doc.page_content)
            
            # Filtrer les chunks trop petits
            chunks = [c for c in chunks if len(c) >= min_chunk_size]
            
            for i, chunk in enumerate(chunks):
                chunk_metadata = doc.metadata.copy()
                chunk_metadata["chunk_index"] = i
                chunk_metadata["total_chunks"] = len(chunks)
                chunk_metadata["parent_doc_id"] = doc.metadata.get("id")
                chunk_metadata["is_chunked"] = True
                
                chunked_docs.append(
                    Document(page_content=chunk, metadata=chunk_metadata)
                )
            
            stats["chunked"] += 1
            stats["total_chunks"] += len(chunks)
    
    print(f"📄 Chunking Statistics:")
    print(f"   - Documents kept whole: {stats['kept_whole']}")
    print(f"   - Documents chunked: {stats['chunked']}")
    print(f"   - Total chunks created: {stats['total_chunks']}")
    print(f"   - Final count: {len(documents)} docs → {len(chunked_docs)} chunks")
    
    return chunked_docs
