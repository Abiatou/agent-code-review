import sys
from src.git_client import GitClient
from src.llm_engine import LLMEngine
from src.filter import filter_issues, load_config
from src.chunker import split_patch


def safe_filter(issues, config):
    """R5 : filtre de secours si le moteur de règles échoue."""
    try:
        return filter_issues(issues, config)
    except Exception as e:
        print(f"⚠️ Erreur du filtrage ({e}) : filtre de secours (CRITICAL et HIGH).")
        return [i for i in issues if i.severity in ("CRITICAL", "HIGH")]


def run_agent(repo_name: str, pr_number: int):
    print(f"🚀 Lancement de la revue de code sur {repo_name} (PR #{pr_number})...")

    git_client = GitClient()
    llm_engine = LLMEngine()

    # Chargement unique de la configuration du filtrage (.ai-review.yml)
    config = load_config(".ai-review.yml")

    # 1. Extraction du diff
    diffs = git_client.get_pr_diff(repo_name, pr_number)
    if not diffs:
        print("Aucun fichier modifié détecté dans cette Pull Request.")
        return

    full_report = "## 🤖 Rapport de Revue Automatisée par l'Agent IA\n\n"
    has_critical = False

    # 2. Analyse LLM pour chaque fichier modifié
    for item in diffs:
        filename = item["filename"]
        patch = item.get("patch")
        if not patch:
            print(f"⏭️ {filename} ignoré (fichier binaire ou sans diff).")
            continue

        print(f"🔍 Analyse du fichier : {filename}")

        # Découpage des gros diffs, puis fusion des résultats
        issues, scores, summaries = [], [], []
        for part in split_patch(patch):
            result = llm_engine.analyze_patch(filename, part)
            issues += result.issues
            scores.append(result.score)
            summaries.append(result.summary)

        # Filtrage indépendant du modèle
        real_issues = safe_filter(issues, config)
        print(f"   {len(issues)} remarques brutes, {len(real_issues)} conservées")

        if any(i.severity == "CRITICAL" for i in real_issues):
            has_critical = True

        full_report += f"### 📄 Fichier : `{filename}` (Note : {min(scores)}/10)\n"
        full_report += f"**Résumé :** {' '.join(summaries)}\n\n"

        if real_issues:
            full_report += "#### ⚠️ Problèmes identifiés :\n"
            for issue in real_issues:
                full_report += f"- **[{issue.severity}] {issue.category.upper()}** (Ligne ~{issue.line_number}) : {issue.description}\n"
                full_report += f"  > 💡 **Suggestion :** {issue.suggestion}\n\n"
        else:
            full_report += "✅ Aucune anomalie critique détectée.\n\n"

    # 3. Publication sur GitHub
    print("💬 Publication du rapport sur GitHub...")
    git_client.post_comment(repo_name, pr_number, full_report)
    print("🎉 Revue de code publiée avec succès !")

    # 4. Statut du pipeline : échec si une faille CRITICAL subsiste
    if has_critical:
        print("❌ Anomalie CRITICAL détectée : le pipeline est marqué en échec.")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Utilisation : python main.py <utilisateur/depot> <numero_pr>")
        print("Exemple    : python main.py mon-compte/mon-projet 1")
    else:
        repo = sys.argv[1]
        pr_num = int(sys.argv[2])
        run_agent(repo, pr_num)