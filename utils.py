from models import db, TabooWord, Warning

def filter_content(content, user_id):
    taboo_words = [t.word for t in TabooWord.query.all()]
    found_count = 0
    filtered_content = content
    
    for word in taboo_words:
        # Simple case-insensitive match
        if word.lower() in content.lower():
            found_count += 1
            # Replace all occurrences
            import re
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            filtered_content = pattern.sub('*' * len(word), filtered_content)
            
    if found_count >= 3:
        # Not shown at all, 2 warnings
        warn = Warning(user_id=user_id, reason="Review blocked due to excessive taboo words (3+).")
        db.session.add(warn)
        # We need to increment warning_count in the caller or here
        return None, 2
    elif found_count >= 1:
        # Shown with stars, 1 warning
        warn = Warning(user_id=user_id, reason=f"Review contained {found_count} taboo words (filtered).")
        db.session.add(warn)
        return filtered_content, 1
    
    return content, 0
