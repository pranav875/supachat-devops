"""
Seed script for SupaChat blog analytics database.
Inserts ~50 articles across 8 topics and 90 days of view/engagement records.

Usage:
    DATABASE_URL=postgres://user:pass@host/db python seed.py
"""

import asyncio
import os
import random
from datetime import date, timedelta

import asyncpg

TOPICS = ["AI", "Web Development", "DevOps", "Data Science", "Security", "Cloud", "Mobile", "Open Source"]

ARTICLES = [
    # AI
    ("Understanding Transformer Architecture", "AI", "Alice Chen"),
    ("Fine-tuning LLMs on Custom Datasets", "AI", "Bob Martinez"),
    ("Prompt Engineering Best Practices", "AI", "Alice Chen"),
    ("RAG vs Fine-tuning: When to Use Each", "AI", "Carol White"),
    ("Building AI Agents with Tool Use", "AI", "David Kim"),
    ("Vector Databases Explained", "AI", "Alice Chen"),
    ("Evaluating LLM Output Quality", "AI", "Bob Martinez"),
    # Web Development
    ("React Server Components Deep Dive", "Web Development", "Eve Johnson"),
    ("Building APIs with FastAPI", "Web Development", "Frank Lee"),
    ("TypeScript Generics in Practice", "Web Development", "Eve Johnson"),
    ("CSS Container Queries Guide", "Web Development", "Grace Park"),
    ("Next.js App Router Migration", "Web Development", "Frank Lee"),
    ("Web Performance Optimization Tips", "Web Development", "Grace Park"),
    ("Testing React Components with RTL", "Web Development", "Eve Johnson"),
    # DevOps
    ("Docker Multi-stage Builds", "DevOps", "Henry Brown"),
    ("Kubernetes for Beginners", "DevOps", "Iris Davis"),
    ("GitHub Actions CI/CD Pipelines", "DevOps", "Henry Brown"),
    ("Infrastructure as Code with Terraform", "DevOps", "Jack Wilson"),
    ("Monitoring with Prometheus and Grafana", "DevOps", "Iris Davis"),
    ("Zero-downtime Deployments", "DevOps", "Henry Brown"),
    ("Log Aggregation with Loki", "DevOps", "Jack Wilson"),
    # Data Science
    ("Pandas vs Polars Performance", "Data Science", "Karen Taylor"),
    ("Feature Engineering Techniques", "Data Science", "Liam Anderson"),
    ("Time Series Forecasting with Prophet", "Data Science", "Karen Taylor"),
    ("Data Visualization with Plotly", "Data Science", "Mia Thomas"),
    ("SQL Window Functions for Analytics", "Data Science", "Liam Anderson"),
    ("Building Data Pipelines with Airflow", "Data Science", "Karen Taylor"),
    # Security
    ("OWASP Top 10 for Developers", "Security", "Noah Jackson"),
    ("JWT Authentication Best Practices", "Security", "Olivia Harris"),
    ("Secrets Management in Production", "Security", "Noah Jackson"),
    ("SQL Injection Prevention Guide", "Security", "Olivia Harris"),
    ("Zero Trust Architecture Overview", "Security", "Peter Clark"),
    # Cloud
    ("AWS Lambda Cold Start Optimization", "Cloud", "Quinn Lewis"),
    ("Multi-region Deployment Strategies", "Cloud", "Rachel Walker"),
    ("Cloud Cost Optimization Tips", "Cloud", "Quinn Lewis"),
    ("Serverless vs Containers Trade-offs", "Cloud", "Rachel Walker"),
    ("S3 Best Practices for Production", "Cloud", "Sam Hall"),
    ("Cloud Native Application Design", "Cloud", "Quinn Lewis"),
    # Mobile
    ("React Native vs Flutter in 2024", "Mobile", "Tina Allen"),
    ("Mobile App Performance Profiling", "Mobile", "Uma Young"),
    ("Offline-first Mobile Architecture", "Mobile", "Tina Allen"),
    ("Push Notifications Deep Dive", "Mobile", "Victor King"),
    ("Mobile Security Checklist", "Mobile", "Uma Young"),
    # Open Source
    ("How to Write Good Documentation", "Open Source", "Wendy Scott"),
    ("Contributing to Open Source Projects", "Open Source", "Xavier Green"),
    ("Semantic Versioning Explained", "Open Source", "Wendy Scott"),
    ("Open Source Licensing Guide", "Open Source", "Xavier Green"),
    ("Building a Healthy OSS Community", "Open Source", "Yara Adams"),
    ("Maintaining Open Source Burnout", "Open Source", "Wendy Scott"),
    ("OSS Funding Models That Work", "Open Source", "Xavier Green"),
]


async def seed(database_url: str) -> None:
    conn = await asyncpg.connect(database_url)
    try:
        # Run migration first
        migration_path = os.path.join(os.path.dirname(__file__), "migrations", "001_schema.sql")
        with open(migration_path) as f:
            await conn.execute(f.read())

        # Clear existing seed data
        await conn.execute("DELETE FROM article_engagement")
        await conn.execute("DELETE FROM article_views")
        await conn.execute("DELETE FROM articles")

        # Insert articles
        today = date.today()
        article_ids = []
        for title, topic, author in ARTICLES:
            # Published between 90 and 1 days ago
            days_ago = random.randint(1, 90)
            published_at = today - timedelta(days=days_ago)
            row = await conn.fetchrow(
                "INSERT INTO articles (title, topic, author, published_at) VALUES ($1, $2, $3, $4) RETURNING id",
                title, topic, author, published_at,
            )
            article_ids.append((row["id"], published_at))

        print(f"Inserted {len(article_ids)} articles.")

        # Insert 90 days of views and engagement for each article
        views_rows = []
        engagement_rows = []

        for article_id, published_at in article_ids:
            # Only generate records from the article's publish date onward
            start_date = max(published_at.date() if hasattr(published_at, "date") else published_at,
                             today - timedelta(days=89))
            current = start_date
            while current <= today:
                # Simulate realistic view counts with some variance
                base_views = random.randint(50, 800)
                # Newer articles get a traffic spike
                age_days = (today - current).days
                spike = max(0, 200 - age_days * 2)
                view_count = base_views + spike + random.randint(-20, 20)
                view_count = max(1, view_count)

                views_rows.append((article_id, current, view_count))

                likes = int(view_count * random.uniform(0.02, 0.08))
                comments = int(view_count * random.uniform(0.005, 0.02))
                shares = int(view_count * random.uniform(0.01, 0.05))
                engagement_rows.append((article_id, current, likes, comments, shares))

                current += timedelta(days=1)

        await conn.executemany(
            "INSERT INTO article_views (article_id, viewed_date, view_count) VALUES ($1, $2, $3)",
            views_rows,
        )
        await conn.executemany(
            "INSERT INTO article_engagement (article_id, event_date, likes, comments, shares) VALUES ($1, $2, $3, $4, $5)",
            engagement_rows,
        )

        print(f"Inserted {len(views_rows)} view records.")
        print(f"Inserted {len(engagement_rows)} engagement records.")
        print("Seed complete.")

    finally:
        await conn.close()


if __name__ == "__main__":
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("ERROR: DATABASE_URL environment variable is not set.")
    asyncio.run(seed(database_url))
