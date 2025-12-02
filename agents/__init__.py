"""
Agents GenAI Workflow Automation

Ce package contient les agents RAG et les workflows LangGraph.

Modules:
- graph: Workflow RAG standard
- state: États des graphes
- cov_rag: Système RAG avec Chain-of-Verification (CoVE)
- cov_rag_graph: Workflow LangGraph pour COV-RAG
"""

from agents.state import GraphState, COVRAGGraphState, VerificationState, RAGState
from agents.graph import app as standard_rag_app

# COV-RAG exports
from agents.cov_rag import (
    COVRAGRetriever,
    ChainOfVerification,
    COVRAGAgent,
    RAGResult,
    VerificationQuestion,
    VerificationResult,
    create_cov_rag_agent
)

from agents.cov_rag_graph import (
    cov_rag_app,
    rag_app,
    run_cov_rag,
    build_cov_rag_graph
)

__all__ = [
    # États
    "GraphState",
    "COVRAGGraphState", 
    "VerificationState",
    "RAGState",
    
    # Apps/Workflows
    "standard_rag_app",
    "cov_rag_app",
    "rag_app",
    
    # Classes COV-RAG
    "COVRAGRetriever",
    "ChainOfVerification",
    "COVRAGAgent",
    "RAGResult",
    "VerificationQuestion",
    "VerificationResult",
    
    # Fonctions
    "create_cov_rag_agent",
    "run_cov_rag",
    "build_cov_rag_graph"
]
