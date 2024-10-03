import json

from job_search_application.minsearch import Index
from job_search_application.job_data_fetcher import parse_jobtensor_jobs


if __name__ == "__main__":
    def search(query):
        boost = {}

        results = index.search(
            query=query,
            filter_dict={},
            boost_dict=boost,
            num_results=3
        )

        return results

    with open('job_data.json', 'r') as json_file:
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

    index.fit(job_data)

    query = "I am looking for job as a CRM Lead in Berlin."
    search_results = search(query)

    print(search_results)

    # job_list = parse_jobtensor_jobs()
    #
    # with open('job_data.json', 'w') as json_file:
    #     json.dump(job_list, json_file, indent=2)
    #
    # print(job_list)
