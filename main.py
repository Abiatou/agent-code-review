import sys
from src.git_client import GitClient
from src.llm_engine import LLMEngine
from src.filter import filter_issues, load_config

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

    # 2. Analyse LLM pour chaque fichier modifié
    for item in diffs:
        filename = item["filename"]
        patch = item["patch"]
        
        print(f"🔍 Analyse du fichier : {filename}")
        result = llm_engine.analyze_patch(filename, patch)

        full_report += f"### 📄 Fichier : `{filename}` (Note : {result.score}/10)\n"
        full_report += f"**Résumé :** {result.summary}\n\n"

        # Application du module de filtrage indépendant (Résolution du blocage B3)
        real_issues = filter_issues(result.issues, config)
    
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

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Utilisation : python main.py <utilisateur/depot> <numero_pr>")
        print("Exemple    : python main.py mon-compte/mon-projet 1")
    else:
        repo = sys.argv[1]
        pr_num = int(sys.argv[2])
        run_agent(repo, pr_num)