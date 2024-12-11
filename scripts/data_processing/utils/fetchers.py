# scripts/data_processing/utils/fetchers.py
import os
import git
from pathlib import Path

class GitFetcher:
    def __init__(self, base_path: str = "data/audits"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def clone_or_update_repository(self, repo_url: str, destination: str) -> None:
        """
        Clone a repository if it doesn't exist, or pull latest changes if it does.
        
        Args:
            repo_url: URL of the git repository
            destination: Local path where the repository should be cloned
        """
        dest_path = self.base_path / destination
        
        if not (dest_path / '.git').exists():
            print(f"Cloning repository {repo_url}...")
            git.Repo.clone_from(repo_url, dest_path)
            print("Repository cloned successfully.")
        else:
            print(f"Repository exists at {dest_path}, pulling latest changes...")
            repo = git.Repo(dest_path)
            origin = repo.remotes.origin
            origin.pull()
            print("Repository updated successfully.")

    def fetch_audit_reports(self):
        """Fetch all configured audit report repositories."""
        repos = {
            "spearbit": {
                "url": "https://github.com/spearbit/portfolio.git",
                "destination": "spearbit_portfolio"
            }
            # Add more repositories here as needed
        }
        
        for name, info in repos.items():
            try:
                self.clone_or_update_repository(info["url"], info["destination"])
            except Exception as e:
                print(f"Error fetching {name} repository: {str(e)}")