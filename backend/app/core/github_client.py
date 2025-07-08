from github import Github, GithubIntegration
from app.config import settings

class GitHubClient:
    def __init__(self):
        # Read private key
        with open(settings.GITHUB_PRIVATE_KEY_PATH, 'r') as key_file:
            private_key = key_file.read()
        
        # Create GitHub integration
        self.integration = GithubIntegration(
            settings.GITHUB_APP_ID,
            private_key,
        )
    
    def get_installation_client(self, installation_id: int) -> Github:
        """Get a GitHub client for a specific installation"""
        access_token = self.integration.get_access_token(installation_id).token
        return Github(access_token)

# Create a singleton instance
github_client = GitHubClient()