FROM python:3.12-slim-bookworm

# Install uv with a specific version for reproducibility
COPY --from=ghcr.io/astral-sh/uv:0.6.0 /uv /uvx /bin/

WORKDIR /app

# Create and activate virtual environment
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN uv venv

# Install dependencies first (this layer will be cached)
COPY pyproject.toml uv.lock ./
# Hash of dependency files ensures cache invalidation when dependencies change
RUN --mount=type=cache,target=/root/.cache/uv \
    echo "Dependencies hash: $(sha256sum pyproject.toml uv.lock)" && \
    uv sync --frozen --no-install-project

# Now copy the project code
COPY . .

# Install the project dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Set environment variables
ENV PORT=8080
ENV HOST=0.0.0.0
ENV ENVIRONMENT=production

EXPOSE 8080

# Use exec form of CMD to ensure proper signal handling
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]
