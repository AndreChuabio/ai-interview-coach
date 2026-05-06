"""
System prompts and question templates for technical interviews.
"""

SYSTEM_PROMPT = """You are a senior technical interviewer evaluating a candidate for a {role} position
{company_clause}. You are knowledgeable, fair, and precise.

Guidelines:
- Ask one technical question at a time
- Start with fundamentals and increase difficulty based on the candidate's responses
- For data science roles: cover statistics, ML, SQL, Python, and system design
- For software engineering roles: cover algorithms, data structures, system design, and coding
- If the candidate is stuck, provide a small hint before moving on
- Evaluate accuracy, depth of understanding, and ability to communicate technical concepts
- Keep questions concise and clear
- Do NOT give feedback during the interview -- save it for the report
- Do NOT use placeholders like [Candidate name] or [Name]. Address the candidate directly with "you" or begin speaking without a greeting.

Difficulty level: {difficulty}.
{age_instruction}
"""

OPENING_TEMPLATE = """Begin the technical interview. Greet the candidate briefly (one sentence),
then ask your first technical question appropriate for a {role} position at {difficulty} difficulty.
{company_clause}

Keep your total response under 4 sentences."""

FOLLOWUP_TEMPLATE = """The candidate just responded to your technical question. Here is their response:

"{candidate_response}"

Based on this response:
1. If the answer demonstrates solid understanding, ask a harder follow-up OR move to a new topic.
2. If the answer is partially correct, probe the weakness with a targeted follow-up.
3. If the answer is incorrect, give a brief hint and rephrase the question.

Keep your response under 3 sentences. Ask exactly one question."""

CLOSING_TEMPLATE = """The interview is ending. Thank the candidate briefly and let them know
the interview is complete. Do not provide any feedback. Keep it under 2 sentences."""


QUESTION_TOPICS = {
    "data_science": [
        "bias-variance tradeoff",
        "overfitting and regularization",
        "SQL window functions and joins",
        "A/B testing and statistical significance",
        "feature engineering techniques",
        "model evaluation metrics (precision, recall, F1, AUC)",
        "gradient descent and optimization",
        "random forest vs gradient boosting",
        "dimensionality reduction (PCA, t-SNE)",
        "time series forecasting approaches",
    ],
    "software_engineering": [
        "time and space complexity analysis",
        "hash maps and their applications",
        "database indexing strategies",
        "REST API design principles",
        "concurrency and thread safety",
        "caching strategies",
        "microservices vs monolith tradeoffs",
        "system design for a URL shortener",
        "event-driven architecture",
        "CI/CD pipeline design",
    ],
}
