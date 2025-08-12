#This file serves as a single source of truth for all prompt templates
# used in the RAG application

QA_PROMPT_TEMPLATE = """
Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know.

Context: {context}
Question: {question}
Helpful Answer:
"""