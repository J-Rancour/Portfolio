# Multi-stage build: compile C++ in a stage that has a compiler, then copy only
# the .so into a slim runtime image (smaller, fewer CVEs, no toolchain in prod).
#   docker build -t wx-api .
#   docker run --rm -p 8000:8000 wx-api

# ---- stage 1: build the C++ core ------------------------------------------
# Same base image as the runtime, so the .so is linked against the same
# glibc/libstdc++ it will run with. Building on a newer distro and running on an
# older one fails at load time with "GLIBCXX_3.4.xx not found".
FROM python:3.14-slim AS native
RUN apt-get update && apt-get install -y --no-install-recommends g++ && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY native/ .
RUN sh build.sh

# ---- stage 2: runtime ------------------------------------------------------
FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 && rm -rf /var/lib/apt/lists/*
WORKDIR /app

# Dependencies first: this layer stays cached until requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY --from=native /src/build/libwxcore.so native/build/libwxcore.so

# Don't run as root inside the container.
RUN useradd --create-home appuser && mkdir data && chown appuser data
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"
# 0.0.0.0 so traffic from outside the container reaches uvicorn.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
