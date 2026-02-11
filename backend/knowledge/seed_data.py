"""
Curated seed data for the knowledge graph.

Contains companies, roles, interview questions with example answers,
topics, and the relationships between them.  This data is loaded into
Neo4j by the seeder script.
"""

COMPANIES = [
    {"name": "Google", "industry": "Technology", "description": "Search, cloud, AI"},
    {"name": "Amazon", "industry": "Technology / E-Commerce", "description": "E-commerce, AWS, logistics"},
    {"name": "Meta", "industry": "Technology / Social Media", "description": "Social media, VR, advertising"},
    {"name": "Apple", "industry": "Technology / Consumer Electronics", "description": "Hardware, software, services"},
    {"name": "Microsoft", "industry": "Technology", "description": "Cloud, enterprise software, AI"},
    {"name": "Netflix", "industry": "Entertainment / Technology", "description": "Streaming, content, recommendation"},
    {"name": "Goldman Sachs", "industry": "Finance", "description": "Investment banking, trading, asset management"},
    {"name": "JPMorgan Chase", "industry": "Finance", "description": "Banking, asset management, trading"},
    {"name": "McKinsey", "industry": "Consulting", "description": "Strategy consulting, transformation"},
    {"name": "Deloitte", "industry": "Consulting / Professional Services", "description": "Audit, consulting, advisory"},
    {"name": "Tesla", "industry": "Automotive / Technology", "description": "EVs, energy, autonomous driving"},
    {"name": "Stripe", "industry": "Fintech", "description": "Payment processing, financial infrastructure"},
    {"name": "OpenAI", "industry": "AI / Technology", "description": "AI research, language models, safety"},
    {"name": "Palantir", "industry": "Technology / Defense", "description": "Data analytics, government, enterprise"},
    {"name": "Two Sigma", "industry": "Finance / Quantitative", "description": "Quantitative hedge fund, data science"},
]

ROLES = [
    {"name": "Software Engineer", "level": "mid"},
    {"name": "Senior Software Engineer", "level": "senior"},
    {"name": "Data Scientist", "level": "mid"},
    {"name": "Machine Learning Engineer", "level": "mid"},
    {"name": "Product Manager", "level": "mid"},
    {"name": "Data Analyst", "level": "entry"},
    {"name": "Quantitative Analyst", "level": "mid"},
    {"name": "Frontend Engineer", "level": "mid"},
    {"name": "Backend Engineer", "level": "mid"},
    {"name": "DevOps Engineer", "level": "mid"},
    {"name": "Consulting Analyst", "level": "entry"},
    {"name": "Investment Banking Analyst", "level": "entry"},
]

TOPICS = [
    {"name": "System Design", "category": "technical"},
    {"name": "Algorithms", "category": "technical"},
    {"name": "Data Structures", "category": "technical"},
    {"name": "Machine Learning", "category": "technical"},
    {"name": "SQL & Databases", "category": "technical"},
    {"name": "Statistics", "category": "technical"},
    {"name": "Leadership", "category": "behavioral"},
    {"name": "Conflict Resolution", "category": "behavioral"},
    {"name": "Teamwork", "category": "behavioral"},
    {"name": "Problem Solving", "category": "behavioral"},
    {"name": "Adaptability", "category": "behavioral"},
    {"name": "Communication", "category": "behavioral"},
    {"name": "Market Sizing", "category": "case_study"},
    {"name": "Profitability", "category": "case_study"},
    {"name": "Growth Strategy", "category": "case_study"},
    {"name": "Product Strategy", "category": "case_study"},
]


