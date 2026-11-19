# The research console in a container. The repository is mounted, not copied, so the page
# always shows the working tree's models, reports and logs (console/compose.yaml).
FROM python:3.13-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends procps \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir "z3-solver==5.3.1"
ENV PYTHONPATH=/repo PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /repo
EXPOSE 8770
CMD ["python", "-m", "console.server", "--host", "0.0.0.0", "--port", "8770"]
