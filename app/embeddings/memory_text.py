def memory_to_text(subject, relation, value):

    relation_templates = {

        "lives_in":
            f"The user currently lives in {value}.",

        "current_job":
            f"The user's current job is {value}.",

        "age":
            f"The user's age is {value}.",

        "born_in":
            f"The user was born in {value}.",

        "current_city":
            f"The user's current city is {value}.",

        "current_country":
            f"The user currently lives in {value}.",

        "likes":
            f"The user likes {value}.",

        "loves":
            f"The user loves {value}.",

        "goal":
            f"The user's goal is {value}.",

        "studies":
            f"The user studies {value}.",

        "skills":
            f"The user's skill is {value}.",

        "building":
            f"The user is building {value}."
    }

    return relation_templates.get(
        relation,
        f"The user {relation.replace('_', ' ')} {value}."
    )