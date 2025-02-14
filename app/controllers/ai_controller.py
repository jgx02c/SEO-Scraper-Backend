from fastapi import HTTPException
from ai.ai_service import run_seo_fix, run_ai_action, generate_content

# Trigger SEO fix action
def run_seo_fix_action(db, user_email):
    result = run_seo_fix(user_email)
    if not result:
        raise HTTPException(status_code=400, detail="SEO fix action failed")
    return {"message": "SEO fix action executed successfully"}


# Run a general AI action
def trigger_ai_action(action_type, db, user_email):
    result = run_ai_action(action_type, user_email)
    if not result:
        raise HTTPException(status_code=400, detail="AI action failed")
    return {"message": f"AI action '{action_type}' executed successfully"}


# Generate AI-powered content
def generate_ai_content(content_type, db, user_email):
    result = generate_content(content_type, user_email)
    if not result:
        raise HTTPException(status_code=400, detail="Content generation failed")
    return {"message": f"AI content generation for {content_type} completed", "content": result}
