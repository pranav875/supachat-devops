"""
DevOps Agent — FastAPI sidecar for AI-powered deployment automation and log analysis.

Endpoints:
  POST /agent/deploy    — trigger docker-compose pull + up -d
  POST /agent/restart   — restart a named container
  GET  /agent/logs      — fetch recent logs + LLM summary
  POST /agent/diagnose  — accept CI failure log text, return RCA
  GET  /agent/health    — consolidated health check across all services
  POST /agent/alert     — Grafana webhook receiver → diagnostic summary
"""

import os
import subprocess
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="DevOps Agent", version="1.0.0")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

COMPOSE_PROJECT_DIR = os.getenv("COMPOSE_PROJECT_DIR", "/app")
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://frontend:3000")
NGINX_URL = os.getenv("NGINX_URL", "http://nginx:80")
LOG_LINES = int(os.getenv("LOG_LINES", "100"))

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class RestartRequest(BaseModel):
    container: str  # e.g. "backend", "frontend"

class DiagnoseRequest(BaseModel):
    log_text: str   # raw CI failure log

class AlertPayload(BaseModel):
    """Grafana webhook payload (simplified)."""
    title: str = ""
    message: str = ""
    state: str = ""
    alerts: list[dict[str, Any]] = []

class AgentResponse(BaseModel):
    status: str
    output: str = ""
    summary: str = ""

# ---------------------------------------------------------------------------
# Helpers — subprocess
# ---------------------------------------------------------------------------

def _run(cmd: list[str], cwd: str | None = None, timeout: int = 120) -> str:
    """Run a shell command and return combined stdout+stderr. Raises on non-zero exit."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd or COMPOSE_PROJECT_DIR,
        timeout=timeout,
    )
    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        raise RuntimeError(f"Command {cmd} failed (exit {result.returncode}):\n{output}")
    return output

# ---------------------------------------------------------------------------
# Helpers — LLM
# ---------------------------------------------------------------------------

async def _call_llm(system_prompt: str, user_message: str) -> str:
    """Dispatch to the configured LLM provider and return the raw text response."""
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    if openai_key:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=openai_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
        )
        return response.choices[0].message.content or ""

    if anthropic_key:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=anthropic_key)
        response = await client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=0,
        )
        return response.content[0].text if response.content else ""

    raise RuntimeError("No LLM provider configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY.")

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/agent/health")
async def agent_health():
    """
    Consolidated health check — queries all service health endpoints.
    Requirements: 12.5
    """
    services = {
        "backend": f"{BACKEND_URL}/health",
        "frontend": f"{FRONTEND_URL}/",
        "nginx": f"{NGINX_URL}/",
    }
    results: dict[str, str] = {}
    overall = "healthy"

    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in services.items():
            try:
                resp = await client.get(url)
                results[name] = "healthy" if resp.status_code < 400 else f"unhealthy ({resp.status_code})"
            except Exception as exc:
                results[name] = f"unreachable ({exc})"
                overall = "degraded"

    return {"status": overall, "services": results}


@app.post("/agent/deploy", response_model=AgentResponse)
async def deploy():
    """
    Trigger docker-compose pull + up -d.
    Requirements: 12.1
    """
    try:
        pull_out = _run(["docker", "compose", "pull"])
        up_out = _run(["docker", "compose", "up", "-d", "--remove-orphans"])
        output = pull_out + "\n" + up_out
        return AgentResponse(status="success", output=output)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/agent/restart", response_model=AgentResponse)
async def restart(req: RestartRequest):
    """
    Restart a named container.
    Requirements: 12.2
    """
    try:
        output = _run(["docker", "compose", "restart", req.container])
        return AgentResponse(status="success", output=output)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/agent/logs", response_model=AgentResponse)
async def logs(container: str = "backend", lines: int = LOG_LINES):
    """
    Fetch recent container logs and return an LLM-generated summary of errors/anomalies.
    Requirements: 12.3
    """
    try:
        raw_logs = _run(["docker", "compose", "logs", "--no-color", f"--tail={lines}", container])
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # LLM summarization (req 12.3)
    try:
        summary = await _call_llm(
            "You are a DevOps expert. Analyze the following container logs and provide a concise "
            "summary highlighting any errors, warnings, or anomalies. If everything looks normal, say so.",
            f"Container: {container}\n\nLogs:\n{raw_logs[-8000:]}",  # trim to avoid token limits
        )
    except RuntimeError:
        summary = "LLM unavailable — raw logs returned without summary."

    return AgentResponse(status="success", output=raw_logs, summary=summary)


@app.post("/agent/diagnose", response_model=AgentResponse)
async def diagnose(req: DiagnoseRequest):
    """
    Accept CI failure log text and return an LLM-generated root cause analysis.
    Requirements: 12.4
    """
    try:
        rca = await _call_llm(
            "You are a senior DevOps engineer. Analyze the following CI/CD pipeline failure log "
            "and provide a clear root cause analysis with actionable remediation steps.",
            f"CI Failure Log:\n{req.log_text[-8000:]}",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=f"LLM unavailable: {exc}")

    return AgentResponse(status="success", summary=rca)


@app.post("/agent/alert", response_model=AgentResponse)
async def alert(payload: AlertPayload):
    """
    Grafana webhook receiver — returns an LLM-generated diagnostic summary.
    Requirements: 12.6
    """
    # Build a human-readable description of the alert
    alert_details = f"Title: {payload.title}\nState: {payload.state}\nMessage: {payload.message}\n"
    if payload.alerts:
        alert_details += "\nAlert details:\n"
        for a in payload.alerts:
            alert_details += f"  - {a}\n"

    try:
        summary = await _call_llm(
            "You are a DevOps on-call engineer. A Grafana alert has fired. "
            "Analyze the alert details and provide a concise diagnostic summary with "
            "likely causes and recommended immediate actions.",
            alert_details,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=f"LLM unavailable: {exc}")

    return AgentResponse(status="received", summary=summary)
