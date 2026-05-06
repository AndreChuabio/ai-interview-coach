"""
Prompts for the class-materials card pipeline.

Two passes:
  1. CONCEPT_EXTRACTION_*  - given a batch of source snippets, the model
     lists the 1-3 most important teachable concepts per snippet.
  2. CARD_SYNTHESIS_*      - given one concept plus its source chunk, the
     model writes one short-answer flashcard.

Both prompts return strict JSON and are invoked via
``LLMProvider.chat_json``.
"""

CONCEPT_EXTRACTION_SYSTEM = """You extract teachable concepts from class
notes for a short-answer flashcard trainer. You return STRICT JSON.

Rules:
- A concept is a named idea, formula, definition, procedure, or theorem
  that a student could be quizzed on in 2-4 sentences.
- Only include concepts clearly supported by the source text -- do not
  invent from outside knowledge.
- Keep 'term' to at most 8 words. Keep 'definition' to at most 2 sentences.
- Prefer specific over vague ("bias-variance tradeoff" beats "machine
  learning basics").
- If a snippet has no teachable concepts, return no concepts for it -- do
  not pad.
"""


CONCEPT_EXTRACTION_USER = """For each numbered source snippet below, extract
1 to 3 of the most important teachable concepts. If a snippet has nothing
quiz-worthy, return no concepts for it.

Return JSON with this exact shape:

{{
  "concepts": [
    {{"term": "...", "definition": "...", "source_index": 0}},
    ...
  ]
}}

Source snippets:
{snippets_block}
"""


CARD_SYNTHESIS_SYSTEM = """You write short-answer flashcards for a
technical interview trainer. You return STRICT JSON.

Rules:
- The question must be answerable in 2-4 sentences by a student who studied
  the material.
- Do NOT leak the answer inside the question.
- The reference answer should be concise but specific -- include the key
  mechanism or formula.
- The topic tag is 2-4 words describing the broader subject area.
- Stay grounded in the source context; do not introduce facts not in it.
"""


CARD_SYNTHESIS_USER = """Write ONE flashcard for the concept below.

Term: {term}
Brief definition (reference only): {definition}

Source context (authoritative; the answer must be consistent with this):
\"\"\"
{chunk_text}
\"\"\"

Return JSON with this exact shape:

{{
  "question": "...",
  "reference_answer": "...",
  "topic": "...",
  "difficulty": "easy" | "medium" | "hard"
}}
"""
