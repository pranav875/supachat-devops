# SupaChat

A conversational analytics platform that lets you query a blog analytics database using plain English. Type a question, get back a text summary, a sortable data table, and an interactive chart — all powered by an LLM-to-SQL pipeline backed by Supabase PostgreSQL.

---

## Architecture

```mermaid
graph TD
    User["Browser (Next.js)"]
    Nginx["Nginx :80"]
    Frontend["Frontend\nNext.js :3000"]
    Backend["Backend\nFastAPI :8000"]
    MCP["MCP Server\n(in-process)"]
    Supabase["Supabase PostgreSQL\n(external)"]
    LLM["LLM API\nOpenAI / Anthropic"]
    Prometheus["Prometheus :9090"]
    Grafana["Grafana :3001"]
    Loki["Loki :3100"]
    Promtail["Promtail"]
    DevOpsAgent["DevOps Agent\n:8001"]

    User --> Nginx
    Nginx -->|"/"| Frontend
    Nginx -->|"/api"| Backend
    Backend --> MCP
    MCP --> Supabase
    Backend --> LLM
    Promtail --> Loki
    Prometheus --> Grafana
    Loki --> Grafana
    DevOpsAgent --> Backend
    DevOpsAgent --> LLM
```

**Request flow:** Browser → Nginx → Next.js frontend (UI) or FastAPI backend (API). The backend builds an LLM prompt with the DB schema, gets back SQL, executes it via the in-process MCP server against Supabase, formats the results, and returns a structured JSON response with a text summary, tabular data, and Recharts-ready chart data.

