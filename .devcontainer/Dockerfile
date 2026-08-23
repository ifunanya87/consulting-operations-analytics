# Opwfficial Python development container
FROM mcr.microsoft.com/devcontainers/python:1-3.11-bullseye

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set uv environment variables
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Set the working directory
WORKDIR /workspaces/${localWorkspaceFolderBasename}
