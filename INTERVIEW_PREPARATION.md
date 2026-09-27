# Interview Preparation: AI Business Intelligence System

This guide is based on the current implementation, not only the original specification. Be honest in an interview: MySQL live authentication, external LLM execution, and Power BI refresh are prepared but not fully validated in this environment.

## Senior Interviewer Assessment

### 1. Technical concepts demonstrated

- Synthetic data generation with controlled business patterns and reproducible seeds.
- Relational data modeling with customers, products, orders, and order items.
- Primary keys, foreign keys, indexes, constraints, and normalized table design.
- Pandas-based data loading, joins, grouping, aggregation, segmentation, and KPI calculation.
- Feature engineering for customer churn.
- Classification with Logistic Regression and Random Forest.
- One-hot encoding, missing-value imputation, scaling, class weighting, and pipelines.
- Precision, recall, F1-score, confusion matrix, and ROC-AUC evaluation.
- Train/validation/holdout evaluation and target-leakage prevention.
- Flask application factory, blueprints, REST endpoints, JSON contracts, and error handlers.
- HTML/CSS/JavaScript dashboard development and API integration.
- Grounded natural-language question routing through approved analytics tools.
- Read-only SQL validation and identifier allow-listing.
- Environment-based configuration and basic logging.
- Power BI dimensional modeling and DAX design.
- Automated tests for ML, API, assistant, and database-security behavior.

### 2. Genuinely strong parts

- The project has a coherent end-to-end shape: data generation, analytics, ML, API, frontend, assistant, and BI documentation.
- The data generator creates linked tables rather than unrelated random CSVs and validates foreign-key relationships.
- The schema correctly represents order-level and order-line-level grains.
- The churn pipeline uses reusable scikit-learn pipelines and more appropriate metrics than accuracy alone.
- Target leakage was identified and removed from the model segment feature.
- The assistant defaults to deterministic, verified analytics instead of inventing answers.
- The API has consistent JSON errors and test coverage across its endpoints.
- The project contains security-focused tests rather than only happy-path tests.

### 3. Superficial or incomplete parts

- MySQL is designed and scripted, but local authentication prevented a complete live database validation.
- The assistant is primarily a keyword-to-tool router. The external LLM provider is abstracted but not the source of the final answer.
- Power BI is documented, but no PBIX file or live refresh result exists.
- The frontend is a custom dashboard with CSS/SVG-style visualizations, not a production charting system with browser automation.
- The dataset is synthetic, and the exact time at which churn is observed is not modeled. Temporal leakage cannot be completely ruled out.
- Authentication, authorization, rate limiting, and production deployment are not implemented.
- The ML model is suitable for demonstration, not yet for operational retention decisions.

### 4. Concepts to understand before the interview

- The grain of every table and why joining `orders` to `order_items` can duplicate order-level values.
- Why revenue is calculated from `order_items.line_total` for product/category analysis.
- Why `DISTINCTCOUNT(orders.order_id)` is needed for order counts.
- How customer segmentation differs from churn prediction.
- Why using `churn` to create a model feature is target leakage.
- Why precision, recall, F1-score, and ROC-AUC answer different questions.
- How class weighting changes training but does not solve every imbalance problem.
- The difference between training, validation, and final holdout data.
- How Flask blueprints and the application factory organize the API.
- Why SQL parameters protect values but not table or column identifiers.
- Why an LLM must not be allowed to execute arbitrary SQL or Python.
- Why a read-only database user is different from an application owner account.
- Why synthetic-data performance does not prove real-world model performance.

### 5. Questions likely to be asked

- Why did you choose a normalized schema?
- What is the grain of `orders` and `order_items`?
- How do you avoid double-counting revenue?
- How was churn generated, and what makes the data realistic?
- Why was Logistic Regression selected over Random Forest?
- How did you detect target leakage?
- What does a recall of 0.70 mean for churn detection?
- What happens if the saved model artifact is missing?
- How does the assistant know whether it can answer a question?
- What happens when an LLM response is malformed?
- How would you deploy the Flask API securely?
- Why is the Power BI model a star schema?
- What would you change for millions of orders?

### 6. Questions that could expose AI-generated work

- Explain one function you personally debugged and what the original failure was.
- Why does `orders` contain `total_amount` while `order_items` contains `line_total`?
- Why was `customer_segment` removed or changed in the churn pipeline?
- Why can’t the assistant safely trust a provider-generated recommendation?
- Why is the current MySQL integration not live-verified?
- What exact command runs the tests, and what do the tests cover?
- Show how you would add a new approved assistant intent.
- What would happen if a user sent `SELECT ... INTO OUTFILE`?
- What does `class_weight="balanced"` do?
- Which technologies in `requirements.txt` are not actually used?

