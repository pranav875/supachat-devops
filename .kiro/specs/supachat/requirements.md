# Requirements Document

## Introduction

SupaChat is a conversational analytics application built on top of a Supabase PostgreSQL blog analytics database. Users can query the database using natural language, which gets translated into SQL/MCP calls via a backend service. Results are returned as chatbot responses, data tables, and interactive Recharts graphs. The project also encompasses a full DevOps lifecycle: Dockerization, EC2 deployment, Nginx reverse proxy, GitHub Actions CI/CD, and a Prometheus/Grafana/Loki monitoring stack. A bonus DevOps Agent provides AI-powered deployment automation and log analysis.

---

## Requirements

### Requirement 1 — Supabase Database & Schema

**User Story:** As a developer, I want a Supabase PostgreSQL database seeded with blog analytics data, so that the app has realistic data to query against.

#### Acceptance Criteria

1. WHEN the project is set up THEN the system SHALL have a Supabase project with a `blog_analytics` schema containing tables for articles, topics, views, and engagement metrics.
2. WHEN the database is initialized THEN the system SHALL include seed data covering at least 90 days of daily view counts, article metadata, and topic classifications.
3. IF the Supabase connection string is provided via environment variable THEN the system SHALL connect without hardcoded credentials.

---

### Requirement 2 — MCP Server Integration

**User Story:** As a backend developer, I want an MCP (Model Context Protocol) server that exposes Supabase query capabilities, so that the AI layer can call structured database tools.

#### Acceptance Criteria

1. WHEN the backend starts THEN the system SHALL initialize an MCP server that registers tools for querying the Supabase database.
2. WHEN an MCP tool is called with a SQL query THEN the system SHALL execute it against Supabase and return structured JSON results.
3. WHEN an MCP tool call fails THEN the system SHALL return a structured error response with a descriptive message.
4. IF the database is unreachable THEN the system SHALL respond with a 503-equivalent error without crashing.

---

### Requirement 3 — Natural Language to SQL Translation

**User Story:** As a user, I want to type questions in plain English and have them converted to SQL queries, so that I don't need to know SQL to explore the data.

#### Acceptance Criteria

1. WHEN a user submits a natural language query THEN the system SHALL use an LLM (e.g., OpenAI or Anthropic) to translate it into a valid SQL query targeting the blog analytics schema.
2. WHEN the SQL is generated THEN the system SHALL execute it via the MCP server and return results.
3. IF the LLM cannot generate a valid SQL query THEN the system SHALL return a user-friendly error message explaining the limitation.
4. WHEN the query involves time ranges (e.g., "last 30 days") THEN the system SHALL correctly resolve relative dates to absolute SQL date filters.
5. WHEN the query is ambiguous THEN the system SHALL make a reasonable assumption and include a note about the interpretation in the response.

---

### Requirement 4 — Backend API (FastAPI)

**User Story:** As a frontend developer, I want a REST API backend, so that the frontend can send queries and receive structured responses.

#### Acceptance Criteria

1. WHEN the backend starts THEN the system SHALL expose a `POST /api/query` endpoint that accepts a natural language query string.
2. WHEN `POST /api/query` is called THEN the system SHALL return a JSON response containing: a text summary, tabular data (rows/columns), and chart-ready data series.
3. WHEN the backend starts THEN the system SHALL expose a `GET /health` endpoint returning `{"status": "ok"}` with HTTP 200.
4. WHEN the backend starts THEN the system SHALL expose a `GET /api/history` endpoint returning the last N queries and their results.
5. IF a request body is malformed THEN the system SHALL return HTTP 422 with a descriptive validation error.
6. WHEN the backend is running THEN the system SHALL expose Prometheus metrics at `GET /metrics`.

---

### Requirement 5 — Frontend Chatbot UI (Next.js)

**User Story:** As an end user, I want a chat interface to submit natural language queries and see results, so that I can explore blog analytics conversationally.

#### Acceptance Criteria

1. WHEN the frontend loads THEN the system SHALL display a chat input box and a message history panel.
2. WHEN a user submits a query THEN the system SHALL show a loading indicator while awaiting the backend response.
3. WHEN a response is received THEN the system SHALL display the text summary as a chat bubble.
4. WHEN tabular data is returned THEN the system SHALL render it as a sortable data table below the chat bubble.
5. WHEN chart data is returned THEN the system SHALL render an appropriate Recharts visualization (line, bar, or pie chart) based on the data shape.
6. WHEN an error occurs THEN the system SHALL display a user-friendly error message in the chat.
7. WHEN the page loads THEN the system SHALL display a query history sidebar showing previous queries.
8. IF the user clicks a history item THEN the system SHALL re-display that query's results.

---

### Requirement 6 — Chart Rendering with Recharts

**User Story:** As a user, I want visual charts for time-series and comparative data, so that I can quickly understand trends.

#### Acceptance Criteria

1. WHEN the response contains time-series data THEN the system SHALL render a Recharts `LineChart` with labeled axes.
2. WHEN the response contains categorical comparison data THEN the system SHALL render a Recharts `BarChart`.
3. WHEN the response contains proportional data THEN the system SHALL render a Recharts `PieChart`.
4. WHEN a chart is rendered THEN the system SHALL include a legend, tooltips, and axis labels.
5. IF chart data is empty THEN the system SHALL display a "No data to visualize" message instead of a broken chart.

---

### Requirement 7 — Dockerization

**User Story:** As a DevOps engineer, I want the app fully containerized, so that it runs consistently across environments.

#### Acceptance Criteria

