"""
COV-RAG: Retrieval-Augmented Generation avec Chain-of-Verification (CoVE)

Ce module implémente un système RAG robuste avec vérification des hallucinations
via le pattern CoVE (Chain-of-Verification).

Pipeline:
1. Récupération hybride (dense + MMR pour diversité)
2. Re-ranking des documents
3. Génération initiale avec ancrage strict
4. Extraction des affirmations vérifiables
5. Génération de questions de vérification
6. Vérification croisée avec les sources
7. Correction et génération finale

Auteur: GenAI Workflow Automation
"""

import sys
import re
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.schema import Document
from qdrant_client import QdrantClient
from qdrant_client import models as qdrant_models

from scripts import config


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class VerificationQuestion:
    """Question de vérification générée pour une affirmation."""
    question: str
    fact_to_verify: str
    source_required: bool = True
    category: str = "factual"  # factual, numerical, temporal, entity


@dataclass
class VerificationResult:
    """Résultat de vérification d'une affirmation."""
    original_claim: str
    is_verified: bool
    confidence: float
    evidence: str
    correction: Optional[str] = None
    source_ids: List[str] = field(default_factory=list)


@dataclass
class RAGResult:
    """Résultat complet du pipeline RAG + CoVE."""
    query: str
    answer: str
    initial_answer: Optional[str] = None
    sources: List[Dict[str, Any]] = field(default_factory=list)
    verifications: List[VerificationResult] = field(default_factory=list)
    confidence_score: float = 0.0
    hallucination_detected: bool = False
    corrections_made: int = 0
    processing_time_ms: float = 0.0
    language: str = "fr"


# ============================================================================
# COV-RAG RETRIEVER - Récupération Hybride
# ============================================================================