If you cannot answer these from understanding, do not claim that you built every part independently. Explain that you studied, adapted, tested, and improved the implementation.

### 7. Project limitations

- No production authentication or authorization.
- No live MySQL verification in the current environment.
- No real customer data or production labels.
- No time-based churn observation window.
- No model calibration, drift monitoring, experiment tracking, or retraining workflow.
- Pickle model artifacts must be treated as trusted files.
- No browser-based visual regression tests.
- External LLM output is deliberately non-authoritative; the current assistant is grounded by predefined analytics tools.
- Power BI documentation exists, but a connected report has not been validated.

### 8. Improvements for realism

1. Add an observation date and churn outcome window so features are calculated before the target period.
2. Validate the pipeline against a real MySQL instance with a dedicated read-only account.
3. Add authentication, authorization, rate limiting, request-size limits, and HTTPS deployment.
4. Add model calibration, cross-validation, threshold selection, drift checks, and experiment tracking.
5. Store model predictions in a governed table with model version and prediction timestamp.
6. Use a production charting library and Playwright tests for the dashboard.
7. Add database migrations, connection pooling, structured logs, and deployment configuration.
8. Add an LLM grounded-generation layer only after establishing a factual verifier and audit logs.
9. Create a real Power BI report connected to MySQL and validate refresh behavior.
10. Add data-quality checks for revenue reconciliation between order totals and line totals.

### 9. Explain these without looking at code

- The complete data flow from generated CSV to API response.
- The four database tables and their relationships.
- The difference between an order and an order item.
- How a customer becomes a churn feature row.
- Why the model has categorical preprocessing and numeric preprocessing.
- How the model is selected and evaluated.
- Why the assistant uses tools instead of arbitrary generated SQL.
- How the Flask API handles validation and errors.
- How the frontend obtains live data.
- How Power BI should connect to the database.
- What is implemented versus merely documented.

## Technologies Actually Used

| Technology | Actual status |
| --- | --- |
| Python 3.13 | Used throughout data generation, analytics, ML, database utilities, and API services |
| Pandas | Used for loading, joins, aggregation, feature engineering, and analytics |
| NumPy | Used in synthetic data generation and ML preprocessing decisions |
| scikit-learn | Used for churn pipelines, preprocessing, evaluation, and prediction |
| Flask | Used for the REST API and static frontend serving |
| PyMySQL | Used for MySQL connection and query utilities; live server validation is incomplete |
| python-dotenv | Used to load `.env` configuration |
| pytest | Used for automated tests |
| HTML/CSS/JavaScript | Used for the dashboard frontend |
| MySQL | Schema, seed script, and query design exist; live authentication/refresh is not validated |
| Power BI | Connection, model, DAX, and page documentation exists; no PBIX report is included |
| LLM provider | Abstract compatible adapter exists; no external provider is required or used by default |
| SQLAlchemy | Listed in `requirements.txt`, but not used by the current application code |
| mysql-connector-python | Listed, but the application database utility uses PyMySQL instead |
| OpenAI/LangChain | Not installed or used |
| React | Not used |

## Interview Question Bank

Each answer below has four parts: a beginner-friendly answer, a deeper explanation, the relevant project component, and a likely follow-up.

## Basic Questions

### What is the project?

**Interviewer question:** What did you build?

**Beginner-friendly answer:** I built an AI-powered business intelligence prototype for an e-commerce business. It generates linked business data, calculates sales and customer KPIs, predicts churn, exposes REST APIs, displays a dashboard, and answers approved business questions using verified analytics.

**Deeper technical explanation:** The system is layered: synthetic source data feeds Pandas analytics and a normalized MySQL design; feature engineering feeds two scikit-learn classifiers; Flask exposes analytics and prediction contracts; the frontend consumes those contracts; the assistant routes natural-language questions to predefined tools.

**Relevant project component:** `src/data_generator.py`, `src/analytics.py`, `src/ml_model.py`, `api/`, `frontend/`, `src/ai_assistant.py`.

**Possible follow-up:** Which layer would you replace first for production? Answer: the CSV-backed analytics path would be replaced or supplemented with a validated database-backed repository.

### Why did you build it?

**Beginner-friendly answer:** I wanted one project that demonstrated data engineering, analytics, machine learning, backend development, and business communication instead of showing isolated scripts.

