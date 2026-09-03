"""PolicyLens: document intelligence for synthetic life-insurance products."""

from .agents import PolicyWorkflow, ProcessedDocument
from .audit import AuditRepository
from .extract import ProductExtractor
from .retrieval import GroundedRetriever

__all__ = [
    "AuditRepository",
    "GroundedRetriever",
    "PolicyWorkflow",
    "ProcessedDocument",
    "ProductExtractor",
]

__author__ = "Arkamitra Bhattacharyya"
__version__ = "1.1.0"
