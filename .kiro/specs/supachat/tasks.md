# Implementation Plan

- [x] 1. Project scaffolding and shared configuration
  - Create the monorepo directory structure: `frontend/`, `backend/`, `devops-agent/`, `nginx/`, `monitoring/`, `.github/workflows/`
  - Create `.env.example` with all required environment variable keys (no values)
  - Create root `docker-compose.yml` skeleton with service stubs for frontend, backend, nginx, prometheus, grafana, loki, promtail
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 2. Supabase schema and seed data
- [x] 2.1 Write SQL migration files for the blog analytics schema
  - Create `backend/db/migrations/001_schema.sql` with `articles`, `article_views`, `article_engagement` tables
  - _Requirements: 1.1_

- [x] 2.2 Write seed data script
  - Create `backend/db/seed.py` that inserts ~50 articles across 8 topics and 90 days of view/engagement records using `asyncpg`
  - Script must read `DATABASE_URL` from environment
  - _Requirements: 1.2, 1.3_

- [x] 3. Backend core setup (FastAPI)
- [x] 3.1 Initialize FastAPI app with health and metrics endpoints
  - Create `backend/app/main.py` with FastAPI app instance
  - Add `GET /health` returning `{"status": "ok"}`
  - Add `prometheus-fastapi-instrumentator` and expose `GET /metrics`
  - Create `backend/requirements.txt` with all dependencies
  - _Requirements: 4.3, 4.6_

- [x] 3.2 Implement Pydantic schemas
  - Create `backend/app/schemas.py` with `QueryRequest`, `QueryResponse`, `HistoryRecord` models
  - _Requirements: 4.1, 4.2_

- [x] 3.3 Implement asyncpg database connection module
  - Create `backend/app/db.py` with connection pool initialization and a `execute_read_query(sql)` helper
  - Wrap all queries in read-only transactions
  - Handle connection errors and raise appropriate HTTP exceptions
  - _Requirements: 2.2, 2.4, 4.5_

- [x] 4. MCP Server implementation
- [x] 4.1 Implement MCP tool definitions
  - Create `backend/app/mcp_server.py` using the `mcp` Python SDK
  - Register `execute_query(sql)`, `get_schema()`, and `get_topics()` tools
  - Wire `execute_query` to `db.execute_read_query`
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 4.2 Write unit tests for MCP tools
  - Create `backend/tests/test_mcp.py` using `pytest` with a mock DB connection
  - Test successful query execution, empty results, and DB error handling
  - _Requirements: 2.2, 2.3, 2.4_

- [x] 5. LLM integration and SQL generation
- [x] 5.1 Implement LLM prompt builder and SQL extractor
  - Create `backend/app/llm.py` with `generate_sql(nl_query: str) -> str`
  - Build system prompt including schema context (from `get_schema()`), today's date, and few-shot examples
  - Parse LLM response to extract SQL block; raise `ValueError` if no valid SQL found
  - Support both `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` via env-based provider selection
  - _Requirements: 3.1, 3.4, 3.5_

- [x] 5.2 Implement retry logic for invalid SQL
  - In `llm.py`, if the first SQL attempt fails validation, retry once with the error appended to the prompt
  - After two failures, raise an exception that maps to HTTP 422
  - _Requirements: 3.3_

- [x] 5.3 Write unit tests for LLM module
  - Create `backend/tests/test_llm.py` mocking the LLM API
  - Test SQL extraction, relative date resolution, retry on invalid SQL, and failure after two attempts
  - _Requirements: 3.1, 3.3, 3.4_

- [x] 6. Response formatter and chart type detection
- [x] 6.1 Implement result formatter
  - Create `backend/app/formatter.py` with `format_results(columns, rows) -> dict`
  - Implement chart type detection logic: date+numeric → `line`, category+numeric → `bar`, label+share → `pie`, else `none`
  - Shape `chart_data` into Recharts-compatible format for each chart type
  - _Requirements: 3.2, 6.1, 6.2, 6.3_

- [x] 6.2 Write unit tests for formatter
  - Create `backend/tests/test_formatter.py`
  - Test each chart type detection branch and the Recharts data shape for line, bar, pie, and none
  - Test empty rows returning `chart_type: "none"`
  - _Requirements: 6.1, 6.2, 6.3, 6.5_