class COVRAGRetriever:
    """
    Système de récupération hybride pour COV-RAG.
    
    Combine:
    - Recherche vectorielle dense (similarité cosinus)
    - Recherche MMR (Maximum Marginal Relevance) pour la diversité
    - Re-ranking basé sur la pertinence
    """
    
    def __init__(
        self,
        collection_name: str = "demo_public",
        use_cloud: bool = True,
        top_k: int = 5,
        score_threshold: float = 0.35,
        diversity_factor: float = 0.3
    ):
        self.collection_name = collection_name
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.diversity_factor = diversity_factor
        
        # Client Qdrant
        if use_cloud:
            self.client = QdrantClient(
                url=config.QDRANT_CLOUD_URL,
                api_key=config.QDRANT_API_KEY,
            )
        else:
            self.client = QdrantClient(
                host=config.QDRANT_HOST,
                port=config.QDRANT_PORT
            )
        
        # Modèle d'embedding OpenAI
        self.embedding_model = OpenAIEmbeddings(
            model=config.DEFAULT_EMBEDDING_MODEL,
            api_key=config.OPENAI_API_KEY
        )
        
        print(f"✅ COVRAGRetriever initialisé - Collection: {collection_name}")
    
    def retrieve(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Récupération dense standard avec filtres optionnels.
        """
        try:
            query_vector = self.embedding_model.embed_query(query)
        except Exception as e:
            print(f"❌ Erreur embedding: {e}")
            return []
        
        # Construire les filtres Qdrant
        query_filter = self._build_filter(filters)
        
        # Recherche vectorielle
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=self.top_k,
            score_threshold=self.score_threshold
        )
        
        return self._convert_to_documents(results)
    
    def hybrid_retrieve(
        self, 
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Récupération hybride: dense + MMR pour diversité.
        
        Combine les résultats de la recherche dense avec MMR
        pour éviter la redondance et maximiser la couverture.
        """
        try:
            query_vector = self.embedding_model.embed_query(query)
        except Exception as e:
            print(f"❌ Erreur embedding: {e}")
            return []
        
        query_filter = self._build_filter(filters)
        
        # 1. Recherche dense standard
        dense_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=self.top_k,
            score_threshold=self.score_threshold
        )
        
        # 2. Recherche avec plus de candidats pour MMR
        extended_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=self.top_k * 3,
            score_threshold=self.score_threshold * 0.8
        )
        
        # 3. Appliquer MMR manuellement
        mmr_results = self._apply_mmr(
            query_vector=query_vector,
            candidates=extended_results,
            k=self.top_k,
            lambda_mult=1 - self.diversity_factor
        )
        
        # 4. Fusionner et dédupliquer
        merged = self._merge_and_deduplicate(dense_results, mmr_results)
        
        return self._convert_to_documents(merged[:self.top_k])
    
    def rerank(
        self, 
        query: str, 
        documents: List[Document],
        use_cross_encoder: bool = False
    ) -> List[Document]:
        """
        Re-classe les documents par pertinence.
        
        Utilise une combinaison de:
        - Similarité sémantique (embedding)
        - Overlap lexical (BM25-like)
        - Couverture des termes de la requête
        """
        if not documents:
            return []
        
        query_vector = self.embedding_model.embed_query(query)
        query_terms = set(re.findall(r'\w{3,}', query.lower()))
        
        scored_docs = []
        for doc in documents:
            # Score sémantique
            doc_vector = self.embedding_model.embed_query(doc.page_content[:1000])
            semantic_score = self._cosine_similarity(query_vector, doc_vector)
            
            # Score lexical (terme overlap)
            doc_terms = set(re.findall(r'\w{3,}', doc.page_content.lower()))
            lexical_score = len(query_terms & doc_terms) / max(len(query_terms), 1)
            
            # Score combiné (70% sémantique, 30% lexical)
            combined_score = 0.7 * semantic_score + 0.3 * lexical_score
            
            scored_docs.append((doc, combined_score))
        
        # Trier par score décroissant
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, _ in scored_docs]
    
    def _build_filter(self, filters: Optional[Dict[str, Any]]) -> Optional[qdrant_models.Filter]:
        """Construit un filtre Qdrant à partir d'un dictionnaire."""
        if not filters:
            return None
        
        must_conditions = []
        for key, value in filters.items():
            if isinstance(value, (list, tuple, set)):
                must_conditions.append(
                    qdrant_models.FieldCondition(
                        key=key,
                        match=qdrant_models.MatchAny(any=list(value))
                    )
                )
            else:
                must_conditions.append(
                    qdrant_models.FieldCondition(
                        key=key,
                        match=qdrant_models.MatchValue(value=value)
                    )
                )
        
        return qdrant_models.Filter(must=must_conditions) if must_conditions else None
    
    def _apply_mmr(
        self,
        query_vector: List[float],
        candidates: List,
        k: int,
        lambda_mult: float = 0.7
    ) -> List:
        """
        Applique Maximum Marginal Relevance pour diversifier les résultats.
        
        MMR = λ * sim(doc, query) - (1-λ) * max(sim(doc, selected))
        """
        if not candidates:
            return []
        
        import numpy as np
        
        selected = []
        remaining = list(candidates)
        
        while len(selected) < k and remaining:
            best_score = float('-inf')
            best_idx = 0
            
            for i, candidate in enumerate(remaining):
                # Similarité avec la requête
                relevance = candidate.score
                
                # Pénalité de redondance avec les documents sélectionnés
                redundancy = 0.0
                if selected:
                    # Calculer la similarité textuelle avec les sélectionnés
                    candidate_text = candidate.payload.get("page_content", "")[:500]
                    for sel in selected:
                        sel_text = sel.payload.get("page_content", "")[:500]
                        text_sim = self._text_similarity(candidate_text, sel_text)
                        redundancy = max(redundancy, text_sim)
                
                # Score MMR
                mmr_score = lambda_mult * relevance - (1 - lambda_mult) * redundancy
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i
            
            selected.append(remaining.pop(best_idx))
        
        return selected
    
    def _merge_and_deduplicate(self, list1: List, list2: List) -> List:
        """Fusionne deux listes de résultats en supprimant les doublons."""
        seen_ids = set()
        merged = []
        
        for item in list1 + list2:
            item_id = item.id
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                merged.append(item)
        
        # Trier par score
        merged.sort(key=lambda x: x.score, reverse=True)
        return merged
    
    def _convert_to_documents(self, results: List) -> List[Document]:
        """Convertit les résultats Qdrant en objets Document."""
        documents = []
        for hit in results:
            metadata = {k: v for k, v in hit.payload.items() if k != "page_content"}
            metadata["id"] = str(hit.id)
            metadata["score"] = hit.score
            
            doc = Document(
                page_content=hit.payload.get("page_content", ""),
                metadata=metadata
            )
            documents.append(doc)
        
        return documents
    
    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calcule la similarité cosinus entre deux vecteurs."""
        import numpy as np
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10))
    
    @staticmethod
    def _text_similarity(text1: str, text2: str) -> float:
        """Calcule la similarité textuelle (Jaccard) entre deux textes."""
        words1 = set(re.findall(r'\w{3,}', text1.lower()))
        words2 = set(re.findall(r'\w{3,}', text2.lower()))
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)


# ============================================================================
# CHAIN OF VERIFICATION (CoVE)
# ============================================================================

class ChainOfVerification:
    """
    Implémentation de Chain-of-Verification (CoVE) pour réduire les hallucinations.
    
    Pipeline CoVE:
    1. Extraire les affirmations vérifiables de la réponse
    2. Générer des questions de vérification pour chaque affirmation
    3. Répondre aux questions en utilisant uniquement les sources
    4. Comparer les réponses avec les affirmations originales
    5. Corriger les incohérences et générer la réponse finale
    
    Référence: "Chain-of-Verification Reduces Hallucination in Large Language Models"
    """
    
    def __init__(
        self,
        llm: ChatOpenAI,
        retriever: COVRAGRetriever,
        verification_threshold: float = 0.7,
        max_claims_to_verify: int = 5
    ):
        self.llm = llm
        self.retriever = retriever
        self.verification_threshold = verification_threshold
        self.max_claims_to_verify = max_claims_to_verify
        self._init_prompts()
    
    def _init_prompts(self):
        """Initialise les prompts pour chaque étape du pipeline CoVE."""
        
        # Prompt pour extraire les affirmations
        self.extract_claims_prompt = ChatPromptTemplate.from_messages([
            ("system", """Tu es un expert en analyse de texte. Extrais toutes les affirmations factuelles vérifiables de la réponse.