# Each entry: question text, interview_type, difficulty, topics, roles, companies, example_answers
QUESTIONS_WITH_CONTEXT = [
    # --- Behavioral ---
    {
        "text": "Tell me about a time you had to lead a project with minimal guidance.",
        "interview_type": "behavioral",
        "difficulty": "medium",
        "topics": ["Leadership", "Problem Solving"],
        "roles": ["Software Engineer", "Senior Software Engineer", "Product Manager"],
        "companies": ["Google", "Amazon", "Meta"],
        "answers": [
            {
                "text": (
                    "At my previous company, our team lead left mid-sprint during a critical migration "
                    "from monolith to microservices. I stepped up and organized daily standups, broke the "
                    "remaining work into clear tasks, and set up a shared Kanban board. I identified the "
                    "riskiest component -- the auth service -- and paired with our junior engineer to tackle "
                    "it first. We delivered two days ahead of schedule. The experience taught me that "
                    "leadership is about removing blockers, not having all the answers."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Describe a time you had a disagreement with a colleague. How did you resolve it?",
        "interview_type": "behavioral",
        "difficulty": "medium",
        "topics": ["Conflict Resolution", "Communication"],
        "roles": ["Software Engineer", "Data Scientist", "Product Manager"],
        "companies": ["Google", "Microsoft", "McKinsey"],
        "answers": [
            {
                "text": (
                    "A senior engineer and I disagreed on whether to use GraphQL or REST for a new API. "
                    "Instead of debating opinions, I proposed we each write a one-page comparison with "
                    "concrete tradeoffs for our specific use case -- request volume, caching needs, and "
                    "client diversity. We presented to the team, and it became clear that REST was better "
                    "for our high-cache, low-complexity endpoints. The key was making it about data, "
                    "not egos."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Tell me about a time you failed. What did you learn?",
        "interview_type": "behavioral",
        "difficulty": "medium",
        "topics": ["Adaptability", "Problem Solving"],
        "roles": ["Software Engineer", "Data Scientist", "Machine Learning Engineer"],
        "companies": ["Amazon", "Meta", "Netflix"],
        "answers": [
            {
                "text": (
                    "I deployed a model to production that had excellent offline metrics but performed "
                    "poorly in A/B testing. The issue was data leakage -- a feature derived from the "
                    "target variable was included during training. I learned to always validate feature "
                    "pipelines independently, implement strict train/test temporal splits, and run "
                    "sanity checks on feature importance before any deployment. I also introduced a "
                    "pre-deployment checklist to our team that prevented similar issues."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Give me an example of when you had to influence without authority.",
        "interview_type": "behavioral",
        "difficulty": "hard",
        "topics": ["Leadership", "Communication"],
        "roles": ["Product Manager", "Data Scientist", "Consulting Analyst"],
        "companies": ["McKinsey", "Deloitte", "Google"],
        "answers": [
            {
                "text": (
                    "As a data scientist, I noticed our recommendation engine had a cold-start problem "
                    "for new users. I built a prototype using collaborative filtering with implicit "
                    "signals and presented the results to the product team with clear A/B test projections. "
                    "I framed the pitch around their OKRs -- improving Day-7 retention by 3-5%. They "
                    "allocated engineering resources the next sprint. The key was speaking their language "
                    "(business metrics) rather than mine (model architecture)."
                ),
                "quality": "strong",
            },
        ],
    },
    # --- Technical ---
    {
        "text": "Design a URL shortener service. Walk me through the system architecture.",
        "interview_type": "technical",
        "difficulty": "medium",
        "topics": ["System Design"],
        "roles": ["Software Engineer", "Senior Software Engineer", "Backend Engineer"],
        "companies": ["Google", "Amazon", "Stripe"],
        "answers": [
            {
                "text": (
                    "The core components: a hash function to generate short codes (base62 encoding of "
                    "an auto-incrementing ID or MD5 truncation), a key-value store (Redis for hot lookups, "
                    "PostgreSQL for persistence), and a redirect service. For scale, I would use consistent "
                    "hashing to shard the key space across multiple Redis instances, put a CDN in front "
                    "for popular links, and use a write-ahead log for durability. Read-to-write ratio "
                    "is roughly 100:1, so the architecture is read-optimized. Rate limiting via token "
                    "bucket prevents abuse."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Explain the bias-variance tradeoff and how it affects model selection.",
        "interview_type": "technical",
        "difficulty": "medium",
        "topics": ["Machine Learning", "Statistics"],
        "roles": ["Data Scientist", "Machine Learning Engineer", "Quantitative Analyst"],
        "companies": ["Google", "Two Sigma", "Palantir", "Netflix"],
        "answers": [
            {
                "text": (
                    "Bias measures how far off predictions are from truth on average -- high bias means "
                    "underfitting. Variance measures how much predictions change across different training "
                    "sets -- high variance means overfitting. Total error decomposes into bias squared "
                    "plus variance plus irreducible noise. Simple models (linear regression) have high "
                    "bias, low variance. Complex models (deep nets, random forests with many trees) have "
                    "low bias, high variance. In practice, I use cross-validation to find the sweet spot "
                    "and regularization (L1/L2) to control variance without sacrificing too much bias."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "How would you design a rate limiter for an API?",
        "interview_type": "technical",
        "difficulty": "medium",
        "topics": ["System Design"],
        "roles": ["Software Engineer", "Backend Engineer", "Senior Software Engineer"],
        "companies": ["Stripe", "Amazon", "Meta"],
        "answers": [
            {
                "text": (
                    "I would use the sliding window log algorithm for precision or token bucket for "
                    "simplicity. Implementation: Redis sorted sets keyed by user ID, with timestamps "
                    "as scores. On each request, remove expired entries, count remaining, reject if "
                    "over limit. For distributed systems, use a centralized Redis cluster with Lua "
                    "scripts for atomic check-and-increment. Return 429 status with Retry-After header. "
                    "Different tiers get different limits. Monitor with dashboards tracking rejection "
                    "rates per endpoint."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Walk me through how you would build a fraud detection model from scratch.",
        "interview_type": "technical",
        "difficulty": "hard",
        "topics": ["Machine Learning", "Statistics"],
        "roles": ["Data Scientist", "Machine Learning Engineer"],
        "companies": ["Stripe", "JPMorgan Chase", "Goldman Sachs", "Palantir"],
        "answers": [
            {
                "text": (
                    "First, define the label: what constitutes fraud (chargebacks, manual reviews). "
                    "Handle class imbalance via SMOTE or cost-sensitive learning. Feature engineering: "
                    "transaction velocity, amount deviation from user mean, geolocation anomalies, "
                    "device fingerprinting, time-since-last-transaction. Start with gradient boosting "
                    "(XGBoost/LightGBM) for interpretability and speed. Evaluate with precision-recall "
                    "curves (not accuracy) since false positives have high cost. Deploy with a two-stage "
                    "system: fast rules engine for obvious fraud, then ML model for borderline cases. "
                    "Set up a feedback loop where analyst decisions retrain the model weekly."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Explain the CAP theorem and its practical implications.",
        "interview_type": "technical",
        "difficulty": "medium",
        "topics": ["System Design", "SQL & Databases"],
        "roles": ["Software Engineer", "Backend Engineer", "Senior Software Engineer"],
        "companies": ["Amazon", "Google", "Netflix"],
        "answers": [],
    },
    {
        "text": "Write a query to find the second highest salary in each department.",
        "interview_type": "technical",
        "difficulty": "medium",
        "topics": ["SQL & Databases"],
        "roles": ["Data Analyst", "Data Scientist", "Backend Engineer"],
        "companies": ["Goldman Sachs", "JPMorgan Chase", "Amazon"],
        "answers": [
            {
                "text": (
                    "Using a window function: SELECT department, salary FROM "
                    "(SELECT department, salary, DENSE_RANK() OVER (PARTITION BY department "
                    "ORDER BY salary DESC) AS rnk FROM employees) ranked WHERE rnk = 2. "
                    "DENSE_RANK handles ties correctly -- if two people share the top salary, "
                    "the next distinct salary gets rank 2. Alternative approach using a correlated "
                    "subquery: SELECT department, MAX(salary) FROM employees e1 WHERE salary < "
                    "(SELECT MAX(salary) FROM employees e2 WHERE e1.department = e2.department) "
                    "GROUP BY department."
                ),
                "quality": "strong",
            },
        ],
    },
    # --- Case Study ---
    {
        "text": "Estimate the total addressable market for AI-powered interview preparation tools.",
        "interview_type": "case_study",
        "difficulty": "medium",
        "topics": ["Market Sizing"],
        "roles": ["Product Manager", "Consulting Analyst", "Data Analyst"],
        "companies": ["McKinsey", "Deloitte", "Google"],
        "answers": [
            {
                "text": (
                    "Start with the job seeker population: approximately 160M people in the US labor "
                    "force, with roughly 6M unemployed and 4M annual new graduates actively interviewing. "
                    "Add employed job seekers (about 15% passively looking) -- roughly 24M. Total "
                    "addressable: ~34M active interview candidates in the US. Globally, multiply by ~3x "
                    "for English-speaking markets: ~100M. Willingness to pay: assume 20% would use a paid "
                    "tool at $20/month average. TAM = 100M * 20% * $20 * 12 = $4.8B annually. Narrow to "
                    "SAM (AI-specific, early adopters): maybe 5% of TAM = ~$240M."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "A SaaS company's margins dropped 15% despite growing revenue. Diagnose the problem.",
        "interview_type": "case_study",
        "difficulty": "hard",
        "topics": ["Profitability"],
        "roles": ["Product Manager", "Consulting Analyst", "Data Analyst"],
        "companies": ["McKinsey", "Deloitte", "Goldman Sachs"],
        "answers": [
            {
                "text": (
                    "Framework: Revenue vs. Cost decomposition. Revenue is growing, so the issue is on "
                    "the cost side or revenue quality. Check: (1) Customer mix shift -- are they acquiring "
                    "lower-ARPU customers or giving deeper discounts? (2) CAC inflation -- is the cost "
                    "to acquire each customer rising faster than LTV? (3) Infrastructure costs -- did they "
                    "scale servers/cloud spend ahead of revenue? (4) Headcount -- did they hire aggressively? "
                    "(5) Churn -- is gross churn stable? Revenue can grow while net revenue retention falls. "
                    "Most likely diagnosis: rapid customer acquisition via discounting combined with "
                    "infrastructure scaling ahead of actual demand."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "A fintech startup wants to enter the wealth management space. How should they approach this?",
        "interview_type": "case_study",
        "difficulty": "hard",
        "topics": ["Growth Strategy", "Product Strategy"],
        "roles": ["Product Manager", "Consulting Analyst", "Investment Banking Analyst"],
        "companies": ["Goldman Sachs", "JPMorgan Chase", "McKinsey", "Stripe"],
        "answers": [],
    },
    {
        "text": "How many electric vehicle charging stations will New York City need by 2030?",
        "interview_type": "case_study",
        "difficulty": "medium",
        "topics": ["Market Sizing"],
        "roles": ["Consulting Analyst", "Data Analyst", "Product Manager"],
        "companies": ["McKinsey", "Deloitte", "Tesla"],
        "answers": [],
    },
]