- [x] 7. Query history store
  - Create `backend/app/history.py` using `aiosqlite` for a local SQLite store
  - Implement `save_query(record: HistoryRecord)` and `get_history(limit: int) -> list[HistoryRecord]`
  - Initialize the SQLite DB table on app startup
  - _Requirements: 4.4_

- [x] 8. Wire up POST /api/query endpoint
  - In `backend/app/main.py`, implement `POST /api/query` using the full pipeline: validate → `generate_sql` → `execute_query` via MCP → `format_results` → LLM summary → `save_query` → return `QueryResponse`
  - Implement `GET /api/history` endpoint calling `get_history()`
  - Add structured error handling mapping exceptions to correct HTTP status codes (422, 503, 504)
  - _Requirements: 4.1, 4.2, 4.4, 4.5, 3.2, 3.3_

- [x] 9. Backend integration tests
  - Create `backend/tests/test_api.py` using `httpx.AsyncClient` with a test Postgres instance
  - Test `POST /api/query` end-to-end with a real SQL-generating mock LLM and real DB
  - Test `GET /health`, `GET /api/history`, and error scenarios (bad SQL, DB down)
  - _Requirements: 4.1, 4.2, 4.3, 4.5_

- [x] 10. Backend Dockerfile
  - Create `backend/Dockerfile` using a slim Python base image
  - Multi-stage build: install deps in builder stage, copy to runtime stage
  - Set `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`
  - _Requirements: 7.1, 7.3_

- [x] 11. Frontend scaffolding (Next.js)
- [x] 11.1 Initialize Next.js project with TypeScript and Tailwind CSS
  - Set up `frontend/` with `next.config.js`, `tsconfig.json`, and Tailwind config
  - Install dependencies: `recharts`, `@tanstack/react-table`, `axios`
  - Create `frontend/src/lib/api.ts` with typed wrappers for `POST /api/query` and `GET /api/history`
  - _Requirements: 5.1_

- [x] 11.2 Implement ChatInput component
  - Create `frontend/src/components/ChatInput.tsx`
  - Text input + submit button; calls `onSubmit(query: string)` prop
  - Disabled while loading; shows loading spinner on submit
  - _Requirements: 5.1, 5.2_

- [x] 11.3 Implement DataTable component
  - Create `frontend/src/components/DataTable.tsx` using TanStack Table
  - Accepts `columns: string[]` and `rows: any[][]` props
  - Supports column header click to sort
  - _Requirements: 5.4_

- [x] 11.4 Implement ChartPanel component
  - Create `frontend/src/components/ChartPanel.tsx`
  - Renders `LineChart`, `BarChart`, or `PieChart` from Recharts based on `chartType` prop
  - Includes legend, tooltips, and labeled axes for line/bar; legend and tooltips for pie
  - Renders "No data to visualize" when `chartType === "none"` or data is empty
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 11.5 Implement ChatBubble component
  - Create `frontend/src/components/ChatBubble.tsx`
  - Renders text summary as a styled bubble
  - Conditionally renders `DataTable` and `ChartPanel` below the bubble when data is present
  - Renders an error variant when `isError` prop is true
  - _Requirements: 5.3, 5.4, 5.5, 5.6_

- [x] 11.6 Implement HistorySidebar component
  - Create `frontend/src/components/HistorySidebar.tsx`
  - Fetches history from `GET /api/history` on mount
  - Lists queries; clicking one calls `onSelect(record)` prop to re-display results
  - _Requirements: 5.7, 5.8_

- [x] 11.7 Implement ChatWindow and wire main page
  - Create `frontend/src/components/ChatWindow.tsx` composing `ChatBubble` list with auto-scroll
  - Update `frontend/src/app/page.tsx` to compose `ChatInput`, `ChatWindow`, and `HistorySidebar`
  - Manage chat state (messages array, loading, error) with `useReducer`
  - On submit: add user bubble, call API, add assistant bubble with results or error
  - _Requirements: 5.1, 5.2, 5.3, 5.6, 5.7_

- [x] 12. Frontend unit tests
  - Create tests for `DataTable`, `ChartPanel`, and `ChatBubble` using `jest` + `@testing-library/react`
  - Test chart type rendering, empty state, error state, and table sorting
  - _Requirements: 6.4, 6.5, 5.6_

- [x] 13. Frontend Dockerfile
  - Create `frontend/Dockerfile` with multi-stage build: `npm ci && npm run build` in builder, serve with `next start` in runtime
  - Expose port 3000
  - _Requirements: 7.1, 7.6_