**Deeper technical explanation:** The business use case connects descriptive analytics with a predictive retention workflow. The design also demonstrates how a dashboard and assistant should consume structured, auditable results rather than directly inventing answers.

**Relevant project component:** `PROJECT_SPEC.md`, `README.md`, `powerbi/README.md`.

**Possible follow-up:** What did you learn that a notebook alone would not teach you? Answer: API contracts, validation, module boundaries, security, deployment constraints, and testing.

### What problem does it solve?

**Beginner-friendly answer:** It helps a business monitor revenue and customers, identify churn patterns, and receive decision-support outputs from one system.

**Deeper technical explanation:** It provides KPIs by time, category, product, city, and customer; a churn classification workflow; and a constrained question interface that returns the source records used for the answer.

**Relevant project component:** `src/analytics.py`, `api/routes/analytics.py`, `src/ai_assistant.py`.

**Possible follow-up:** Does it make autonomous business decisions? Answer: no. It provides analysis and risk signals; a human must decide what action to take.

### What is your contribution?

**Beginner-friendly answer:** My contribution is the design and integration of the data generator, analytics modules, ML pipeline, API, frontend, assistant boundary, security checks, tests, and Power BI model documentation.

**Deeper technical explanation:** I can explain the decisions and tradeoffs in each layer, including the target-leakage correction, holdout evaluation, SQL safety boundaries, and why the assistant preserves deterministic verified responses.

**Relevant project component:** The repository as a whole.

**Possible follow-up:** Which part required the most debugging? Answer: the model input contract and the boundary between natural-language requests, approved analytics, and untrusted provider output.

## Python Questions

### Why did you split the code into modules?

**Beginner-friendly answer:** Each module has one main responsibility, which makes the code easier to test and change.

**Deeper technical explanation:** Data generation, analytics, feature engineering, model lifecycle, database access, API routing, and assistant orchestration have separate ownership boundaries. This avoids putting business logic in Flask route functions.

**Relevant project component:** `src/`, `api/services/`, and `api/routes/`.

**Possible follow-up:** What is one module you would split further? Answer: production database repositories and configuration could become separate modules.

### How do you use Pandas?

**Beginner-friendly answer:** I use it to load CSV tables, join related data, group by business dimensions, calculate totals, and prepare customer-level ML features.

**Deeper technical explanation:** Examples include merging order items with products for category/product performance, merging orders with customers for city performance, and aggregating orders by customer for total orders and spend.

**Relevant project component:** `src/analytics.py`, `src/feature_engineering.py`.

**Possible follow-up:** What is the risk of an incorrect merge? Answer: duplicate rows can inflate revenue, so table grain and key uniqueness must be checked.

### How do you make generated data reproducible?

**Beginner-friendly answer:** The generator uses NumPy random generators with a configurable seed.

**Deeper technical explanation:** The same seed produces the same customer, product, order, and item relationships, which makes tests and model experiments repeatable. A changed seed creates a different valid dataset.

**Relevant project component:** `src/data_generator.py`.

**Possible follow-up:** Is reproducibility the same as realism? Answer: no. It makes experiments repeatable, but synthetic distributions still need domain validation.

## SQL Questions

### How do you prevent SQL injection?

**Beginner-friendly answer:** Values should use parameterized queries, and table/column identifiers must be allow-listed because parameters do not protect identifiers.

**Deeper technical explanation:** The database utility validates read-only analytics SQL and restricts CSV-import identifiers to known tables and columns. The assistant uses predefined tools instead of executing arbitrary LLM-generated SQL.

**Relevant project component:** `src/database.py`, `src/ai_assistant.py`.

**Possible follow-up:** Why cannot you write `SELECT * FROM %s` with a parameter? Answer: database drivers bind values, not SQL identifiers; an identifier needs allow-listing or safe quoting.

### What does read-only SQL mean?

**Beginner-friendly answer:** Only analytical `SELECT` statements are permitted; data-changing or schema-changing commands are rejected.

**Deeper technical explanation:** The validator rejects write operations, stacked statements, comments, and file-writing forms such as `INTO OUTFILE`. Production database permissions must enforce the same policy with a read-only account.

**Relevant project component:** `src/database.py`, `database/schema.sql`, `powerbi/README.md`.

**Possible follow-up:** Is an application validator enough? Answer: no. It is defense in depth; database permissions are the real enforcement layer.

### How do you avoid double-counting orders?

