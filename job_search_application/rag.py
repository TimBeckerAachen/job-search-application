import json
from time import time
from ai21 import AI21Client
from ai21.models.chat import ChatMessage

from job_search_application import ingest

client = AI21Client()
index = ingest.load_index()


def search(query):
    boost = {
      'title': 1.24,
      'company': 1.2,
      'locations': 2.91,
      'skills': 1.05,
      'posted_at': 2.09,
      'is_remote': 0.83,
      'snippet_fragments': 0.56,
      'description': 2.18
    }

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


evaluation_prompt_template = """
You are an expert evaluator for a RAG system.
Your task is to analyze the relevance of the generated response to the given queries.
Based on the relevance of the generated answer, you will classify it
as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".

Here is the data for evaluation:

Query: {query}
Response: {response}

Please analyze the content and context of the generated response in relation to the query
and provide your evaluation in parsable JSON without using code blocks:

{{
  "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
  "Explanation": "[Provide a very brief explanation for your evaluation]"
}}
""".strip()


def evaluate_relevance(query, response_llm):
    evaluation_prompt = evaluation_prompt_template.format(
        query=query,
        response=response_llm
    )
    evaluation_llm, token_stats = llm(evaluation_prompt)

    try:
        json_eval = json.loads(evaluation_llm)
    except json.JSONDecodeError:
        json_eval = {"Relevance": "UNKNOWN", "Explanation": "Failed to parse evaluation"}
    return json_eval, token_stats


def calculate_a21_cost(model, tokens):
    cost = 0

    if model == "jamba-1.5-mini":
        cost = (
            tokens["prompt_tokens"] * 0.2 + tokens["completion_tokens"] * 0.4
        ) / 1e6
    elif model == "jamba-1.5-large":
        cost = (
            tokens["prompt_tokens"] * 2 + tokens["completion_tokens"] * 8
        ) / 1e6
    else:
        print("Model not recognized. AI21 cost calculation failed.")

    return cost


def rag(query, model='jamba-1.5-mini'):
    t0 = time()
    search_results = search(query)
    prompt = build_prompt(query, search_results)
    response, token_stats = llm(prompt, model=model)

    relevance, rel_token_stats = evaluate_relevance(query, response)

    t1 = time()
    delta_t = t1-t0

    a21_cost_rag = calculate_a21_cost(model, token_stats)
    a21_cost_eval = calculate_a21_cost(model, rel_token_stats)

    a21_cost = a21_cost_rag + a21_cost_eval

    response_data = {
        "response": response,
        "model_used": model,
        "response_time": delta_t,
        "relevance": relevance.get("Relevance", "UNKNOWN"),
        "relevance_explanation": relevance.get("Explanation", "Failed to parse evaluation"),
        "prompt_tokens": token_stats["prompt_tokens"],
        "completion_tokens": token_stats["completion_tokens"],
        "total_tokens": token_stats["total_tokens"],
        "eval_prompt_tokens": rel_token_stats["prompt_tokens"],
        "eval_completion_tokens": rel_token_stats["completion_tokens"],
        "eval_total_tokens": rel_token_stats["total_tokens"],
        "a21_cost": a21_cost,
    }
    return response_data