All services run as Docker containers orchestrated by `docker-compose`. Promtail ships container logs to Loki; Prometheus scrapes `/metrics` from the backend; Grafana visualizes both.

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) 24+
- [Docker Compose](https://docs.docker.com/compose/install/) v2+
- A [Supabase](https://supabase.com) project with the blog analytics schema applied (see `backend/db/migrations/001_schema.sql`)
- An OpenAI **or** Anthropic API key

---

## Local Setup

### 1. Clone and configure

```bash
git clone https://github.com/your-org/supachat.git
cd supachat
cp .env.example .env
```

Edit `.env` and fill in your values (see [Environment Variables](#environment-variables) below).

### 2. Apply the database schema

Run the migration against your Supabase project:

```bash
psql "$DATABASE_URL" -f backend/db/migrations/001_schema.sql
```

Optionally seed with ~90 days of sample data:

```bash
cd backend
pip install asyncpg python-dotenv
python db/seed.py
```

### 3. Start all services

```bash
docker-compose up -d
```

| Service | URL |
|---------|-----|
| App (via Nginx) | http://localhost |
| Backend API | http://localhost/api |
| Grafana | http://localhost:3001 |
| Prometheus | http://localhost:9090 |
| DevOps Agent | http://localhost:8001 |

### 4. Verify everything is healthy

```bash
docker-compose ps
```

All services should show `healthy`. The backend health endpoint:

```bash
curl http://localhost/api/health
# {"status": "ok"}
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values below.

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Postgres connection string, e.g. `postgresql://user:pass@host:5432/db` |
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | Supabase service role key (bypasses RLS) |
| `OPENAI_API_KEY` | One of these | OpenAI API key for LLM SQL generation |
| `ANTHROPIC_API_KEY` | One of these | Anthropic API key (used if `OPENAI_API_KEY` is not set) |
| `HISTORY_LIMIT` | No | Max history records returned (default: `50`) |
| `HISTORY_DB_PATH` | No | SQLite path inside the backend container (default: `/app/data/supachat_history.db`) |
| `NEXT_PUBLIC_API_URL` | No | API base URL seen by the browser (default: `http://localhost/api`) |

---

## EC2 Deployment

### One-time bootstrap

Provision an Ubuntu EC2 instance (t3.medium or larger recommended), then run the bootstrap script as root:

```bash
# On your local machine — copy the script and your .env to the instance
scp scripts/bootstrap-ec2.sh ec2-user@<EC2-IP>:~
scp .env ec2-user@<EC2-IP>:~

# SSH in and run
ssh ec2-user@<EC2-IP>
sudo ENV_SOURCE=~/.env REPO_URL=https://github.com/your-org/supachat.git bash bootstrap-ec2.sh
```

The script is idempotent — safe to re-run. It will:
1. Install Docker and Docker Compose if not already present
2. Clone (or pull) the repository to `/opt/supachat`
3. Copy your `.env` file
4. Run `docker-compose pull && docker-compose up -d`

### Security group

Open these inbound ports on your EC2 security group:

| Port | Protocol | Purpose |
|------|----------|---------|
| 80 | TCP | HTTP (Nginx) |
| 22 | TCP | SSH (restrict to your IP) |
| 3001 | TCP | Grafana (restrict to your IP) |
| 9090 | TCP | Prometheus (restrict to your IP) |

---

## CI/CD Pipeline

The GitHub Actions workflow at `.github/workflows/deploy.yml` runs on every push to `main`.

```
push to main
    │
    ├─ job: test
    │   ├─ Spin up Postgres service container
    │   ├─ Run pytest (backend)
    │   └─ Run jest --ci (frontend)
    │
    ├─ job: build-push  (needs: test)
    │   ├─ Build supachat-frontend image → GHCR with SHA tag + latest
    │   └─ Build supachat-backend image  → GHCR with SHA tag + latest
    │
    └─ job: deploy  (needs: build-push)
        ├─ SSH to EC2
        ├─ docker-compose pull
        ├─ docker-compose up -d --no-deps
        └─ docker-compose ps (verify healthy)
```

If any job fails, the pipeline stops and the broken code is never deployed.

### Required GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|--------|-------------|
| `EC2_SSH_KEY` | Private SSH key for the EC2 instance |
| `EC2_HOST` | Public IP or hostname of the EC2 instance |
| `GHCR_TOKEN` | GitHub personal access token with `write:packages` scope |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service role key |
| `OPENAI_API_KEY` | OpenAI API key |

---

## Monitoring & Grafana Dashboards

The monitoring stack (Prometheus, Grafana, Loki, Promtail) starts automatically with `docker-compose up`.

Grafana is available at **http://localhost:3001** (default credentials: `admin` / `admin`).

Two dashboards are pre-provisioned:

**SupaChat App** (`monitoring/grafana/dashboards/supachat.json`)
- HTTP request rate
- p95 request latency
- Error rate (4xx/5xx)
- Error-level logs from Loki

**Infrastructure** (`monitoring/grafana/dashboards/infrastructure.json`)
- CPU usage per container
- Memory usage per container
- Container uptime

Logs from all containers are collected by Promtail and queryable in Grafana Explore using LogQL, e.g.:

```logql
{container="supachat-backend-1"} |= "ERROR"
```

---

## DevOps Agent (Bonus)

A FastAPI sidecar on port 8001 provides AI-powered operational automation:

| Endpoint | Description |
|----------|-------------|
| `POST /agent/deploy` | Trigger `docker-compose pull && up -d` |
| `POST /agent/restart` | Restart a named container |
| `GET /agent/logs` | Fetch recent logs + LLM-generated summary |
| `POST /agent/diagnose` | Submit CI failure logs, get root cause analysis |
| `GET /agent/health` | Consolidated health check across all services |
| `POST /agent/alert` | Grafana webhook receiver → diagnostic summary |

Example — get an AI summary of recent backend errors:

```bash
curl http://localhost:8001/agent/logs?service=backend&lines=100
```

---

## Running Tests

**Backend:**

```bash
cd backend
pip install -r requirements.txt
pytest --tb=short
```

**Frontend:**

```bash
cd frontend
npm ci
npm test -- --watchAll=false
```

---

## AI Tools Used

- **OpenAI GPT-4o / GPT-4** — natural language to SQL translation, query result summarization
- **Anthropic Claude** — alternative LLM provider for SQL generation and summarization (selected when `ANTHROPIC_API_KEY` is set and `OPENAI_API_KEY` is not)
- **Kiro** — AI-assisted IDE used throughout development for code generation, spec creation, and implementation planning
