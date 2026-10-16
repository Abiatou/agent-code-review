# src/filter.py
import yaml
from typing import List, Dict, Any

RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}

DEFAULT_CONFIG = {
    "min_severity": "MEDIUM",
    "ignore_categories": ["style", "style_code", "formatting"]
}

def load_config(config_path: str = ".ai-review.yml") -> Dict[str, Any]:
    """Charge la configuration YAML du filtre ou retourne la configuration par défaut."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config if config else DEFAULT_CONFIG
    except FileNotFoundError:
        return DEFAULT_CONFIG

def filter_issues(issues: List[Any], cfg: Dict[str, Any] = None) -> List[Any]:
    """Applique le filtrage déterministe indépendant sur les remarques."""
    if cfg is None:
        cfg = load_config()

    seen, kept = set(), []
    min_sev = str(cfg.get("min_severity", "MEDIUM")).upper()
    ignored_cats = [str(c).lower() for c in cfg.get("ignore_categories", [])]

    for i in issues:
        # 1. Respect de l'auto-évaluation initiale si déjà marqué faux positif
        if getattr(i, "is_false_positive", False):
            continue

        # Extraction propre des chaînes (compatible Enum Pydantic et String)
        cat_str = str(getattr(i, "category", getattr(i, "categorie", ""))).lower()
        sev_str = str(getattr(i, "severity", getattr(i, "severite", "MEDIUM"))).upper()
        # Gestion des représentations type "CategorieEnum.STYLE_CODE"
        if "." in cat_str: cat_str = cat_str.split(".")[-1]
        if "." in sev_str: sev_str = sev_str.split(".")[-1]

        # 2. Règle "Linters" : Exclusion des catégories déléguées (ex: Style)
        if any(ignored in cat_str for ignored in ignored_cats):
            i.is_false_positive = True
            continue

        # 3. Seuil de sévérité minimale
        if RANK.get(sev_str, 0) < RANK.get(min_sev, 1):
            i.is_false_positive = True
            continue

        # 4. Dédoublonnage sur la ligne et la catégorie
        line_num = getattr(i, "line_number", getattr(i, "line", 0))
        key = (line_num, cat_str)
        if key in seen:
            i.is_false_positive = True
            continue

        seen.add(key)
        kept.append(i)

    return kept