- [x] 14. Nginx configuration
  - Create `nginx/nginx.conf` proxying `/` to `frontend:3000` and `/api` to `backend:8000`
  - Enable gzip for `text/plain`, `application/json`, `text/css`, `application/javascript`
  - Add static asset cache headers (`Cache-Control: public, max-age=31536000`) for `/_next/static`
  - Add WebSocket support headers (`Upgrade`, `Connection`)
  - Block external access to `/metrics`
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 15. Complete docker-compose.yml
  - Fill in all service definitions: frontend, backend, nginx, prometheus, grafana, loki, promtail
  - Add CPU/memory limits for each service
  - Add health checks for frontend (`/`), backend (`/health`), and nginx
  - Configure named volumes for grafana data, loki data, and SQLite history
  - Wire environment variables from `.env` file
  - _Requirements: 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [x] 16. Monitoring stack configuration
- [x] 16.1 Configure Prometheus
  - Create `monitoring/prometheus.yml` with scrape config targeting `backend:8000/metrics` every 15s
  - _Requirements: 11.1_

- [x] 16.2 Configure Loki and Promtail
  - Create `monitoring/loki-config.yml` with filesystem storage config
  - Create `monitoring/promtail-config.yml` to tail Docker container logs and ship to Loki with `container` label
  - _Requirements: 11.3_

- [x] 16.3 Configure Grafana datasources and dashboards
  - Create `monitoring/grafana/datasources.yml` provisioning Prometheus and Loki datasources
  - Create `monitoring/grafana/dashboards/supachat.json` with panels: request rate, p95 latency, error rate
  - Create `monitoring/grafana/dashboards/infrastructure.json` with panels: CPU, memory, container uptime
  - Create a Logs panel in the SupaChat dashboard querying Loki for error-level logs
  - _Requirements: 11.2, 11.4, 11.5_

- [x] 17. GitHub Actions CI/CD pipeline
  - Create `.github/workflows/deploy.yml` triggered on push to `main`
  - Job 1 `test`: run `pytest` (backend) and `jest --ci` (frontend); fail fast on error
  - Job 2 `build-push`: build and push `supachat-frontend` and `supachat-backend` images to GHCR with SHA tag
  - Job 3 `deploy` (needs `build-push`): SSH to EC2, `docker-compose pull`, `docker-compose up -d`, verify with `docker-compose ps`
  - Store all secrets in GitHub Secrets: `EC2_SSH_KEY`, `EC2_HOST`, `GHCR_TOKEN`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `OPENAI_API_KEY`
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [x] 18. EC2 bootstrap script
  - Create `scripts/bootstrap-ec2.sh` that installs Docker, Docker Compose, clones the repo, copies `.env`, and runs `docker-compose up -d`
  - Script must be idempotent (safe to run multiple times)
  - _Requirements: 9.2, 9.3, 9.4_

- [x] 19. DevOps Agent (bonus)
- [x] 19.1 Implement DevOps Agent FastAPI app
  - Create `devops-agent/app/main.py` with endpoints: `POST /agent/deploy`, `POST /agent/restart`, `GET /agent/logs`, `POST /agent/diagnose`, `GET /agent/health`, `POST /agent/alert`
  - Use `subprocess` to run Docker CLI commands for deploy/restart/logs
  - _Requirements: 12.1, 12.2, 12.3, 12.5_

- [x] 19.2 Implement LLM-powered log summarization and RCA
  - In `devops-agent/app/main.py`, call LLM API in `/agent/logs` to summarize fetched log lines
  - In `/agent/diagnose`, accept CI failure log text and return LLM-generated root cause analysis
  - In `/agent/alert`, accept Grafana webhook payload and return diagnostic summary
  - _Requirements: 12.3, 12.4, 12.6_

- [x] 19.3 Add devops-agent service to docker-compose
  - Add `devops-agent` service with port 8001, mount Docker socket (`/var/run/docker.sock`) for container management
  - Add CPU/memory limits and health check
  - _Requirements: 12.1, 12.2_

- [x] 20. README documentation
  - Write `README.md` covering: architecture diagram, prerequisites, local setup with `docker-compose up`, environment variable reference, EC2 deployment steps, CI/CD pipeline description, Grafana dashboard screenshots/links, and list of AI tools used
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_
