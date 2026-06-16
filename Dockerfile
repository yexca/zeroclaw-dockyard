ARG ZEROCLAW_BASE_IMAGE=zeroclaw:0.8.0-beta2-matrix
FROM ${ZEROCLAW_BASE_IMAGE}

ARG ZEROCLAW_INSTALL_PYTHON3=false

USER root

RUN set -eux; \
    install_python3=false; \
    case "$(printf '%s' "${ZEROCLAW_INSTALL_PYTHON3:-false}" | tr '[:upper:]' '[:lower:]')" in \
      1|true|yes|on) install_python3=true ;; \
    esac; \
    if command -v apt-get >/dev/null 2>&1; then \
      apt-get update; \
      DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        dnsutils \
        file \
        findutils \
        iproute2 \
        iputils-ping \
        jq \
        less \
        nano \
        netcat-openbsd \
        procps \
        tar \
        unzip \
        vim-tiny \
        xxd \
        zip \
        $(if [ "$install_python3" = "true" ]; then printf '%s' "python3 python3-pip python3-venv python-is-python3"; fi); \
      rm -rf /var/lib/apt/lists/*; \
    elif command -v apk >/dev/null 2>&1; then \
      apk add --no-cache \
        bash \
        bind-tools \
        busybox-extras \
        ca-certificates \
        curl \
        file \
        findutils \
        iproute2 \
        iputils \
        jq \
        less \
        nano \
        procps \
        tar \
        unzip \
        vim \
        xxd \
        zip \
        $(if [ "$install_python3" = "true" ]; then printf '%s' "python3 py3-pip"; fi); \
      if [ "$install_python3" = "true" ] && ! command -v python >/dev/null 2>&1; then \
        ln -sf /usr/bin/python3 /usr/bin/python; \
      fi; \
    else \
      echo "No supported package manager found; leaving base image unchanged." >&2; \
    fi