Pour chaque affirmation, identifie:
- Le fait précis énoncé
- La catégorie: "numerical" (chiffres, montants), "temporal" (dates), "entity" (noms, lieux), "factual" (autres faits)
- Si une source est nécessaire pour vérifier

IMPORTANT: Ne garde que les affirmations qui peuvent être vérifiées avec des sources.
Ignore les opinions, conseils généraux ou formulations vagues.

Retourne UNIQUEMENT un tableau JSON valide, sans texte avant ou après:
[
  {{"fact": "...", "category": "...", "source_required": true}},
  ...
]"""),
            ("human", "Réponse à analyser:\n{response}")
        ])
        
        # Prompt pour générer les questions de vérification
        self.generate_questions_prompt = ChatPromptTemplate.from_messages([
            ("system", """Pour chaque affirmation, génère une question de vérification précise et directe.
La question doit permettre de confirmer ou infirmer l'affirmation en consultant les sources.

Retourne UNIQUEMENT un tableau JSON valide:
[
  {{"question": "...", "fact_to_verify": "...", "category": "..."}},
  ...
]"""),
            ("human", "Affirmations à vérifier:\n{claims}")
        ])
        
        # Prompt pour vérifier une affirmation
        self.verify_claim_prompt = ChatPromptTemplate.from_messages([
            ("system", """Tu es un vérificateur de faits rigoureux. Vérifie si l'affirmation est correcte selon les sources fournies.

RÈGLES STRICTES:
1. Une affirmation est "verified" UNIQUEMENT si elle est explicitement supportée par les sources
2. Si l'information n'est pas dans les sources, is_verified = false
3. Pour les chiffres et dates, ils doivent correspondre exactement
4. Cite toujours l'evidence exacte des sources

