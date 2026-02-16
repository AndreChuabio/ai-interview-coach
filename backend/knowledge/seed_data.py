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
        "answers": [
            {
                "text": (
                    "The CAP theorem states that a distributed system can guarantee at most two of "
                    "three properties: Consistency (every read returns the latest write), Availability "
                    "(every request receives a response), and Partition Tolerance (the system operates "
                    "despite network failures). In practice, partitions are inevitable, so the real "
                    "choice is between CP and AP. Banks and financial systems choose CP -- they would "
                    "rather reject a request than return stale data. Social media feeds choose AP -- "
                    "showing a slightly stale timeline is better than showing nothing. DynamoDB is AP "
                    "with eventual consistency; Spanner is CP using TrueTime for global ordering."
                ),
                "quality": "strong",
            },
        ],
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
        "answers": [
            {
                "text": (
                    "Framework: Market attractiveness, competitive landscape, entry strategy, regulatory "
                    "barriers. The wealth management market is ~$100T AUM globally but heavily regulated "
                    "(SEC, FINRA licensing). Incumbents (Schwab, Fidelity) have trust and scale. The "
                    "fintech advantage is lower fees and better UX for younger demographics. I would "
                    "recommend a niche entry: target underserved segments like mass affluent ($100K-$1M) "
                    "with automated portfolio management and tax-loss harvesting. Acquire a registered "
                    "investment advisor license rather than building compliance from scratch. Start with "
                    "a robo-advisor model (low CAC, scalable) and layer in human advisors as AUM grows. "
                    "Key metric: CAC-to-LTV ratio must exceed 3x within 18 months."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "How many electric vehicle charging stations will New York City need by 2030?",
        "interview_type": "case_study",
        "difficulty": "medium",
        "topics": ["Market Sizing"],
        "roles": ["Consulting Analyst", "Data Analyst", "Product Manager"],
        "companies": ["McKinsey", "Deloitte", "Tesla"],
        "answers": [
            {
                "text": (
                    "Top-down approach. NYC has roughly 2M registered vehicles. EV adoption projections "
                    "suggest 20-25% by 2030, so approximately 400K-500K EVs. Average EV charges 2-3 times "
                    "per week, but many will charge at home (houses, private garages) -- roughly 30% of "
                    "NYC drivers have home charging access. The remaining 70% (350K drivers) depend on "
                    "public infrastructure. Each Level 2 charger serves roughly 3-4 cars per day; DC fast "
                    "chargers serve 8-12. Assuming a mix (80% Level 2, 20% DCFC) and average 5 charges per "
                    "charger per day, we need roughly 350K * 2.5 weekly charges / 7 days / 5 charges per "
                    "charger = ~25,000 public charging ports. Current NYC has about 4,000, so the gap is "
                    "roughly 20,000 new ports by 2030."
                ),
                "quality": "strong",
            },
        ],
    },
    # =====================================================================
    # NEW BEHAVIORAL QUESTIONS (+11)
    # =====================================================================
    {
        "text": "Describe a time you worked under a very tight deadline.",
        "interview_type": "behavioral",
        "difficulty": "medium",
        "topics": ["Teamwork", "Adaptability"],
        "roles": ["Software Engineer", "Data Scientist", "Product Manager"],
        "companies": ["Google", "Amazon", "Meta"],
        "answers": [
            {
                "text": (
                    "Our team had 48 hours to ship a critical security patch after a vulnerability was "
                    "disclosed. I triaged the affected endpoints, divided the work across three engineers, "
                    "and set up a shared war-room Slack channel with 2-hour check-ins. I personally "
                    "handled the highest-risk endpoint (payment processing), wrote the fix and tests in "
                    "6 hours, and coordinated a staggered rollout starting with internal traffic. We "
                    "patched all services within 36 hours with zero customer-facing incidents. The key "
                    "was clear prioritization and constant communication."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Tell me about a time you had to make a decision with incomplete information.",
        "interview_type": "behavioral",
        "difficulty": "hard",
        "topics": ["Problem Solving", "Adaptability"],
        "roles": ["Product Manager", "Data Scientist", "Consulting Analyst"],
        "companies": ["Amazon", "Goldman Sachs", "McKinsey"],
        "answers": [
            {
                "text": (
                    "During a product launch, we had to choose between two pricing tiers but only had "
                    "survey data from 200 users -- not enough for statistical confidence. I identified "
                    "the three highest-uncertainty assumptions, built a simple sensitivity analysis in "
                    "a spreadsheet showing revenue outcomes under each scenario, and recommended the "
                    "conservative option that had the higher floor even if its ceiling was lower. We "
                    "launched at $15/month instead of $25/month, hit 140% of our sign-up target in week "
                    "one, and raised the price six months later with data to support it."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Give an example of receiving tough feedback and how you acted on it.",
        "interview_type": "behavioral",
        "difficulty": "medium",
        "topics": ["Communication", "Adaptability"],
        "roles": ["Software Engineer", "Data Scientist", "Machine Learning Engineer"],
        "companies": ["Google", "Microsoft", "Deloitte"],
        "answers": [
            {
                "text": (
                    "In a code review, a senior engineer told me my data pipeline was 'over-engineered "
                    "and hard to maintain.' My initial reaction was defensive, but I asked for specific "
                    "examples. He pointed out three unnecessary abstraction layers I had built for "
                    "flexibility that would likely never be needed. I refactored the pipeline from 12 "
                    "files to 4, reducing complexity by 60% while keeping the same functionality. I also "
                    "started applying YAGNI (You Aren't Gonna Need It) as a design principle. My next "
                    "two code reviews had zero structural comments."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Tell me about your most impactful project.",
        "interview_type": "behavioral",
        "difficulty": "medium",
        "topics": ["Leadership", "Problem Solving"],
        "roles": ["Software Engineer", "Senior Software Engineer", "Data Scientist"],
        "companies": ["Google", "Amazon", "Apple"],
        "answers": [
            {
                "text": (
                    "I built an automated anomaly detection system for our e-commerce platform that "
                    "flagged revenue drops in real time. Previously, the team discovered issues from "
                    "daily reports -- often 12-24 hours after they started. My system used statistical "
                    "process control (CUSUM) on 5-minute revenue windows and alerted the on-call "
                    "engineer via PagerDuty within 15 minutes of any significant deviation. In its "
                    "first quarter, it caught three incidents that would have cost an estimated $2.1M "
                    "in lost revenue. It became a company-wide standard."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Describe a situation where you had to manage competing priorities.",
        "interview_type": "behavioral",
        "difficulty": "medium",
        "topics": ["Problem Solving", "Communication"],
        "roles": ["Product Manager", "Consulting Analyst", "Data Scientist"],
        "companies": ["McKinsey", "Goldman Sachs", "JPMorgan Chase"],
        "answers": [
            {
                "text": (
                    "I was simultaneously supporting a quarterly earnings analysis for a senior MD and "
                    "a pitch book for a potential $500M acquisition. Both had the same deadline. I mapped "
                    "out the remaining work for each, identified which tasks were on the critical path, "
                    "and had a transparent conversation with both stakeholders about sequencing. I "
                    "proposed completing the earnings model first (2 days) since it was needed for a "
                    "client call, then shifting fully to the pitch book. I also delegated the formatting "
                    "work to an analyst. Both deliverables shipped on time and the MD specifically noted "
                    "my communication throughout."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Tell me about a time you mentored or coached someone.",
        "interview_type": "behavioral",
        "difficulty": "medium",
        "topics": ["Leadership", "Teamwork"],
        "roles": ["Senior Software Engineer", "Data Scientist", "Product Manager"],
        "companies": ["Google", "Microsoft", "Amazon"],
        "answers": [
            {
                "text": (
                    "A new hire on my team was struggling with our codebase and had missed two sprint "
                    "commitments. Instead of escalating, I set up 30-minute daily pairing sessions for "
                    "two weeks. I walked through our architecture using real PRs, explained the why "
                    "behind design decisions, and let them drive while I navigated. By week three they "
                    "were shipping independently and by month two they completed a feature that had been "
                    "on our backlog for a quarter. They later told me those sessions were the most "
                    "valuable onboarding they had experienced."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Describe a time you had to push back on a stakeholder.",
        "interview_type": "behavioral",
        "difficulty": "hard",
        "topics": ["Communication", "Conflict Resolution"],
        "roles": ["Product Manager", "Consulting Analyst", "Data Scientist"],
        "companies": ["McKinsey", "Deloitte", "Goldman Sachs"],
        "answers": [
            {
                "text": (
                    "A partner wanted us to recommend a full cloud migration for a client, but our "
                    "analysis showed a hybrid approach would save 40% in year-one costs with similar "
                    "long-term benefits. I prepared a one-page comparison showing TCO over 3 years for "
                    "both options, highlighting that the full migration had a 9-month payback period "
                    "the client could not afford. I presented it as 'here is how we maximize client "
                    "value' rather than 'you are wrong.' The partner agreed, and the client later cited "
                    "our cost-conscious approach as the reason they expanded the engagement."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Give an example of when you had to learn a new skill quickly.",
        "interview_type": "behavioral",
        "difficulty": "medium",
        "topics": ["Adaptability", "Problem Solving"],
        "roles": ["Software Engineer", "Machine Learning Engineer", "Data Scientist"],
        "companies": ["Tesla", "OpenAI", "Stripe"],
        "answers": [
            {
                "text": (
                    "Our team needed to deploy a model to edge devices for real-time inference, but "
                    "nobody had experience with ONNX Runtime or model quantization. I spent a weekend "
                    "going through the ONNX documentation and Microsoft's optimization tutorials, then "
                    "converted our PyTorch model to ONNX format and applied INT8 quantization. Latency "
                    "dropped from 120ms to 18ms with only 0.3% accuracy loss. I documented the full "
                    "pipeline and ran a knowledge-sharing session so the team could replicate it for "
                    "future models. The entire learning-to-deployment cycle took five days."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Tell me about a time you improved a process or system.",
        "interview_type": "behavioral",
        "difficulty": "medium",
        "topics": ["Problem Solving", "Leadership"],
        "roles": ["Software Engineer", "Backend Engineer", "DevOps Engineer"],
        "companies": ["Amazon", "Netflix", "Stripe"],
        "answers": [
            {
                "text": (
                    "Our deployment pipeline took 45 minutes and failed roughly 20% of the time due to "
                    "flaky integration tests. I analyzed three months of CI logs, identified the 8 "
                    "most-failing tests (all related to database state leaking between tests), and "
                    "refactored them to use isolated transactions with rollback. I also parallelized the "
                    "test suite across 4 workers. Pipeline time dropped to 12 minutes and the failure "
                    "rate fell to under 2%. The team went from deploying twice a week (because deploys "
                    "were painful) to deploying daily."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Describe a cross-functional collaboration that was challenging.",
        "interview_type": "behavioral",
        "difficulty": "medium",
        "topics": ["Teamwork", "Communication"],
        "roles": ["Product Manager", "Software Engineer", "Data Scientist"],
        "companies": ["Meta", "Apple", "Goldman Sachs"],
        "answers": [
            {
                "text": (
                    "I led the data science workstream for a cross-functional initiative involving "
                    "engineering, legal, and marketing to launch a personalization feature in the EU "
                    "under GDPR. Legal wanted minimal data collection; marketing wanted maximum "
                    "personalization; engineering wanted simplicity. I proposed a privacy-preserving "
                    "approach using differential privacy that satisfied legal, still improved click-through "
                    "rates by 12% (satisfying marketing), and used an existing ML pipeline (satisfying "
                    "engineering). The key was creating a shared document where each team listed their "
                    "non-negotiables so we could find the overlap."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Tell me about an ethical dilemma you faced at work.",
        "interview_type": "behavioral",
        "difficulty": "hard",
        "topics": ["Leadership", "Communication"],
        "roles": ["Data Scientist", "Product Manager", "Consulting Analyst"],
        "companies": ["Goldman Sachs", "McKinsey", "Palantir"],
        "answers": [
            {
                "text": (
                    "I discovered that a model we were about to deploy for loan approvals had a "
                    "significant bias: approval rates for applicants from certain zip codes were 30% "
                    "lower, even after controlling for credit score and income. The model was technically "
                    "accurate but encoded historical lending discrimination through correlated features. "
                    "I flagged it to my manager with a quantified impact analysis, proposed retraining "
                    "with fairness constraints (equalized odds), and recommended a human-in-the-loop "
                    "review for borderline cases. The launch was delayed by three weeks but the revised "
                    "model reduced the disparity to under 5% while maintaining 95% of the original "
                    "predictive performance."
                ),
                "quality": "strong",
            },
        ],
    },
    # =====================================================================
    # NEW TECHNICAL QUESTIONS (+13)
    # =====================================================================
    {
        "text": "Design a real-time stock price alerting system.",
        "interview_type": "technical",
        "difficulty": "hard",
        "topics": ["System Design"],
        "roles": ["Software Engineer", "Backend Engineer", "Quantitative Analyst"],
        "companies": ["Goldman Sachs", "JPMorgan Chase", "Two Sigma"],
        "answers": [
            {
                "text": (
                    "Ingest price feeds via WebSocket from market data providers (e.g., Bloomberg, "
                    "Reuters) into a Kafka topic partitioned by ticker symbol. A stream processor "
                    "(Flink or Kafka Streams) evaluates each price tick against user-defined alert "
                    "rules stored in Redis (e.g., AAPL > $200). When triggered, publish to a "
                    "notifications topic consumed by push notification, email, and SMS services. "
                    "For scale: millions of users with different alert thresholds. Use an inverted "
                    "index mapping price ranges to user IDs so you only evaluate relevant alerts per "
                    "tick. Deduplication via a sliding window prevents alert storms during volatility. "
                    "Latency target: under 500ms from tick to notification."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "How would you detect anomalies in a time series dataset?",
        "interview_type": "technical",
        "difficulty": "medium",
        "topics": ["Machine Learning", "Statistics"],
        "roles": ["Data Scientist", "Machine Learning Engineer", "Quantitative Analyst"],
        "companies": ["Two Sigma", "Palantir", "Netflix"],
        "answers": [
            {
                "text": (
                    "Approach depends on the data characteristics. For stationary series with known "
                    "seasonality: decompose into trend, seasonal, and residual components (STL "
                    "decomposition), then flag residuals beyond 3 standard deviations. For non-stationary "
                    "or complex patterns: use an autoencoder trained on normal behavior -- high "
                    "reconstruction error indicates anomalies. For real-time detection: Isolation Forest "
                    "or CUSUM (cumulative sum control chart) for streaming data. Always pair statistical "
                    "methods with domain context -- a 2x spike in trading volume on earnings day is "
                    "expected, not anomalous. Evaluate with precision at high recall since missing an "
                    "anomaly is typically costlier than a false alarm."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Design an autocomplete/typeahead system.",
        "interview_type": "technical",
        "difficulty": "medium",
        "topics": ["System Design", "Algorithms"],
        "roles": ["Software Engineer", "Senior Software Engineer", "Frontend Engineer"],
        "companies": ["Google", "Amazon", "Meta"],
        "answers": [
            {
                "text": (
                    "Core data structure: a trie (prefix tree) where each node stores the top-K "
                    "suggestions by popularity. Precompute suggestions at each prefix to avoid "
                    "traversal at query time. For scale: shard the trie by first two characters across "
                    "multiple servers. Use a caching layer (Redis) for hot prefixes -- the top 1000 "
                    "prefixes likely cover 80% of queries. Update popularity counts asynchronously via "
                    "a MapReduce job on search logs (hourly or daily). Personalization: maintain a small "
                    "per-user trie in the client or session cache that blends with global results. "
                    "Latency requirement: under 100ms p99. Return results after 2-3 characters to "
                    "reduce server load."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Explain how a transformer model works and why it replaced RNNs.",
        "interview_type": "technical",
        "difficulty": "hard",
        "topics": ["Machine Learning"],
        "roles": ["Machine Learning Engineer", "Data Scientist"],
        "companies": ["OpenAI", "Google", "Meta"],
        "answers": [
            {
                "text": (
                    "Transformers process entire sequences in parallel using self-attention, which "
                    "computes a weighted sum of all token representations where weights are learned "
                    "compatibility scores (query-key dot products scaled by sqrt(d_k)). Multi-head "
                    "attention lets the model attend to different relationship types simultaneously. "
                    "Positional encodings (sinusoidal or learned) inject sequence order since attention "
                    "is position-agnostic. RNNs processed tokens sequentially, creating a bottleneck: "
                    "O(n) sequential steps, vanishing gradients over long sequences, and inability to "
                    "parallelize during training. Transformers are O(1) in depth (all positions computed "
                    "simultaneously) and O(n^2) in attention computation, which is worth the tradeoff "
                    "because GPU parallelism handles it efficiently. This enabled training on much "
                    "larger datasets, leading to GPT, BERT, and modern LLMs."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "How would you optimize a slow SQL query on a table with 100M rows?",
        "interview_type": "technical",
        "difficulty": "medium",
        "topics": ["SQL & Databases"],
        "roles": ["Data Analyst", "Backend Engineer", "Data Scientist"],
        "companies": ["Amazon", "Goldman Sachs", "Palantir"],
        "answers": [
            {
                "text": (
                    "Step 1: Run EXPLAIN ANALYZE to see the query plan -- look for sequential scans, "
                    "nested loops, and sort operations. Step 2: Add indexes on columns used in WHERE, "
                    "JOIN, and ORDER BY clauses. Composite indexes for multi-column filters. Step 3: "
                    "Check for missing statistics (ANALYZE the table). Step 4: Rewrite the query -- "
                    "replace correlated subqueries with JOINs, use CTEs for readability but be aware "
                    "they can prevent optimization in some databases. Step 5: Consider partitioning "
                    "(range partition on date columns for time-series data). Step 6: For analytical "
                    "queries, materialize frequently-accessed aggregations into summary tables refreshed "
                    "on a schedule. A query that took 45 seconds with a sequential scan often drops "
                    "to under 100ms with the right composite index."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Design a notification system that handles millions of users.",
        "interview_type": "technical",
        "difficulty": "hard",
        "topics": ["System Design"],
        "roles": ["Software Engineer", "Senior Software Engineer", "Backend Engineer"],
        "companies": ["Meta", "Amazon", "Apple"],
        "answers": [
            {
                "text": (
                    "Architecture: event producers publish to a Kafka topic when a notification-worthy "
                    "event occurs. A notification service consumes events, resolves user preferences "
                    "(channels: push, email, SMS; frequency: immediate, digest, muted), and routes to "
                    "channel-specific workers. Each channel worker handles delivery: APNs for iOS, FCM "
                    "for Android, SES for email, Twilio for SMS. Use a priority queue so urgent "
                    "notifications (security alerts) bypass digest batching. Deduplication: store "
                    "event hashes in Redis with a TTL. Rate limiting per user prevents notification "
                    "fatigue. For millions of users: horizontally scale Kafka consumers by partition, "
                    "use connection pooling for external APIs, and implement exponential backoff with "
                    "dead letter queues for failures."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Explain L1 vs L2 regularization and when to use each.",
        "interview_type": "technical",
        "difficulty": "medium",
        "topics": ["Machine Learning", "Statistics"],
        "roles": ["Data Scientist", "Machine Learning Engineer", "Quantitative Analyst"],
        "companies": ["Two Sigma", "Netflix", "Palantir"],
        "answers": [
            {
                "text": (
                    "L1 (Lasso) adds the sum of absolute weights to the loss function; L2 (Ridge) "
                    "adds the sum of squared weights. L1 drives small coefficients to exactly zero, "
                    "performing automatic feature selection -- useful when you suspect many features "
                    "are irrelevant. L2 shrinks all coefficients toward zero but rarely to exactly "
                    "zero -- useful when most features contribute some signal. Geometrically, L1's "
                    "constraint region is a diamond (corners at axes encourage sparsity) while L2's "
                    "is a sphere. Use L1 when you want interpretability and have high-dimensional "
                    "sparse data. Use L2 when features are correlated (L1 arbitrarily picks one). "
                    "Elastic Net combines both and is often the best default choice."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "How would you build a recommendation engine for a streaming platform?",
        "interview_type": "technical",
        "difficulty": "hard",
        "topics": ["Machine Learning", "System Design"],
        "roles": ["Machine Learning Engineer", "Data Scientist", "Software Engineer"],
        "companies": ["Netflix", "Amazon", "Apple"],
        "answers": [
            {
                "text": (
                    "Two-stage architecture: candidate generation then ranking. Candidate generation "
                    "uses collaborative filtering (matrix factorization on the user-item interaction "
                    "matrix) to produce ~500 candidates from a catalog of millions. The ranking model "
                    "(gradient-boosted trees or a neural network) scores candidates using user features "
                    "(watch history, demographics), item features (genre, cast, release year), and "
                    "context (time of day, device). Serve rankings via a feature store (precomputed "
                    "user embeddings in Redis). Handle cold start for new users with content-based "
                    "filtering on stated preferences, and for new items with metadata similarity. "
                    "Retrain the ranking model daily on implicit feedback (watch duration, completion "
                    "rate) and run weekly A/B tests on recommendation quality."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Design a distributed cache with eviction policies.",
        "interview_type": "technical",
        "difficulty": "hard",
        "topics": ["System Design", "Data Structures"],
        "roles": ["Software Engineer", "Senior Software Engineer", "Backend Engineer"],
        "companies": ["Google", "Amazon", "Stripe"],
        "answers": [
            {
                "text": (
                    "Core: a hash map for O(1) lookups backed by a doubly-linked list for LRU "
                    "ordering. For distribution: consistent hashing assigns keys to nodes so adding "
                    "or removing a node only remaps ~1/n of keys. Each node runs the same LRU cache "
                    "locally. Replication: write to primary and async replicate to one secondary for "
                    "fault tolerance. Eviction policies: LRU (least recently used) is the default; "
                    "LFU (least frequently used) works better for workloads with stable hot keys; "
                    "TTL-based expiration for time-sensitive data. Handle thundering herd on cache "
                    "miss with a single-flight pattern: only one goroutine/thread fetches from the "
                    "backend while others wait. Monitor hit rate (target >95%), eviction rate, and "
                    "p99 latency."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Walk me through A/B testing -- how do you determine sample size and significance?",
        "interview_type": "technical",
        "difficulty": "medium",
        "topics": ["Statistics"],
        "roles": ["Data Scientist", "Product Manager", "Data Analyst"],
        "companies": ["Google", "Meta", "Netflix"],
        "answers": [
            {
                "text": (
                    "Sample size depends on four parameters: baseline conversion rate, minimum "
                    "detectable effect (MDE), significance level (alpha, typically 0.05), and "
                    "statistical power (1-beta, typically 0.80). Formula: n = (Z_alpha/2 + Z_beta)^2 "
                    "* 2 * p * (1-p) / MDE^2. For a 5% baseline with 1% MDE, you need roughly "
                    "25,000 users per variant. Run the test for at least one full business cycle "
                    "(typically 1-2 weeks) to capture day-of-week effects. At the end, compute a "
                    "two-proportion z-test or use a Bayesian approach for continuous monitoring. "
                    "Check for novelty effects by segmenting results by exposure day. Always define "
                    "the primary metric and guardrail metrics before launching."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "How would you design a data pipeline for processing 10TB of daily log data?",
        "interview_type": "technical",
        "difficulty": "hard",
        "topics": ["System Design", "SQL & Databases"],
        "roles": ["Data Scientist", "Backend Engineer", "DevOps Engineer"],
        "companies": ["Amazon", "Palantir", "Tesla"],
        "answers": [
            {
                "text": (
                    "Ingest: applications write structured logs to Kafka (partitioned by service name). "
                    "A Kafka Connect sink writes raw logs to S3 in Parquet format, partitioned by "
                    "date/hour for efficient querying. Processing: a Spark job runs hourly to clean, "
                    "deduplicate, and enrich logs (join with user and service metadata). Output lands "
                    "in a curated S3 bucket. Serving: load into a columnar warehouse (Redshift, "
                    "BigQuery, or ClickHouse) for analyst queries. For real-time use cases, maintain "
                    "a parallel Flink job that computes 5-minute aggregates (error rates, latency "
                    "percentiles) and writes to a time-series database (InfluxDB or TimescaleDB). "
                    "Monitoring: track pipeline lag, data quality checks (schema validation, null "
                    "rates), and set alerts on processing failures."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Explain gradient boosting vs random forest -- tradeoffs and when to use each.",
        "interview_type": "technical",
        "difficulty": "medium",
        "topics": ["Machine Learning"],
        "roles": ["Data Scientist", "Machine Learning Engineer", "Quantitative Analyst"],
        "companies": ["Goldman Sachs", "Two Sigma", "JPMorgan Chase"],
        "answers": [
            {
                "text": (
                    "Random forest builds many independent trees in parallel (bagging) and averages "
                    "their predictions. Gradient boosting builds trees sequentially, each correcting "
                    "the residual errors of the previous ensemble. Tradeoffs: random forest is harder "
                    "to overfit and needs less hyperparameter tuning -- good as a strong baseline. "
                    "Gradient boosting (XGBoost, LightGBM) typically achieves higher accuracy but "
                    "is sensitive to learning rate, tree depth, and number of rounds. Gradient boosting "
                    "handles imbalanced classes better with cost-sensitive loss functions. For tabular "
                    "data competitions and production ML, gradient boosting usually wins. For quick "
                    "prototyping or when training time is constrained, random forest is the safer "
                    "choice. In finance, gradient boosting is preferred for its ability to capture "
                    "nonlinear interactions between features."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Design a payment processing system that handles idempotency.",
        "interview_type": "technical",
        "difficulty": "hard",
        "topics": ["System Design"],
        "roles": ["Software Engineer", "Backend Engineer", "Senior Software Engineer"],
        "companies": ["Stripe", "Goldman Sachs", "JPMorgan Chase"],
        "answers": [
            {
                "text": (
                    "Idempotency ensures that retrying a payment request does not charge the customer "
                    "twice. Implementation: the client sends an Idempotency-Key header (a UUID) with "
                    "each request. The server stores this key in a database alongside the request hash "
                    "and result. On retry, the server checks the key -- if found, returns the stored "
                    "result without re-executing. Use a PostgreSQL table with a unique constraint on "
                    "the idempotency key. The payment flow: validate request, create a pending "
                    "transaction record, call the payment gateway (Visa/Mastercard), update the record "
                    "to success/failure. If the gateway call times out, the transaction stays pending "
                    "and a reconciliation job resolves it. Use distributed locks (Redis SETNX) to "
                    "prevent concurrent processing of the same idempotency key."
                ),
                "quality": "strong",
            },
        ],
    },
    # =====================================================================
    # NEW CASE STUDY QUESTIONS (+12)
    # =====================================================================
    {
        "text": "A major bank wants to reduce customer churn by 20%. Structure your approach.",
        "interview_type": "case_study",
        "difficulty": "hard",
        "topics": ["Profitability"],
        "roles": ["Consulting Analyst", "Data Scientist", "Product Manager"],
        "companies": ["Goldman Sachs", "JPMorgan Chase"],
        "answers": [
            {
                "text": (
                    "Framework: Define churn (account closure vs. dormancy), segment customers, "
                    "identify drivers, prioritize interventions. Step 1: Segment by value -- high-net-worth "
                    "clients churning is 10x more costly than basic account holders. Step 2: Analyze "
                    "churn drivers by segment. Common causes: better rates elsewhere, poor service "
                    "experience, life events (relocation), fee sensitivity. Use survival analysis to "
                    "identify at-risk customers 60-90 days before likely churn. Step 3: Interventions "
                    "by segment -- proactive rate matching for high-value, fee waivers for fee-sensitive, "
                    "dedicated relationship manager outreach for wealth clients. Step 4: Measure with "
                    "a control group. A 20% churn reduction on a base of 8% annual churn means moving "
                    "to 6.4%, retaining roughly 1.6% more customers -- quantify the revenue impact."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "How would you price a new premium credit card product?",
        "interview_type": "case_study",
        "difficulty": "hard",
        "topics": ["Product Strategy", "Profitability"],
        "roles": ["Product Manager", "Investment Banking Analyst", "Consulting Analyst"],
        "companies": ["Goldman Sachs", "JPMorgan Chase", "Stripe"],
        "answers": [
            {
                "text": (
                    "Revenue sources for a premium card: annual fee, interchange fees (1.5-3% of "
                    "transaction volume), interest income, and cross-sell. Cost structure: rewards "
                    "program (cashback/points), sign-up bonuses, fraud losses, servicing costs, and "
                    "credit losses. Competitive benchmarking: Amex Platinum ($695/year), Chase Sapphire "
                    "Reserve ($550/year). Pricing decision: work backwards from target margin. If "
                    "rewards cost $400/year per cardholder and servicing costs $100/year, the annual "
                    "fee must exceed $500 to break even on fee revenue alone before interchange. "
                    "Price at $550 with a strong sign-up bonus (80K points) to drive acquisition. "
                    "Key metric: break-even on total cardholder economics within 18 months including "
                    "interchange revenue. Run conjoint analysis to test willingness to pay."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "A consulting firm's utilization rate dropped from 75% to 60%. Diagnose and fix.",
        "interview_type": "case_study",
        "difficulty": "hard",
        "topics": ["Profitability"],
        "roles": ["Consulting Analyst", "Product Manager"],
        "companies": ["McKinsey", "Deloitte"],
        "answers": [
            {
                "text": (
                    "Utilization = billable hours / total available hours. A 15-point drop is severe. "
                    "Diagnose: (1) Demand side -- has the pipeline of client engagements shrunk? Check "
                    "new project wins, average project size, and proposal win rate. (2) Supply side -- "
                    "did headcount grow faster than demand (over-hiring)? (3) Staffing efficiency -- are "
                    "consultants sitting on the bench between projects due to skill mismatch or poor "
                    "staffing processes? (4) Project mix -- are projects becoming shorter, creating more "
                    "transition gaps? Fix by priority: improve staffing algorithms to reduce bench time, "
                    "freeze hiring until utilization recovers, invest in sales to rebuild pipeline, and "
                    "consider upskilling bench consultants in high-demand practice areas. Target: recover "
                    "to 70% within two quarters."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Should a tech company enter the healthcare market? Structure the analysis.",
        "interview_type": "case_study",
        "difficulty": "hard",
        "topics": ["Growth Strategy"],
        "roles": ["Product Manager", "Consulting Analyst", "Data Scientist"],
        "companies": ["Google", "Amazon", "Apple"],
        "answers": [
            {
                "text": (
                    "Framework: Market attractiveness, right to win, barriers, and risk. Market: US "
                    "healthcare is $4.3T with massive inefficiency -- ~30% is waste (admin, redundant "
                    "testing). Attractive size and pain points. Right to win: a tech company brings "
                    "data infrastructure, AI capabilities, and consumer UX expertise. Entry points: "
                    "EHR integration, AI-powered diagnostics, patient engagement, or claims processing "
                    "automation. Barriers: HIPAA compliance (costly, 12-18 month certification), "
                    "provider trust (hospitals are risk-averse), and long sales cycles (6-18 months). "
                    "Recommendation: enter via a partnership or acquisition of a HIPAA-compliant startup "
                    "rather than building compliance from scratch. Start with a narrow wedge (e.g., "
                    "radiology AI or administrative automation) and expand. Risk: regulatory change "
                    "and reputational damage if patient data is mishandled."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Estimate the number of Uber rides taken daily in Manhattan.",
        "interview_type": "case_study",
        "difficulty": "medium",
        "topics": ["Market Sizing"],
        "roles": ["Consulting Analyst", "Data Analyst", "Product Manager"],
        "companies": ["McKinsey", "Deloitte"],
        "answers": [
            {
                "text": (
                    "Manhattan population: ~1.6M residents plus ~3M daily commuters = ~4.6M people on "
                    "a typical weekday. Not everyone uses rideshare: estimate 15% use Uber/Lyft on any "
                    "given day = ~690K potential riders. Average rides per rider per day: ~1.3 (some "
                    "take one ride, some take round trips). Total ride demand: ~900K rides/day across "
                    "all rideshare. Uber market share in NYC is roughly 60-65%. So Uber rides in "
                    "Manhattan: ~900K * 0.62 = ~560K rides per day. Cross-check: NYC TLC data shows "
                    "roughly 500K-600K rideshare trips daily across all boroughs; Manhattan accounts "
                    "for about 60-70% of trips. That gives ~350K-420K, suggesting my estimate is "
                    "slightly high but in the right ballpark. Adjust to ~450K as a best estimate."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "A retail chain is considering closing 30% of its stores. Advise.",
        "interview_type": "case_study",
        "difficulty": "hard",
        "topics": ["Profitability", "Growth Strategy"],
        "roles": ["Consulting Analyst", "Product Manager", "Data Analyst"],
        "companies": ["McKinsey", "Amazon"],
        "answers": [
            {
                "text": (
                    "Framework: store-level profitability, cannibalization analysis, strategic value. "
                    "Step 1: Rank stores by 4-wall profitability (revenue minus direct costs including "
                    "rent, labor, inventory). The bottom 30% are candidates. Step 2: Cannibalization -- "
                    "closing a store redirects some sales to nearby stores and online. Model the recapture "
                    "rate (typically 20-40% for retail). A store losing $200K/year but redirecting $300K "
                    "to profitable nearby locations is a net positive close. Step 3: Strategic value -- "
                    "some unprofitable stores serve as brand presence in key markets or drive online "
                    "sales (BOPIS). Step 4: Lease obligations -- early termination penalties may make "
                    "it cheaper to ride out the lease. Recommendation: close stores that are unprofitable "
                    "AND have high recapture potential AND no strategic value. This is typically 15-20% "
                    "of the fleet, not necessarily the full 30%."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "How would you monetize a social media platform without advertising?",
        "interview_type": "case_study",
        "difficulty": "medium",
        "topics": ["Product Strategy"],
        "roles": ["Product Manager", "Consulting Analyst"],
        "companies": ["Meta", "Apple"],
        "answers": [
            {
                "text": (
                    "Revenue streams beyond ads: (1) Subscription tier -- premium features like "
                    "analytics for creators, ad-free experience, enhanced messaging (Twitter/X Blue "
                    "model). Target: 2-5% of MAU at $8-12/month. (2) Commerce -- take a percentage "
                    "of in-app purchases, creator merchandise, or tipping (like TikTok Creator Fund). "
                    "(3) Data licensing -- anonymized, aggregated trend data sold to market research "
                    "firms and brands (with strict privacy compliance). (4) Enterprise tools -- "
                    "business accounts with CRM integrations, scheduling, and team management "
                    "(like LinkedIn Premium). (5) Virtual goods and digital identity -- profile "
                    "customization, badges, verified status. Best bet for a large platform: subscription "
                    "plus commerce. For a platform with 100M MAU, 3% subscription adoption at $10/month "
                    "= $360M ARR before commerce revenue."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "A food delivery company wants to expand to grocery delivery. Evaluate.",
        "interview_type": "case_study",
        "difficulty": "medium",
        "topics": ["Growth Strategy", "Market Sizing"],
        "roles": ["Product Manager", "Consulting Analyst", "Data Analyst"],
        "companies": ["Amazon", "Deloitte"],
        "answers": [
            {
                "text": (
                    "Synergies: existing driver fleet, last-mile logistics expertise, customer base "
                    "with delivery app installed, and demand data on neighborhoods. Challenges: grocery "
                    "has 2-3% margins vs 15-20% for restaurant delivery; requires cold chain "
                    "infrastructure (refrigerated storage, insulated bags); different fulfillment "
                    "(picking 30+ items vs one bag from a restaurant); and entrenched competitors "
                    "(Instacart, Walmart, Amazon Fresh). Recommendation: start with a dark store "
                    "model in 2-3 high-density markets rather than partnering with existing grocers. "
                    "Limit SKUs to 2,000 high-velocity items (not full grocery). This reduces pick "
                    "time and inventory complexity. Target basket size: $35+ to achieve positive unit "
                    "economics with a $3.99 delivery fee. Evaluate after 6 months: if order density "
                    "exceeds 100/day/store, expand to more markets."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "An AI startup is choosing between B2B and B2C go-to-market. Advise.",
        "interview_type": "case_study",
        "difficulty": "medium",
        "topics": ["Growth Strategy", "Product Strategy"],
        "roles": ["Product Manager", "Consulting Analyst"],
        "companies": ["OpenAI", "Stripe", "Google"],
        "answers": [
            {
                "text": (
                    "Key factors: unit economics, sales cycle, defensibility, and capital efficiency. "
                    "B2B: higher ACV ($10K-$500K/year), longer sales cycles (3-9 months), requires "
                    "enterprise features (SSO, audit logs, SLAs), but lower churn (5-10% annual) and "
                    "more predictable revenue. B2C: lower price ($10-50/month), viral acquisition "
                    "potential, faster iteration cycles, but high churn (5-10% monthly) and high CAC "
                    "if relying on paid marketing. For an AI startup with limited funding: B2B is "
                    "typically more capital-efficient because fewer customers generate meaningful "
                    "revenue. However, if the product has strong viral/word-of-mouth potential "
                    "(like ChatGPT), B2C can build a massive user base that later converts to B2B. "
                    "Hybrid approach: launch B2C freemium to build brand and usage data, then layer "
                    "B2B enterprise offering on top (the 'land and expand' from bottom-up)."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "Estimate the annual revenue of a single Starbucks location in NYC.",
        "interview_type": "case_study",
        "difficulty": "medium",
        "topics": ["Market Sizing"],
        "roles": ["Consulting Analyst", "Data Analyst", "Investment Banking Analyst"],
        "companies": ["McKinsey", "Goldman Sachs"],
        "answers": [
            {
                "text": (
                    "Operating hours: roughly 5am-9pm = 16 hours. Divide into peak and off-peak. "
                    "Morning peak (5am-10am, 5 hours): ~80 transactions/hour = 400 transactions. "
                    "Lunch peak (11am-2pm, 3 hours): ~50/hour = 150. Off-peak (remaining 8 hours): "
                    "~25/hour = 200. Total daily transactions: ~750. Average ticket: $5.50 (coffee "
                    "$4.50 average, 30% of customers add food at $4.00). Daily revenue: 750 * $5.50 "
                    "= ~$4,125. Annual revenue (365 days, Starbucks opens every day): $4,125 * 365 "
                    "= ~$1.5M. Cross-check: Starbucks reports average US store revenue of ~$1.8M. "
                    "NYC locations likely outperform average due to foot traffic and higher prices, "
                    "so adjust upward to ~$1.8-2.2M. A high-traffic Manhattan location could hit $2.5M+."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "A streaming platform's subscriber growth has stalled. Diagnose and propose solutions.",
        "interview_type": "case_study",
        "difficulty": "hard",
        "topics": ["Growth Strategy", "Product Strategy"],
        "roles": ["Product Manager", "Consulting Analyst", "Data Analyst"],
        "companies": ["Netflix", "Amazon", "Apple"],
        "answers": [
            {
                "text": (
                    "Diagnose: (1) Market saturation -- what is penetration vs TAM? If at 70%+ of "
                    "addressable households, organic growth naturally slows. (2) Content pipeline -- "
                    "has content spend or release cadence changed? Subscribers correlate with tentpole "
                    "releases. (3) Competitive pressure -- are subscribers churning to competitors or "
                    "is new subscriber acquisition slowing? Check churn vs acquisition separately. "
                    "(4) Pricing sensitivity -- did a recent price increase cause a demand response? "
                    "Solutions by diagnosis: For saturation -- launch an ad-supported tier at lower "
                    "price to capture price-sensitive segments, expand internationally (focus on markets "
                    "with growing middle class like India, Brazil). For content -- invest in local-language "
                    "content for international markets. For competition -- introduce bundling (streaming + "
                    "gaming + music) to increase switching costs. For pricing -- introduce annual plans "
                    "with a discount to lock in subscribers and reduce monthly churn."
                ),
                "quality": "strong",
            },
        ],
    },
    {
        "text": "How would you evaluate whether a fintech company should build or buy its compliance infrastructure?",
        "interview_type": "case_study",
        "difficulty": "hard",
        "topics": ["Product Strategy", "Profitability"],
        "roles": ["Product Manager", "Investment Banking Analyst", "Consulting Analyst"],
        "companies": ["Stripe", "Goldman Sachs"],
        "answers": [
            {
                "text": (
                    "Framework: cost comparison, time-to-market, strategic value, and risk. Build: "
                    "estimated 12-18 months, $2-5M in engineering costs, plus ongoing maintenance "
                    "(2-3 engineers dedicated). Gives full control and customization, but diverts "
                    "engineering resources from core product. Buy: $200K-$500K/year for a compliance "
                    "SaaS platform (e.g., Alloy, Unit21), operational within 2-4 months. Less "
                    "customizable but frees engineering to focus on revenue-generating features. Key "
                    "question: is compliance a differentiator or table stakes? For most fintechs, it "
                    "is table stakes -- buy. For companies where compliance IS the product (RegTech), "
                    "build. Recommendation for a typical fintech: buy for the first 2-3 years to move "
                    "fast, then evaluate building when scale makes the SaaS cost exceed build cost "
                    "(usually around $1M+ annually in vendor fees)."
                ),
                "quality": "strong",
            },
        ],
    },
]
