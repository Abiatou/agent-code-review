import os
from github import Github
from dotenv import load_dotenv

# Charger les variables du fichier .env
load_dotenv()

class GitClient:
    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("Erreur : GITHUB_TOKEN est absent du fichier .env")
        self.client = Github(token)

    def get_pr_diff(self, repo_name: str, pr_number: int):
        """Récupère la liste des fichiers modifiés et leurs patchs (diffs)."""
        repo = self.client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        diff_data = []
        for file in pr.get_files():
            # Ne conserve que les fichiers texte contenant des modifications (patch)
            if file.patch:
                diff_data.append({
                    "filename": file.filename,
                    "status": file.status,
                    "patch": file.patch
                })
        return diff_data

    def post_comment(self, repo_name: str, pr_number: int, comment: str):
        """Publie un commentaire sur la Pull Request."""
        repo = self.client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        pr.create_issue_comment(comment)