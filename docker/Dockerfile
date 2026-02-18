ARG PACKAGE_NAME_INTERNAL
ARG PACKAGE_NAME_EXTERNAL
ARG UV_INDEX
ARG UV_INDEX_USERNAME

ARG DEBIAN_VERSION='trixie'
ARG PYTHON_VERSION='3.13'
ARG SOPS_VERSION='v3.11.0'

###############################################################################
FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-${DEBIAN_VERSION}-slim AS builder
###############################################################################

ARG PACKAGE_NAME_INTERNAL
ARG UV_INDEX
ARG UV_INDEX_USERNAME

ENV UV_COMPILE_BYTECODE='1'
ENV UV_LINK_MODE='copy'
ENV UV_NATIVE_TLS='true'
ENV UV_PRERELEASE='disallow'
ENV UV_PYTHON_DOWNLOADS='0'

WORKDIR /app

COPY docker/root.pem /usr/local/share/ca-certificates/root.crt
RUN update-ca-certificates
RUN --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=secret,id=UV_INDEX_PASSWORD,env=UV_INDEX_PASSWORD \
    <<'EOF'
    set -e
    if [ -n "${UV_INDEX}" ]; then
      if [ "${UV_INDEX#*=}" = "${UV_INDEX}" ]; then
        UV_INDEX="custom=${UV_INDEX}"
      fi
      NAME=$(printf '%s\n' "${UV_INDEX%%=*}" | tr '[:lower:]' '[:upper:]')
      export "UV_INDEX_${NAME}_USERNAME"="${UV_INDEX_USERNAME}"
      export "UV_INDEX_${NAME}_PASSWORD"="${UV_INDEX_PASSWORD}"
    fi
    uv sync --no-dev --no-install-project --locked
EOF

COPY README.md /app/README.md
COPY pyproject.toml /app/pyproject.toml
COPY src/${PACKAGE_NAME_INTERNAL} /app/src/${PACKAGE_NAME_INTERNAL}
COPY uv.lock /app/uv.lock

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=secret,id=UV_INDEX_PASSWORD,env=UV_INDEX_PASSWORD \
    <<'EOF'
    set -e
    if [ -n "${UV_INDEX}" ]; then
      if [ "${UV_INDEX#*=}" = "${UV_INDEX}" ]; then
        UV_INDEX="custom=${UV_INDEX}"
      fi
      NAME=$(printf '%s\n' "${UV_INDEX%%=*}" | tr '[:lower:]' '[:upper:]')
      export "UV_INDEX_${NAME}_USERNAME"="${UV_INDEX_USERNAME}"
      export "UV_INDEX_${NAME}_PASSWORD"="${UV_INDEX_PASSWORD}"
    fi
    uv sync --no-dev --locked
EOF

###############################################################################
FROM ghcr.io/getsops/sops:${SOPS_VERSION} AS sops
# https://github.com/getsops/sops/pkgs/container/sops
###############################################################################

###############################################################################
FROM python:${PYTHON_VERSION}-slim-${DEBIAN_VERSION}
###############################################################################

ARG PACKAGE_NAME_EXTERNAL

RUN <<'EOF'
    set -e
    apt-get update
    apt-get install -y --no-install-recommends age
    apt-get install -y --no-install-recommends build-essential libpq-dev
    rm -rf /var/lib/apt/lists/*
EOF

COPY --from=builder /app /app
COPY --from=sops /usr/local/bin/sops /usr/local/bin/

ENV PATH=/app/.venv/bin:${PATH}
ENV PATH=/root/.local/bin:${PATH}

WORKDIR /app

RUN <<'EOF'
    set -e
    echo "#!/usr/bin/env sh\nexec ${PACKAGE_NAME_EXTERNAL}-cli \"\$@\"" > /usr/local/bin/entrypoint.sh
    chmod u+x /usr/local/bin/entrypoint.sh
EOF

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
