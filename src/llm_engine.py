import os
from typing import List
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

class CodeIssue(BaseModel):
    category: str = Field(description="Catégorie : 'security', 'bug', 'performance' ou 'style'")
    severity: str = Field(description="Niveau : 'CRITICAL', 'HIGH', 'MEDIUM', ou 'LOW'")
    line_number: int = Field(default=0, description="Numéro de ligne approximatif concerné")
    description: str = Field(description="Explication précise du problème détecté")
    suggestion: str = Field(description="Proposition de correction détaillée")
    is_false_positive: bool = Field(description="True si le signalement potentiel s'avère être un faux positif")

class ReviewResult(BaseModel):
    summary: str = Field(description="Résumé concis des modifications et de la qualité générale")
    score: int = Field(description="Note globale du code analysé attribuée sur 10")
    issues: List[CodeIssue] = Field(description="Liste des anomalies ou alertes identifiées")


class LLMEngine:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Erreur : GROQ_API_KEY est absente du fichier .env")
        
        self.llm = ChatGroq(
            model="qwen/qwen3.8-27b",
            temperature=0.1,
            groq_api_key=api_key
        )
        self.structured_llm = self.llm.with_structured_output(ReviewResult)

    def analyze_patch(self, filename: str, patch: str) -> ReviewResult:
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "Vous êtes un expert en revue de code automatisée. Votre rôle est d'analyser les "
                "modifications de code (diff/patch) fournies, d'identifier les vulnérabilités de sécurité, "
                "les bugs et les opportunités d'optimisation. Soyez rigoureux et filtrez les faux positifs "
                "en marquant 'is_false_positive' à True lorsque l'alerte n'impose aucun changement critique."
            )),
            ("user", "Fichier à examiner : {filename}\n\nDiff à analyser :\n{patch}")
        ])
        
        chain = prompt | self.structured_llm
        return chain.invoke({"filename": filename, "patch": patch})