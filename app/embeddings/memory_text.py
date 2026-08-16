def memory_to_text(subject, relation, value):
    """Convert a structured memory into a natural-language sentence."""

    subject = str(subject).strip() or "User"
    value = str(value).strip()

    relation_templates = {
        "lives_in": f"{subject} currently lives in {value}.",
        "current_job": f"{subject}'s current job is {value}.",
        "age": f"{subject}'s age is {value}.",
        "born_in": f"{subject} was born in {value}.",
        "current_city": f"{subject}'s current city is {value}.",
        "current_country": f"{subject} currently lives in {value}.",
        "likes": f"{subject} likes {value}.",
        "loves": f"{subject} loves {value}.",
        "goal": f"{subject}'s goal is {value}.",
        "studies": f"{subject} studies {value}.",
        "skills": f"{subject}'s skill is {value}.",
        "building": f"{subject} is building {value}.",
    }

    return relation_templates.get(
        relation,
        f"{subject} {relation.replace('_', ' ')} {value}."
    )