**Beginner-friendly answer:** `orders` is one row per order, while `order_items` can contain many rows per order. I use `DISTINCTCOUNT(order_id)` for order counts and line totals for item-level revenue.

**Deeper technical explanation:** Joining the two facts can multiply order-level columns, so order-level measures must use distinct order IDs or remain on the order table. Product/category revenue naturally belongs to order-item grain.

**Relevant project component:** `database/schema.sql`, `src/analytics.py`, `powerbi/README.md`.

**Possible follow-up:** Why can order totals and line totals disagree? Answer: discounts, taxes, shipping, rounding, or bad data; the project should add a reconciliation check.

## Database Questions

### Why are there four tables?

**Beginner-friendly answer:** Customers, products, orders, and order items represent different entities and grains, so separating them avoids duplication and preserves relationships.

**Deeper technical explanation:** Customers and products are dimensions. Orders are order-grain facts, and order items are line-grain facts. Foreign keys preserve valid customer, product, and order references.

**Relevant project component:** `database/schema.sql`.

**Possible follow-up:** Why not store product name directly in orders? Answer: an order can contain multiple products; product details belong in products and order items reference them.

### What indexes did you choose?

**Beginner-friendly answer:** Indexes exist on customer city/churn, order customer/date/amount, product category, and order-item order/product keys.

**Deeper technical explanation:** They support common joins, date filtering, city/churn filtering, and product/category aggregation. Indexes improve reads but add storage and write cost.

**Relevant project component:** `database/schema.sql`.

**Possible follow-up:** Which index would you validate with `EXPLAIN` first? Answer: `orders(order_date)` for time-series filtering and the foreign-key join indexes for reporting joins.

### What remains incomplete in the database layer?

**Beginner-friendly answer:** The schema and seed scripts exist, but local MySQL authentication blocked a complete live import and query validation.

**Deeper technical explanation:** The application can use PyMySQL and has safer import/query utilities, but operational verification still requires a running server, correct credentials, a read-only account, and a successful refresh test.

**Relevant project component:** `src/database.py`, `database/seed.sql`.

**Possible follow-up:** How would you finish it? Answer: create the database, run schema and seed scripts, validate row counts and foreign keys, run representative `EXPLAIN` plans, and execute integration tests against a disposable database.

## Machine Learning Questions

### What is the churn target?

**Beginner-friendly answer:** `churn` is a binary customer outcome: 1 means churned and 0 means not churned.

**Deeper technical explanation:** The customer table supplies the target. The model uses customer demographics, behavior, spend, order aggregates, payment method, and a target-independent business segment.

**Relevant project component:** `src/feature_engineering.py`, `src/ml_model.py`.

**Possible follow-up:** How did you prevent leakage? Answer: the model segment no longer uses `churn`; I added a test that flips the target and expects the segment feature to remain unchanged.

### Why Logistic Regression and Random Forest?

**Beginner-friendly answer:** Logistic Regression is interpretable and provides a strong baseline; Random Forest can capture nonlinear relationships and interactions.

**Deeper technical explanation:** Both are wrapped in preprocessing pipelines. Logistic Regression uses imputation, scaling, one-hot encoding, and class weighting. Random Forest uses imputation, one-hot encoding, and balanced subsampling.

**Relevant project component:** `src/ml_model.py`.

**Possible follow-up:** Why was Logistic Regression selected? Answer: selection uses validation F1, while final metrics are reported on an untouched holdout.

### Why not use accuracy alone?

**Beginner-friendly answer:** If churn is less common, a model can achieve good accuracy by mostly predicting no churn while missing the customers we care about.

**Deeper technical explanation:** Recall measures captured churners, precision measures how many flagged customers truly churn, F1 balances both, and ROC-AUC measures ranking quality across thresholds. The business cost of false negatives and false positives should determine the operating threshold.

**Relevant project component:** `_evaluate_model` in `src/ml_model.py`.

**Possible follow-up:** Which metric matters most here? Answer: likely recall or a cost-weighted metric, but the company must define the cost of each error.

### What are the model limitations?

**Beginner-friendly answer:** The data is synthetic, churn timing is not explicitly modeled, and there is no production monitoring or calibration.

**Deeper technical explanation:** Features may include information from the same broad period as the label, so a real project needs a point-in-time feature window and future outcome window. Performance should be validated on time-based and external data.

**Relevant project component:** `src/data_generator.py`, `src/feature_engineering.py`, `src/ml_model.py`.

