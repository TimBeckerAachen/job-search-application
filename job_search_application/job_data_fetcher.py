import time
import json
import random
import requests
from typing import List, Dict
from bs4 import BeautifulSoup


def parse_jobtensor_jobs() -> List[Dict[str, str]]:
    # TODO: provide filter
    # TODO: standard interface
    # url = "https://jobtensor.com/search?q=data&m=Lead,Principal&l=Berlin"
    url = "https://jobtensor.com/search?q=data&o=Data+Scientist,Data+Engineer&l=Berlin"

    json_data = get_dict_from_url(url)

    per_page = json_data['config']['per_page']
    total_jobs = json_data['total']
    num_pages = int(total_jobs / per_page) + (total_jobs % per_page > 0)
    print(f'Total number of pages {num_pages}')
    job_list = []
    index = 18

    for page_num in range(num_pages):
        print(page_num)
        current_url = f"{url}&page={page_num + 1}"

        json_data = get_dict_from_url(current_url)

        job_hits = json_data['hits']

        for job in job_hits:
            job_dict = {
                "id": index,
                "title": job["title"],
                "company": job["company"],
                "locations": ", ".join(job["locations"]),
                "skills": ", ".join(job["skills"]),
                "posted_at": job["posted_at"],
                "is_remote": str(job["is_remote"]),
                "snippet_fragments": ", ".join(job["snippet_fragments"]),
            }
            posting_url = f"https://jobtensor.com/job/{job['slug']}"
            print(posting_url)
            inner_json_data = get_dict_from_url(posting_url)

            job_dict['description'] = inner_json_data['job']['description']

            job_list.append(job_dict)
            index += 1
            time.sleep(random.randint(1, 10))

    return job_list


def get_dict_from_url(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/58.0.3029.110 Safari/537.3"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise

    json_data = get_dict_from_resp(response)
    return json_data


def get_dict_from_resp(response: requests.Response) -> dict:
    main_soup = BeautifulSoup(response.text, 'html.parser')
    script_tag = main_soup.find('script', type='text/javascript')
    script_content = script_tag.string.strip()
    start_idx = script_content.find('{"config":')
    raw_data = script_content[start_idx:-1]
    json_data = json.loads(raw_data)
    return json_data
