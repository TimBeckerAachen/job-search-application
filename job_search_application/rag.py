from time import time
from ai21 import AI21Client
from ai21.models.chat import ChatMessage

from job_search_application import ingest

client = AI21Client()
index = ingest.load_index()


def search(query):
    boost = {}

    results = index.search(
        query=query,
        filter_dict={},
        boost_dict=boost,
        num_results=3
    )

    return results


prompt_template = """
You're an expert application coach. Answer the QUESTION based on the CONTEXT from the job database.
Use only the facts from the CONTEXT when answering the QUESTION.

QUESTION: {question}

CONTEXT:
{context}
""".strip()

entry_template = """
job_title: {title}
company_name: {company}
work locations: {locations}
highlighted skills: {skills}
date of posting: {posted_at}
short job summary: {snippet_fragments}
detailed job description: {description}
""".strip()


def build_prompt(query, search_results):
    context = ""

    for doc in search_results:
        context = context + entry_template.format(**doc) + "\n\n"

    prompt = prompt_template.format(question=query, context=context).strip()
    return prompt


def llm(prompt, model='jamba-1.5-mini'):
    response = client.chat.completions.create(
    model=model,
    messages=[ChatMessage(
        role="user",
        content=prompt
    )],
        temperature=0.8,
        max_tokens=200
    )

    token_stats = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }

    return response.choices[0].message.content, token_stats


def rag(query, model='jamba-1.5-mini'):
    t0 = time()
    search_results = search(query)
    prompt = build_prompt(query, search_results)
    response, token_stats = llm(prompt, model=model)

    # TODO: add evaluation?

    t1 = time()
    delta_t = t1-t0

    response_data = {
        "response": response,
        "model_used": model,
        "response_time": delta_t,
        # "relevance": relevance.get("Relevance", "UNKNOWN"),
        # "relevance_explanation": relevance.get(
        #     "Explanation", "Failed to parse evaluation"
        # ),
        "prompt_tokens": token_stats["prompt_tokens"],
        "completion_tokens": token_stats["completion_tokens"],
        "total_tokens": token_stats["total_tokens"],
        # "eval_prompt_tokens": rel_token_stats["prompt_tokens"],
        # "eval_completion_tokens": rel_token_stats["completion_tokens"],
        # "eval_total_tokens": rel_token_stats["total_tokens"],
        # "openai_cost": openai_cost,
    }
    return response_data