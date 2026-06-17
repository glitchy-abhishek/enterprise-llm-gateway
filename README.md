# Enterprise LLM Gateway

A highly scalable, asynchronous AI API Gateway engineered to centralize traffic, enforce granular rate limits, manage access control policies, and expose live telemetry across multiple upstream AI providers.

## 🚀 Key Features
* **Multi-Provider Dynamic Routing:** Routes requests seamlessly across OpenAI and Anthropic infrastructure based on payload intents.
* **Granular GitOps Access Policies:** Configuration-driven authorization layer mapping team permissions and authorized models via YAML.
* **Distributed Rate Limiting:** High-throughput token-bucket limiting layer utilizing Redis async connection pools.
* **Production Observability:** Integrated Prometheus counters tracking real-time status code distributions and provider latency.
* **Container-Native Infrastructure:** Hardened, lightweight Docker orchestration footprint.

## 🛠️ Tech Stack
* **Framework:** FastAPI, Uvicorn, Python 3.11+
* **Storage & Caching:** Redis (Asyncio)
* **Observability:** Prometheus Client
* **Infrastructure:** Docker
