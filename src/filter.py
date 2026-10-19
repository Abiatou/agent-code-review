RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
DEFAULT_CFG = {"min_severity": "MEDIUM", "ignore_categories": ["style"]}

def load_config(path=".ai-review.yml"):
    try:
        import yaml
        with open(path, encoding="utf-8") as f:
            return {**DEFAULT_CFG, **(yaml.safe_load(f) or {})}
    except Exception:
        return dict(DEFAULT_CFG)

def filter_issues(issues, cfg):
    seen, kept = set(), []
    for i in issues:
        if i.is_false_positive:                              # R1 : avis du modèle
            continue
        if i.category in cfg["ignore_categories"]:           # R2 : catégories ignorées
            continue
        if RANK[i.severity] < RANK[cfg["min_severity"]]:     # R3 : seuil
            continue
        key = (i.line_number, i.category)                    # R4 : dédoublonnage
        if key in seen:
            continue
        seen.add(key)
        kept.append(i)
    return kept

def safe_filter(issues, cfg):
    try:
        return filter_issues(issues, cfg)
    except Exception:                                        # R5 : filtre de secours
        return [i for i in issues if i.severity in ("CRITICAL", "HIGH")]