"""Synthetic Braintrust prompt used only to test versioning and deployment."""

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
                "Classify the supplied synthetic evidence as sufficient or "
                "insufficient. Never authorize a real release."
            ),
        },
        {"role": "user", "content": "{{{evidence}}}"},
    ],
    metadata={"dogfood_revision": "v1"},
)
