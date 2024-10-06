# job-search-application
Application using a LLM to help you analysis relevant job postings. For This a RAG 
approach is used. Job postings are retrieved that contain content that is relevant to 
the user question. 

TODO: put into chatGPT with example of the data, add what is required 
TODO: description of the dataset

Problem description
0 points: The problem is not described
1 point: The problem is described but briefly or unclearly
2 points: The problem is well-described and it's clear what problem the project solves

## Running it

Please create a virtual environment and install the requirements which are given in the
`requirements.txt` file.

## Interface

## Evaluation

## Retrival

## RAG flow

## Monitoring

## Ingestion

## Docker help

docker ps
docker stop $(docker ps -aq) && docker rm $(docker ps -aq)

docker ps -a
docker logs id

docker build -t job-search-app .
docker run -it --rm -p 8000:8000 -e AI21_API_KEY=${AI21_API_KEY} job-search-app
docker exec -it 07e4691c4a2f /bin/bash