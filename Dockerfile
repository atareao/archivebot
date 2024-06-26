###############################################################################
## Builder
###############################################################################
FROM alpine:3.19 as builder

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN echo "**** install Python ****" && \
    apk add --update --no-cache --virtual \
            .build-deps \
            gcc~=13.2 \
            musl-dev~=1.2 \
            python3-dev~=3.11 \
            python3~=3.11 \
            py3-pip~=23.3 \
            poetry~=1.7 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN echo "**** install Python dependencies ****" && \
    poetry install --no-root && rm -rf $POETRY_CACHE_DIR

###############################################################################
## Final image
###############################################################################
FROM alpine:3.19

LABEL maintainer="Lorenzo Carbonell <a.k.a. atareao> lorenzo.carbonell.cerezo@gmail.com"

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONIOENCODING=utf-8 \
    PYTHONUNBUFFERED=1 \
    USER=app \
    UID=101

RUN echo "**** install Python ****" && \
    apk add --update --no-cache \
            ffmpeg~=6.1 \
            sqlite~=3.44 \
            python3~=3.11 && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY run.sh ./archivebot /app/

RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/${USER}" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    "${USER}" && \
    chown -R app:app /app

WORKDIR /app
USER app

CMD ["/bin/sh", "/app/run.sh"]
