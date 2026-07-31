"""Second synthetic prompt revision used to test Braintrust version history."""

import braintrust


project = braintrust.projects.create(name="My Project")

release_reviewer = project.prompts.create(
    name="HRAI synthetic release reviewer",
    slug="hrai-synthetic-release-reviewer",
    description="Non-production prompt used for Braintrust dogfood.",
    model="gpt-4.1-mini",
    params={"temperature": 0},
    messages=[
        {
            "role": "system",
            "content": (
                "Classify the supplied synthetic evidence as sufficient, "
                "insufficient, or non-comparable. Never authorize a real "
                "release, and state which required evidence is absent."
            ),
        },
        {"role": "user", "content": "{{{evidence}}}"},
    ],
    metadata={"dogfood_revision": "v2"},
)