Retourne UNIQUEMENT un objet JSON valide:
{{
  "is_verified": true/false,
  "confidence": 0.0-1.0,
  "evidence": "citation exacte de la source",
  "correction": "version correcte si l'affirmation est fausse, sinon null",
  "source_ids": ["id1", "id2"]
}}"""),
            ("human", """Affirmation à vérifier: {claim}
Question de vérification: {question}

Sources disponibles:
{sources}""")
        ])
        
        # Prompt pour générer la réponse corrigée
        self.correct_response_prompt = ChatPromptTemplate.from_messages([
            ("system", """Tu es un assistant expert. Génère une réponse corrigée en tenant compte des vérifications.

RÈGLES:
1. Conserve les parties de la réponse qui ont été vérifiées comme correctes
2. Corrige ou supprime les affirmations incorrectes
3. Ne rajoute PAS de nouvelles informations non présentes dans les sources
4. Maintiens un ton professionnel et naturel
5. Cite les sources quand c'est approprié

Si des corrections majeures sont nécessaires, reformule complètement la partie concernée."""),
            ("human", """Question originale: {query}

Réponse initiale:
{initial_response}

Résultats de vérification:
{verification_results}

Sources disponibles:
{sources}

Génère la réponse corrigée:""")
        ])
    
    async def verify_and_correct(
        self,
        query: str,
        initial_response: str,
        context_docs: List[Document],
        language: str = "fr"
    ) -> Tuple[str, List[VerificationResult], bool]:
        """
        Pipeline CoVE complet: vérifie et corrige la réponse.
        
        Args:
            query: Question originale
            initial_response: Réponse générée initialement
            context_docs: Documents sources utilisés
            language: Langue de la réponse
            
        Returns:
            Tuple[str, List[VerificationResult], bool]: 
                - Réponse corrigée
                - Liste des résultats de vérification
                - Indicateur d'hallucination détectée
        """
        # Étape 1: Extraire les affirmations vérifiables
        claims = await self._extract_claims(initial_response)
        
        if not claims:
            print("ℹ️ Aucune affirmation vérifiable extraite")
            return initial_response, [], False
        
        print(f"📋 {len(claims)} affirmation(s) extraite(s)")
        
        # Limiter le nombre d'affirmations à vérifier
        claims = claims[:self.max_claims_to_verify]
        
        # Étape 2: Générer les questions de vérification
        questions = await self._generate_verification_questions(claims)
        
        # Étape 3: Vérifier chaque affirmation
        verification_results = await self._verify_claims(questions, context_docs)
        
        # Étape 4: Détecter les hallucinations
        hallucination_detected = any(
            not r.is_verified and r.confidence < self.verification_threshold
            for r in verification_results
        )
        
        # Étape 5: Corriger si nécessaire
        needs_correction = any(not r.is_verified for r in verification_results)
        
        if needs_correction:
            print(f"⚠️ {sum(1 for r in verification_results if not r.is_verified)} affirmation(s) à corriger")
            corrected_response = await self._generate_corrected_response(
                query=query,
                initial_response=initial_response,
                verification_results=verification_results,
                context_docs=context_docs,
                language=language
            )
            return corrected_response, verification_results, hallucination_detected
        
        print("✅ Toutes les affirmations vérifiées")
        return initial_response, verification_results, False
    
    async def _extract_claims(self, response: str) -> List[Dict[str, Any]]:
        """Extrait les affirmations vérifiables de la réponse."""
        chain = self.extract_claims_prompt | self.llm
        
        try:
            result = await chain.ainvoke({"response": response})
            content = result.content.strip()
            
            # Nettoyer le JSON si nécessaire
            content = self._clean_json_response(content)
            claims = json.loads(content)
            
            return claims if isinstance(claims, list) else []
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"⚠️ Erreur extraction claims: {e}")
            # Fallback: extraire les phrases comme affirmations simples
            return self._fallback_extract_claims(response)
    
    def _fallback_extract_claims(self, response: str) -> List[Dict[str, Any]]:
        """Extraction de secours basée sur des règles."""
        claims = []
        sentences = re.split(r'[.!?]\s+', response)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            
            # Détecter la catégorie
            category = "factual"
            if re.search(r'\b\d+[,.]?\d*\s*[€$%]|\b\d+\s*(euros?|dollars?)\b', sentence, re.I):
                category = "numerical"
            elif re.search(r'\b(19|20)\d{2}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', sentence):
                category = "temporal"
            
            # Ignorer les phrases trop génériques
            generic_patterns = [
                r'^(je|vous|nous|il|elle|on)\s+(peux|pouvez|pouvons|peut|peuvent)',
                r'^(voici|voilà|en résumé|pour conclure)',
                r'n\'hésitez pas',
                r'contactez'
            ]
            if any(re.search(p, sentence, re.I) for p in generic_patterns):
                continue
            
            claims.append({
                "fact": sentence,
                "category": category,
                "source_required": True
            })
        
        return claims[:self.max_claims_to_verify]
    
    async def _generate_verification_questions(
        self, 
        claims: List[Dict[str, Any]]
    ) -> List[VerificationQuestion]:
        """Génère des questions de vérification pour chaque affirmation."""
        chain = self.generate_questions_prompt | self.llm
        
        try:
            result = await chain.ainvoke({"claims": json.dumps(claims, ensure_ascii=False)})
            content = self._clean_json_response(result.content.strip())
            questions_data = json.loads(content)
            
            return [
                VerificationQuestion(
                    question=q.get("question", ""),
                    fact_to_verify=q.get("fact_to_verify", claims[i]["fact"] if i < len(claims) else ""),
                    category=q.get("category", "factual")
                )
                for i, q in enumerate(questions_data)
            ]
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"⚠️ Erreur génération questions: {e}")
            # Fallback: générer des questions simples
            return [
                VerificationQuestion(
                    question=f"L'affirmation suivante est-elle correcte: '{c['fact']}'?",
                    fact_to_verify=c["fact"],
                    category=c.get("category", "factual")
                )
                for c in claims
            ]
    
    async def _verify_claims(
        self,
        questions: List[VerificationQuestion],
        context_docs: List[Document]
    ) -> List[VerificationResult]:
        """Vérifie chaque affirmation contre les sources."""
        results = []
        
        # Préparer le texte des sources
        sources_text = self._format_sources(context_docs)
        
        chain = self.verify_claim_prompt | self.llm
        
        for question in questions:
            try:
                result = await chain.ainvoke({
                    "claim": question.fact_to_verify,
                    "question": question.question,
                    "sources": sources_text
                })
                
                content = self._clean_json_response(result.content.strip())
                verification_data = json.loads(content)
                
                results.append(VerificationResult(
                    original_claim=question.fact_to_verify,
                    is_verified=verification_data.get("is_verified", False),
                    confidence=float(verification_data.get("confidence", 0.5)),
                    evidence=verification_data.get("evidence", ""),
                    correction=verification_data.get("correction"),
                    source_ids=verification_data.get("source_ids", [])
                ))
                
            except (json.JSONDecodeError, Exception) as e:
                print(f"⚠️ Erreur vérification claim: {e}")
                # Fallback conservateur: marquer comme non vérifié
                results.append(VerificationResult(
                    original_claim=question.fact_to_verify,
                    is_verified=False,
                    confidence=0.3,
                    evidence="Vérification automatique impossible",
                    correction=None
                ))
        
        return results
    
    async def _generate_corrected_response(
        self,
        query: str,
        initial_response: str,
        verification_results: List[VerificationResult],
        context_docs: List[Document],
        language: str = "fr"
    ) -> str:
        """Génère une réponse corrigée basée sur les vérifications."""
        
        # Formater les résultats de vérification
        results_text = "\n".join([
            f"- Affirmation: \"{r.original_claim}\"\n"
            f"  Vérifié: {'✅ Oui' if r.is_verified else '❌ Non'} (confiance: {r.confidence:.0%})\n"
            f"  Evidence: {r.evidence}\n"
            f"  Correction suggérée: {r.correction or 'N/A'}"
            for r in verification_results
        ])
        
        sources_text = self._format_sources(context_docs)
        
        # Ajouter instruction de langue
        lang_instruction = (
            "\n\nIMPORTANT: Réponds UNIQUEMENT en français." if language == "fr"
            else "\n\nIMPORTANT: Reply ONLY in English."
        )
        
        chain = self.correct_response_prompt | self.llm
        
        try:
            result = await chain.ainvoke({
                "query": query,
                "initial_response": initial_response,
                "verification_results": results_text + lang_instruction,
                "sources": sources_text
            })
            return result.content
            
        except Exception as e:
            print(f"❌ Erreur correction: {e}")
            return initial_response
    
    def _format_sources(self, context_docs: List[Document]) -> str:
        """Formate les documents sources pour les prompts."""
        sources_parts = []
        for i, doc in enumerate(context_docs):
            doc_id = doc.metadata.get("id", f"doc_{i+1}")
            score = doc.metadata.get("score", 0.0)
            content = doc.page_content[:800] if len(doc.page_content) > 800 else doc.page_content
            sources_parts.append(f"[{doc_id}] (score: {score:.3f})\n{content}")
        
        return "\n\n---\n\n".join(sources_parts)
    
    @staticmethod
    def _clean_json_response(content: str) -> str:
        """Nettoie une réponse pour extraire le JSON valide."""
        # Supprimer les blocs de code markdown
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        
        # Trouver le premier [ ou { et le dernier ] ou }
        start_array = content.find('[')
        start_obj = content.find('{')
        
        if start_array == -1 and start_obj == -1:
            return content
        
        if start_array == -1:
            start = start_obj
            end_char = '}'
        elif start_obj == -1:
            start = start_array
            end_char = ']'
        else:
            start = min(start_array, start_obj)
            end_char = ']' if start == start_array else '}'
        
        end = content.rfind(end_char)
        
        if start != -1 and end != -1 and end > start:
            return content[start:end + 1]
        
        return content


# ============================================================================
# COV-RAG AGENT - Agent Principal
# ============================================================================

class COVRAGAgent:
    """
    Agent principal intégrant RAG + CoVE pour des réponses à faible hallucination.
    
    Workflow complet:
    1. Récupération hybride des documents
    2. Re-ranking pour optimiser la pertinence
    3. Génération initiale avec ancrage strict
    4. Vérification CoVE des affirmations
    5. Correction et génération finale
    """
    
    def __init__(
        self,
        collection_name: str = "demo_public",
        use_cloud: bool = True,
        model_name: str = None,
        temperature: float = 0.2,
        enable_cove: bool = True,
        verification_threshold: float = 0.7
    ):
        self.enable_cove = enable_cove
        
        # Initialiser le retriever
        self.retriever = COVRAGRetriever(
            collection_name=collection_name,
            use_cloud=use_cloud
        )
        
        # Initialiser le LLM
        self.llm = ChatOpenAI(
            model=model_name or config.OPENAI_MODEL,
            temperature=temperature,
            max_tokens=config.OPENAI_MAX_TOKENS,
            api_key=config.OPENAI_API_KEY
        )
        
        # Initialiser CoVE
        if enable_cove:
            self.cove = ChainOfVerification(
                llm=self.llm,
                retriever=self.retriever,
                verification_threshold=verification_threshold
            )
        
        self._init_generation_prompt()
        
        print(f"✅ COVRAGAgent initialisé - CoVE: {'activé' if enable_cove else 'désactivé'}")
    
    def _init_generation_prompt(self):
        """Initialise le prompt de génération avec ancrage strict."""
        self.generation_prompt = ChatPromptTemplate.from_messages([
            ("system", """Tu es un assistant bancaire professionnel travaillant pour une institution financière réputée.

