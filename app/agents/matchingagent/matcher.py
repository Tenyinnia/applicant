def hard_filter(cv, job):
    required = extract_required_skills(job["description"])
    overlap = set(required) & set(cv["skills"])
    return len(overlap) >= 2
