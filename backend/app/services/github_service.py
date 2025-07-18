from app.core.github_client import github_client
from app.core.ai_analyzer import analyze_code
from app.api.analytics import record_review
import logging
import time

logger = logging.getLogger(__name__)

async def handle_pull_request(payload: dict):
    """Process a pull request event"""
    start_time = time.time()
    repo_name = payload['repository']['full_name']
    pr_number = payload['pull_request']['number']
    
    try:
        # Get installation access token
        installation_id = payload['installation']['id']
        gh = github_client.get_installation_client(installation_id)
        
        # Get the repository and PR
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        # Post initial comment
        pr.create_issue_comment("🤖 AI Code Review started...")
        
        # Get the files changed in the PR
        files = pr.get_files()
        
        # Analyze each file
        all_comments = []
        issues_count = 0
        
        for file in files:
            if file.filename.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
                # Get the patch
                if not file.patch:
                    continue
                    
                # Analyze the code
                analysis = await analyze_code(
                    filename=file.filename,
                    patch=file.patch,
                    full_content=None  #TODO: Add full content
                )
                
                # Add review comments
                if analysis and analysis.get('issues'):
                    for issue in analysis['issues']:
                        issues_count += 1
                        comment_body = f"**{issue.get('severity', 'info').upper()}**: {issue['message']}"
                        
                        if issue.get('line'):
                            all_comments.append({
                                'path': file.filename,
                                'line': issue['line'],
                                'body': comment_body
                            })
        
        # Submit the review
        if all_comments:
            # GitHub limits to 30 comments per review
            for i in range(0, len(all_comments), 30):
                batch = all_comments[i:i+30]
                pr.create_review(
                    body=f"AI Code Review (Part {i//30 + 1})" if len(all_comments) > 30 else "AI Code Review Complete",
                    event="COMMENT",
                    comments=batch
                )
            logger.info(f"Submitted review with {len(all_comments)} comments")
        else:
            pr.create_issue_comment("AI Code Review Complete - No issues found! Great job!")
            logger.info("No issues found in PR")
        
        # Record analytics
        response_time = time.time() - start_time
        record_review(repo_name, pr_number, issues_count, response_time)
            
    except Exception as e:
        logger.error(f"Error processing PR: {e}", exc_info=True)
        try:
            repo = gh.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            pr.create_issue_comment(
                f"AI Code Review failed: {str(e)}\n\nPlease check the logs or try again."
            )
        except:
            pass