**Possible follow-up:** What would you add first? Answer: observation and prediction timestamps, time-based splitting, calibration, and monitoring.

## NLP/LLM Questions

### Is this a real LLM application?

**Beginner-friendly answer:** It has an abstract compatible provider adapter, but the default assistant is a deterministic analytics tool router. It does not require an external LLM and does not trust provider text as business truth.

**Deeper technical explanation:** A question is mapped to approved analytics functions, data is retrieved first, and the response includes the verified records. An optional provider can be called, but its output cannot replace the grounded answer.

**Relevant project component:** `src/ai_assistant.py`, `api/routes/ai.py`.

**Possible follow-up:** Why not let the LLM generate SQL directly? Answer: generated SQL can access unauthorized data, mutate data, leak information, or produce incorrect analysis; an allow-listed tool layer is safer for this scope.

### How does the assistant avoid hallucination?

**Beginner-friendly answer:** It answers only supported question patterns using existing analytics functions and explicitly says information is unavailable for unsupported questions.

**Deeper technical explanation:** The response data comes from the analytics layer, not from model-generated claims. SQL validation and a read-only account are additional safeguards for future SQL-backed tools.

**Relevant project component:** `BusinessAssistant._run_approved_tool`, `src/database.py`.

**Possible follow-up:** Is it mathematically impossible for the system to hallucinate? Answer: no system can guarantee that without formal verification, but this design minimizes the risk by making the deterministic data path authoritative.

### How would you productionize the LLM layer?

**Beginner-friendly answer:** I would add a provider client with timeouts, tracing, cost limits, prompt-injection tests, structured-output validation, audit logs, and a factual verifier.

**Deeper technical explanation:** The provider should receive only the minimum structured result needed, use a read-only identity for tools, enforce schema validation, redact sensitive data, and fail closed when the answer cannot be grounded.

**Relevant project component:** `CompatibleLLMProvider` in `src/ai_assistant.py`.

**Possible follow-up:** What must never reach the frontend? Answer: API keys, database credentials, internal prompts, and unrestricted raw database access.

## API/Flask Questions

### Why use an application factory?

**Beginner-friendly answer:** `create_app` makes it easier to create configured application instances for production and tests.

**Deeper technical explanation:** Blueprints register route groups, error handlers are centralized, and tests can enable `TESTING` without starting a server.

**Relevant project component:** `api/app.py`.

**Possible follow-up:** How would you add authentication? Answer: add middleware or decorators around protected blueprints, validate tokens, and keep authorization separate from route logic.

### How are API errors handled?

**Beginner-friendly answer:** Validation errors return structured JSON with status 400, unsupported routes return 404 JSON, and unexpected exceptions are logged and return a generic 500 response.

**Deeper technical explanation:** Routes remain thin; services raise validation errors and the application-level handlers normalize the contract. Sensitive exception details are logged server-side, not returned to clients.

**Relevant project component:** `api/app.py`, `api/routes/`.

**Possible follow-up:** What is missing for production? Answer: authentication, rate limiting, request size limits, correlation IDs, structured logging, and a production WSGI server.

### How does the prediction endpoint validate data?

**Beginner-friendly answer:** It checks JSON shape, required model features, numeric types, finite values, ranges, and allowed categories.

**Deeper technical explanation:** Validation uses the loaded model feature schema so the route does not duplicate model columns. The frontend provides usability validation, but server-side validation is the security boundary.

**Relevant project component:** `api/services/prediction_service.py`.

**Possible follow-up:** Why accept unknown cities but restrict gender? Answer: the model can safely one-hot encode unknown cities, while enums should follow the business contract; production could validate cities against a dimension table.

## Power BI Questions

### Why use a star schema?

**Beginner-friendly answer:** It separates descriptive dimensions from measurable fact tables and makes filtering and DAX easier to reason about.

**Deeper technical explanation:** Customers, products, and date filter the facts through one-directional relationships. Orders and order items remain at their native grains, preventing accidental many-to-many ambiguity.

**Relevant project component:** `powerbi/README.md`, `database/schema.sql`.

**Possible follow-up:** Why add a date table? Answer: it enables reliable month sorting, time intelligence, prior-period comparisons, and year-to-date measures.

### What is the difference between a measure and a calculated column?

**Beginner-friendly answer:** A measure is calculated at query time under the current filter context; a calculated column is computed for each row during refresh.

**Deeper technical explanation:** Revenue and churn rate should be measures because they respond to slicers. Customer segment can be a calculated column because it is a row-level classification refreshed with the model.

