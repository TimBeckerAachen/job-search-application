import json
from pathlib import Path

from job_search_application.minsearch import Index


def load_index() -> Index:
    # TODO: add database
    script_dir = Path(__file__).parent
    relative_path_data = Path("./../data/job_data.json")
    absolute_path_data = (script_dir / relative_path_data).resolve()
    with open(absolute_path_data, 'r') as json_file:
        job_data = json.load(json_file)

    index = Index(
        text_fields=[
            "title",
            "company",
            "locations",
            "skills",
            "posted_at",
            "is_remote",
            "snippet_fragments",
            "description"
        ],
        keyword_fields=["id"]
    )

    return index.fit(job_data)