RÈGLES D'ANCRAGE STRICTES:
1. Utilise UNIQUEMENT les informations des documents fournis
2. Cite TOUJOURS la source [ID] quand tu utilises une information
3. Si l'information n'est pas dans les sources, dis-le clairement
4. NE PAS inventer de dates, montants, numéros ou données personnelles
5. NE PAS extrapoler au-delà des faits présents dans les sources

STYLE:
- Sois professionnel et empathique
- Structure ta réponse clairement
- Propose des actions concrètes basées sur les sources
- Reste factuel et précis"""),
            ("human", """Documents sources:
{context}

Question du client: {question}

Réponds de manière professionnelle en citant les sources utilisées.""")
        ])
    
    async def answer(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        language: str = None
    ) -> RAGResult:
        """
        Pipeline complet RAG + CoVE.
        
        Args:
            query: Question de l'utilisateur
            filters: Filtres optionnels pour la récupération
            language: Langue forcée (fr/en), auto-détecté si None
            
        Returns:
            RAGResult: Résultat complet avec métriques
        """
        import time
        start_time = time.time()
        
        # Détecter la langue si non spécifiée
        if language is None:
            language = self._detect_language(query)
        
        # 1. Récupération hybride
        print("📥 Récupération des documents...")
        docs = self.retriever.hybrid_retrieve(query, filters)
        
        if not docs:
            return RAGResult(
                query=query,
                answer=self._get_no_docs_message(language),
                sources=[],
                confidence_score=0.0,
                language=language,
                processing_time_ms=(time.time() - start_time) * 1000
            )
        
        # 2. Re-ranking
        print("🔄 Re-ranking des documents...")
        docs = self.retriever.rerank(query, docs)
        
        # 3. Génération initiale
        print("💬 Génération de la réponse initiale...")
        initial_response = await self._generate_initial_response(query, docs, language)
        
        # 4. Vérification CoVE (si activé)
        verifications = []
        hallucination_detected = False
        final_response = initial_response
        
        if self.enable_cove:
            print("🔍 Vérification CoVE...")
            final_response, verifications, hallucination_detected = await self.cove.verify_and_correct(
                query=query,
                initial_response=initial_response,
                context_docs=docs,
                language=language
            )
        
        # Calculer le score de confiance
        confidence_score = self._calculate_confidence(docs, verifications)
        
        # Compter les corrections
        corrections_made = sum(1 for v in verifications if not v.is_verified and v.correction)
        
        processing_time = (time.time() - start_time) * 1000
        
        print(f"✅ Réponse générée en {processing_time:.0f}ms - Confiance: {confidence_score:.0%}")
        
        return RAGResult(
            query=query,
            answer=final_response,
            initial_answer=initial_response if self.enable_cove else None,
            sources=[doc.metadata for doc in docs],
            verifications=verifications,
            confidence_score=confidence_score,
            hallucination_detected=hallucination_detected,
            corrections_made=corrections_made,
            processing_time_ms=processing_time,
            language=language
        )
    
    async def _generate_initial_response(
        self,
        query: str,
        docs: List[Document],
        language: str
    ) -> str:
        """Génère la réponse initiale avec ancrage sur les sources."""
        
        # Préparer le contexte
        context_parts = []
        for doc in docs:
            doc_id = doc.metadata.get("id", "unknown")
            score = doc.metadata.get("score", 0.0)
            content = doc.page_content[:600]
            context_parts.append(f"[{doc_id}] (score: {score:.3f})\n{content}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Ajouter instruction de langue
        lang_suffix = (
            "\n\nRéponds UNIQUEMENT en français." if language == "fr"
            else "\n\nReply ONLY in English."
        )
        
        chain = self.generation_prompt | self.llm
        
        try:
            result = await chain.ainvoke({
                "context": context + lang_suffix,
                "question": query
            })
            return result.content
        except Exception as e:
            print(f"❌ Erreur génération: {e}")
            return self._get_error_message(language)
    
    def _calculate_confidence(
        self,
        docs: List[Document],
        verifications: List[VerificationResult]
    ) -> float:
        """Calcule le score de confiance global."""
        
        # Score basé sur les documents
        if docs:
            doc_scores = [doc.metadata.get("score", 0.0) for doc in docs]
            avg_doc_score = sum(doc_scores) / len(doc_scores)
        else:
            avg_doc_score = 0.0
        
        # Score basé sur les vérifications
        if verifications:
            verified_count = sum(1 for v in verifications if v.is_verified)
            verification_score = verified_count / len(verifications)
            avg_confidence = sum(v.confidence for v in verifications) / len(verifications)
        else:
            verification_score = 1.0  # Pas de vérification = confiance par défaut
            avg_confidence = 0.8
        
        # Score combiné
        if verifications:
            # 40% docs, 30% vérification, 30% confiance moyenne
            confidence = 0.4 * avg_doc_score + 0.3 * verification_score + 0.3 * avg_confidence
        else:
            # Sans CoVE: 80% docs, 20% baseline
            confidence = 0.8 * avg_doc_score + 0.2 * 0.7
        
        return min(max(confidence, 0.0), 1.0)
    
    @staticmethod
    def _detect_language(text: str) -> str:
        """Détecte la langue du texte (fr/en)."""
        french_markers = {
            "carte", "bancaire", "compte", "problème", "bonjour", "merci",
            "solde", "crédit", "bloquée", "facturation", "opposition",
            "comment", "pourquoi", "quand", "combien", "quel", "quelle"
        }
        
        lower = text.lower()
        
        # Vérifier les accents français
        if re.search(r"[àâçéèêëîïôùûüÿœ]", lower):
            return "fr"
        
        # Vérifier les mots français
        hits = sum(1 for w in french_markers if w in lower)
        if hits >= 2:
            return "fr"
        
        return "en"
    
    @staticmethod
    def _get_no_docs_message(language: str) -> str:
        """Message quand aucun document n'est trouvé."""
        if language == "fr":
            return (
                "Je n'ai pas trouvé d'informations pertinentes dans notre base de connaissances "
                "pour répondre à votre question. Veuillez contacter notre service client "
                "pour une assistance personnalisée."
            )
        return (
            "I couldn't find relevant information in our knowledge base to answer your question. "
            "Please contact our customer service for personalized assistance."
        )
    
    @staticmethod
    def _get_error_message(language: str) -> str:
        """Message en cas d'erreur."""
        if language == "fr":
            return "Désolé, une erreur s'est produite. Veuillez réessayer."
        return "Sorry, an error occurred. Please try again."


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def create_cov_rag_agent(
    collection_name: str = "demo_public",
    enable_cove: bool = True,
    **kwargs
) -> COVRAGAgent:
    """Factory function pour créer un agent COV-RAG configuré."""
    return COVRAGAgent(
        collection_name=collection_name,
        enable_cove=enable_cove,
        **kwargs
    )


