from app.core.github_client import github_client
from app.core.ai_analyzer import analyze_code
import logging

logger = logging.getLogger(__name__)

async def handle_pull_request(payload: dict):
    """Process a pull request event"""
    try:
        # Get installation access token
        installation_id = payload['installation']['id']
        gh = github_client.get_installation_client(installation_id)
        
        # Get the repository and PR
        repo = gh.get_repo(payload['repository']['full_name'])
        pr = repo.get_pull(payload['pull_request']['number'])
        
        # Get the files changed in the PR
        files = pr.get_files()
        
        # Analyze each file
        comments = []
        for file in files:
            if file.filename.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
                # Analyze the code
                analysis = await analyze_code(
                    filename=file.filename,
                    patch=file.patch,
                    full_content=file.contents_url
                )
                
                # Add review comments
                if analysis and analysis.get('issues'):
                    for issue in analysis['issues']:
                        comments.append({
                            'path': file.filename,
                            'line': issue['line'],
                            'body': issue['message']
                        })
        
        # Submit the review
        if comments:
            pr.create_review(
                body="AI Code Review Complete",
                event="COMMENT",
                comments=comments
            )
            logger.info(f"Submitted review with {len(comments)} comments")
        else:
            pr.create_issue_comment("AI Code Review Complete - No issues found!")
            logger.info("No issues found in PR")
            
    except Exception as e:
        logger.error(f"Error processing PR: {e}")
        try:
            pr.create_issue_comment(
                "AI Code Review failed. Please check the logs or try again."
            )
        except:
            pass