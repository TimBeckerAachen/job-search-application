import json
from time import time
from ai21 import AI21Client
from ai21.models.chat import ChatMessage

from job_search_application import ingest

client = AI21Client()
index = ingest.load_index()


def search(query):
    boost = {
      'title': 2.37,
      'company': 2.19,
      'locations': 0.22,
      'skills': 1.71,
      'posted_at': 1.77,
      'is_remote': 0.29,
      'snippet_fragments': 1.96,
      'description': 0.08
    }

    results = index.search(
        query=query,
        filter_dict={},
        boost_dict=boost,
        num_results=5
    )

    return results


prompt_template = """
You're an expert job application coach. Answer the QUESTION based on the CONTEXT provided from the job database, 
using only the information available. Avoid making assumptions, and if necessary information is missing, acknowledge it.

Please respond concisely and focus on key details relevant to the QUESTION. Structure your response to be user-friendly 
and actionable.

If the CONTEXT lacks enough information, respond with: "The job posting does not provide enough information to answer 
your question directly."

QUESTION: {question}

CONTEXT:
{context}
""".strip()

entry_template = """
job_title: {title}
company_name: {company}
work_locations: {locations}  # List all locations where the position is based
highlighted_skills: {skills}  # Key skills mentioned in the job posting
posting_date: {posted_at}  # When was this job posted
short_summary: {snippet_fragments}  # Brief summary or main highlights of the job
full_description: {description}  # Complete details and requirements for the position
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