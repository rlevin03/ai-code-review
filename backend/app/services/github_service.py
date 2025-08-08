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
    
    gh = None
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
                
                # Add review comments (as GitHub suggestions)
                if analysis and analysis.get('issues'):
                    for issue in analysis['issues']:
                        suggestion_text = issue.get('suggestion')
                        if not suggestion_text:
                            continue

                        issues_count += 1
                        severity = issue.get('severity', 'info').upper()
                        message = issue.get('message', 'Suggestion')
                        comment_body = (
                            f"**{severity}**: {message}\n\n"
                            f"```suggestion\n{suggestion_text}\n```"
                        )

                        start_line = issue.get('start_line')
                        end_line = issue.get('end_line')
                        target_line = issue.get('line')

                        comment_payload = {
                            'path': file.filename,
                            'body': comment_body,
                            'side': 'RIGHT'
                        }

                        # Multi-line suggestion with proper ordering
                        if start_line and end_line:
                            sl = int(start_line)
                            el = int(end_line)
                            if sl == el:
                                # Convert to single-line anchor
                                comment_payload['line'] = sl
                            else:
                                if sl > el:
                                    sl, el = el, sl
                                comment_payload['start_line'] = sl
                                comment_payload['line'] = el
                                comment_payload['start_side'] = 'RIGHT'
                        elif target_line:
                            # Single-line anchor: only 'line'
                            tl = int(target_line)
                            comment_payload['line'] = tl
                        else:
                            # No anchor line; skip
                            continue

                        all_comments.append(comment_payload)
        
        # Submit the review
        if all_comments:
            head_sha = pr.head.sha
            head_commit = repo.get_commit(head_sha)
            # GitHub limits to 30 comments per review
            for i in range(0, len(all_comments), 30):
                batch = all_comments[i:i+30]
                pr.create_review(
                    body=f"AI Code Review (Part {i//30 + 1})" if len(all_comments) > 30 else "AI Code Review Complete",
                    event="COMMENT",
                    comments=batch,
                    commit=head_commit
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
            if gh:
                repo = gh.get_repo(repo_name)
                pr = repo.get_pull(pr_number)
                pr.create_issue_comment(
                    f"AI Code Review failed: {str(e)}\n\nPlease check the logs or try again."
                )
        except:
            pass