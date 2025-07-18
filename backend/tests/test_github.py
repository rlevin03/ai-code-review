import os
from github import Github, GithubIntegration
from dotenv import load_dotenv

load_dotenv()

# Test GitHub App authentication
app_id = int(os.getenv("GITHUB_APP_ID"))
with open("mycodereviewbot.2025-07-01.private-key.pem", 'r') as f:
    private_key = f.read()

print(f"Testing GitHub App ID: {app_id}")

try:
    # Create integration
    integration = GithubIntegration(app_id, private_key)
    print("✓ Created GitHub integration")
    
    # Get installations
    installations = list(integration.get_installations())
    print(f"✓ Found {len(installations)} installations")
    
    for installation in installations:
        print(f"\nInstallation ID: {installation.id}")
        
        # Get access token
        access_token = integration.get_access_token(installation.id).token
        gh = Github(access_token)
        print("✓ Got access token")
        
        # List accessible repos using the integration object
        try:
            # Get repositories for this installation directly from integration
            repos = integration.get_installation(installation.id).get_repos()
            print("\nAccessible repositories:")
            
            repo_count = 0
            for repo in repos:
                print(f"  - {repo.full_name}")
                repo_count += 1
                
                # Test: Try to get recent PRs for first few repos
                if repo_count <= 2:  # Limit to first 2 repos to avoid too much output
                    try:
                        prs = list(repo.get_pulls(state='all')[:3])
                        if prs:
                            print(f"    Recent PRs: {[f'#{pr.number}' for pr in prs]}")
                        else:
                            print(f"    No recent PRs found")
                    except Exception as pr_error:
                        print(f"    Error getting PRs: {pr_error}")
                        
                # Stop after checking first 5 repos to keep output manageable
                if repo_count >= 5:
                    print(f"  ... and more repositories")
                    break
                    
            if repo_count == 0:
                print("  No repositories found for this installation")
                
        except Exception as e:
            print(f"✗ Error accessing repositories: {e}")
            
            # Try alternative approach - get user and check what we can access
            try:
                print("\nTrying to get authenticated user info...")
                user = gh.get_user()
                print(f"Authenticated as: {user.login}")
                print(f"User type: {user.type}")
                
                # Try to get app information
                app = gh.get_app()
                print(f"App name: {app.name}")
                print(f"App permissions: {app.permissions}")
                
            except Exception as user_error:
                print(f"Could not get user info: {user_error}")
            
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
print("GitHub App Test Complete")
print("="*50)