# ============================================================================
# TESTS
# ============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def test_cov_rag():
        print("=" * 70)
        print("🧪 TEST COV-RAG AGENT")
        print("=" * 70)
        
        # Créer l'agent
        agent = create_cov_rag_agent(
            collection_name="demo_public",
            enable_cove=True
        )
        
        # Questions de test
        test_queries = [
            {"query": "Ma carte bancaire est bloquée, que dois-je faire ?", "lang": "fr"},
            {"query": "How do I dispute an unauthorized charge?", "lang": "en"}
        ]
        
        for test in test_queries:
            print(f"\n{'='*70}")
            print(f"📝 Question ({test['lang'].upper()}): {test['query']}")
            print("=" * 70)
            
            result = await agent.answer(test["query"])
            
            print("\n📊 RÉSULTATS:")
            print(f"  - Confiance: {result.confidence_score:.0%}")
            print(f"  - Hallucination détectée: {'Oui' if result.hallucination_detected else 'Non'}")
            print(f"  - Corrections: {result.corrections_made}")
            print(f"  - Sources: {len(result.sources)}")
            print(f"  - Temps: {result.processing_time_ms:.0f}ms")
            
            print("\n💬 RÉPONSE:")
            print(result.answer[:500] + "..." if len(result.answer) > 500 else result.answer)
            
            if result.verifications:
                print(f"\n🔍 VÉRIFICATIONS ({len(result.verifications)}):")
                for v in result.verifications[:3]:
                    status = "✅" if v.is_verified else "❌"
                    print(f"  {status} {v.original_claim[:80]}...")
                    print(f"     Confiance: {v.confidence:.0%}")
        
        print("\n" + "=" * 70)
        print("✅ Tests terminés")
        print("=" * 70)
    
    # Exécuter les tests
    asyncio.run(test_cov_rag())