1. WHEN the project is built THEN the system SHALL have a `Dockerfile` for the frontend and a separate `Dockerfile` for the backend.
2. WHEN `docker-compose up` is run THEN the system SHALL start frontend, backend, and monitoring services together.
3. WHEN containers start THEN the system SHALL read all secrets and config from environment variables (no hardcoded values).
4. WHEN defined in docker-compose THEN each service SHALL have CPU and memory limits configured.
5. WHEN defined in docker-compose THEN each service SHALL have a health check configured.
6. WHEN the frontend container starts THEN the system SHALL be accessible on port 3000.
7. WHEN the backend container starts THEN the system SHALL be accessible on port 8000.

---

### Requirement 8 — Nginx Reverse Proxy

**User Story:** As a DevOps engineer, I want Nginx to route traffic to the correct service, so that the app is accessible via a single public URL.

#### Acceptance Criteria

1. WHEN a request hits `/` THEN Nginx SHALL proxy it to the frontend service.
2. WHEN a request hits `/api` THEN Nginx SHALL proxy it to the backend service.
3. WHEN Nginx is configured THEN it SHALL enable gzip compression for text-based responses.
4. WHEN Nginx is configured THEN it SHALL set appropriate cache headers for static assets.
5. IF WebSocket connections are needed THEN Nginx SHALL be configured to support `Upgrade` and `Connection` headers.
6. WHEN Nginx starts THEN it SHALL be included as a service in docker-compose.

---

### Requirement 9 — AWS EC2 Deployment

**User Story:** As a DevOps engineer, I want the app deployed on an EC2 instance, so that it is publicly accessible.

#### Acceptance Criteria

1. WHEN deployed to EC2 THEN the app SHALL be accessible via a public IP or domain.
2. WHEN deploying THEN the system SHALL use a reproducible deployment script (e.g., shell script or Ansible) requiring minimal manual steps.
3. WHEN the EC2 instance is provisioned THEN it SHALL have Docker and Docker Compose installed.
4. WHEN the app is deployed THEN it SHALL run via `docker-compose up -d` with no interactive prompts.

---

### Requirement 10 — GitHub Actions CI/CD

**User Story:** As a developer, I want automated CI/CD, so that every push to main builds, tests, and deploys the app.

#### Acceptance Criteria

1. WHEN code is pushed to the `main` branch THEN the GitHub Actions workflow SHALL build Docker images for frontend and backend.
2. WHEN images are built successfully THEN the workflow SHALL push them to a container registry (Docker Hub or GHCR).
3. WHEN images are pushed THEN the workflow SHALL SSH into the EC2 instance and run `docker-compose pull && docker-compose up -d`.
4. WHEN the deployment step runs THEN the system SHALL achieve zero or minimal downtime using rolling restarts.
5. IF any step fails THEN the workflow SHALL stop and report the failure without deploying broken code.
6. WHEN the workflow runs THEN secrets (SSH key, registry credentials) SHALL be stored in GitHub Secrets, not in code.

---

### Requirement 11 — Monitoring & Logging (Prometheus, Grafana, Loki)

**User Story:** As a DevOps engineer, I want observability into the running system, so that I can detect and diagnose issues quickly.

#### Acceptance Criteria

1. WHEN the monitoring stack starts THEN Prometheus SHALL scrape metrics from the backend `/metrics` endpoint.
2. WHEN the monitoring stack starts THEN Grafana SHALL be accessible and pre-configured with dashboards showing CPU, memory, container health, and request latency.
3. WHEN the monitoring stack starts THEN Loki SHALL collect container logs from all services via Promtail.
4. WHEN Grafana is accessed THEN it SHALL display application logs from Loki in a Logs panel.
5. WHEN error-level logs are generated THEN they SHALL be queryable in Grafana using LogQL.
6. WHEN the monitoring stack is defined THEN it SHALL be included in docker-compose alongside the app services.

---

### Requirement 12 — DevOps Agent (Bonus)

**User Story:** As a DevOps engineer, I want an AI-powered agent that can automate deployment tasks and diagnose issues, so that operational toil is reduced.

#### Acceptance Criteria

1. WHEN the DevOps agent is invoked with a "deploy" command THEN it SHALL trigger a deployment and report the outcome.
2. WHEN the DevOps agent is invoked with a "restart" command THEN it SHALL restart the specified container and confirm success.
3. WHEN the DevOps agent is invoked with a "logs" command THEN it SHALL fetch recent logs and return an AI-generated summary of errors or anomalies.
4. WHEN a CI/CD pipeline fails THEN the DevOps agent SHALL be able to fetch the failure logs and provide an AI-generated root cause analysis.
5. WHEN the DevOps agent runs a health check THEN it SHALL query all service health endpoints and return a consolidated status report.
6. IF an alert fires in Grafana THEN the DevOps agent SHALL be able to receive a webhook and respond with a diagnostic summary.

---

### Requirement 13 — Documentation

**User Story:** As a reviewer, I want a comprehensive README, so that I can understand, set up, and evaluate the project.

#### Acceptance Criteria

1. WHEN the README is read THEN it SHALL include an architecture diagram or description.
2. WHEN the README is read THEN it SHALL include local setup instructions covering prerequisites, environment variables, and `docker-compose up`.
3. WHEN the README is read THEN it SHALL include deployment instructions for EC2.
4. WHEN the README is read THEN it SHALL describe the CI/CD pipeline and how to configure it.
5. WHEN the README is read THEN it SHALL include links or screenshots of Grafana dashboards.
6. WHEN the README is read THEN it SHALL list all AI tools used during development.