**Relevant project component:** `powerbi/README.md`.

**Possible follow-up:** Why not store ML risk in a calculated column? Answer: Power BI does not run the scikit-learn model; predictions need a governed output table or API/dataflow.

## Security Questions

### What are the main security risks?

**Beginner-friendly answer:** Database credentials, unrestricted SQL, untrusted model artifacts, unauthenticated endpoints, and provider prompt injection are the main risks.

**Deeper technical explanation:** The project mitigates SQL identifiers with allow-lists, restricts read-only SQL, keeps secrets in environment variables, and prevents provider output from replacing grounded responses. It still lacks production authentication and trusted-artifact signing.

**Relevant project component:** `src/database.py`, `src/ai_assistant.py`, `.env.example`, `api/app.py`.

**Possible follow-up:** Why is `pickle` risky? Answer: loading a malicious pickle can execute code, so artifacts must come from a trusted build path with integrity controls.

### What is the difference between authentication and authorization?

**Beginner-friendly answer:** Authentication verifies who a caller is; authorization decides what that caller may do.

**Deeper technical explanation:** This project currently has neither at the API boundary. A production system would authenticate users, authorize report and prediction access, and use a separate read-only identity for analytics.

**Relevant project component:** `api/app.py` and database configuration.

**Possible follow-up:** Should the frontend receive database credentials? Answer: never. It should call the backend, which owns credentials and access policy.

## System Architecture Questions

### Describe the architecture end to end.

**Beginner-friendly answer:** Data is generated into related CSVs, analytics loads and transforms it, ML builds churn features and predictions, Flask exposes results, JavaScript renders the dashboard, and the assistant routes questions to approved analytics tools.

**Deeper technical explanation:** The system has source/data, analytics, feature/ML, service/API, presentation, and BI documentation layers. The boundaries allow the frontend to change without rewriting analytics and allow a future database repository to replace CSV loading.

**Relevant project component:** `src/`, `api/`, `frontend/`, `database/`, `powerbi/`.

**Possible follow-up:** What is the current bottleneck? Answer: repeated CSV loading and the lack of a validated production database path.

### How would you scale it?

**Beginner-friendly answer:** Move analytics to indexed database queries, add connection pooling and caching, separate background model training from API serving, and deploy the API behind a production server.

**Deeper technical explanation:** I would introduce repository interfaces, incremental data loads, materialized aggregates, asynchronous prediction jobs when needed, observability, and a model registry. The frontend would consume paginated endpoints instead of loading every table.

**Relevant project component:** `src/database.py`, `api/services/`, `frontend/app.js`.

**Possible follow-up:** What would you measure? Answer: API latency, error rate, query duration, refresh failures, model precision/recall drift, and assistant unsupported-question rate.

## Project-Specific Questions

### Why is `segment` allowed in the churn model?

**Beginner-friendly answer:** It is a business segment derived from spend and support behavior, not from the churn target anymore.

**Deeper technical explanation:** Earlier logic used `churn` to assign `At Risk`, which leaked the label. The current feature-engineering path disables that target signal and tests that flipping churn does not change the segment feature.

**Relevant project component:** `src/analytics.py`, `src/feature_engineering.py`, `tests/test_ml_pipeline.py`.

**Possible follow-up:** Would you keep this feature in production? Answer: only if its inputs are available before the prediction point and the segment logic is versioned.

### Why does the assistant return records as well as an answer?

**Beginner-friendly answer:** The records let the user inspect the evidence behind the answer.

**Deeper technical explanation:** Returning structured evidence improves auditability and makes it possible for the frontend or Power BI-like consumer to render tables without trusting prose alone.

**Relevant project component:** `src/ai_assistant.py`, `api/routes/ai.py`, `frontend/app.js`.

**Possible follow-up:** What if the records are empty? Answer: return an explicit unavailable response rather than fabricate a conclusion.

### What would you demonstrate first in an interview?

**Beginner-friendly answer:** I would run the tests, show the dashboard, call `/api/summary` and `/api/predict-churn`, then demonstrate a supported and unsupported `/api/ask` question.

**Deeper technical explanation:** That sequence proves the system is executable, shows the data contract, demonstrates model inference, and makes the grounding behavior visible. I would also explain the MySQL limitation before claiming production readiness.

**Relevant project component:** `tests/`, `api/`, `frontend/`, `README.md`.

**Possible follow-up:** What would you avoid claiming? Answer: I would not claim live MySQL, Power BI refresh, real LLM reasoning, or production-grade security without evidence.
