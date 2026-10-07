# syntax=docker/dockerfile:1
# Device-free integration candidate, not the full distribution or a physical release.
# Build context is the RobotTransformation repository root. btcpp is the repository-pinned source.
FROM rust:1.98.1-bookworm@sha256:9a73a5088750b4c95158ab26629c854c3d6fc4b173cb7bc8079ad252d8ed7bfa AS p-build
ENV CARGO_BUILD_JOBS=2 CARGO_INCREMENTAL=0 CARGO_PROFILE_DEV_DEBUG=0
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
WORKDIR /source
COPY rx-platform/Cargo.toml rx-platform/Cargo.lock ./
COPY rx-platform/crates ./crates
COPY rx-platform/proto ./proto
COPY rx-platform/spec ./spec
RUN --mount=type=cache,id=rx-m1-p-registry,target=/usr/local/cargo/registry \
    --mount=type=cache,id=rx-m1-p-target,target=/source/target \
    find /source -path /source/target -prune -o -type f -exec touch {} + && \
    cargo build --release --locked -p rx-platformd && \
    cargo test --locked -p rx-platformd --test delivery_fixture --no-run --message-format=json > /fixture-build.jsonl && \
    mkdir /out && cp target/release/rx-platformd target/release/rx-package-store /out/ && \
    python3 -c 'import json,shutil; a=[json.loads(s) for s in open("/fixture-build.jsonl")]; e=[v["executable"] for v in a if v.get("reason")=="compiler-artifact" and v.get("target",{}).get("name")=="delivery_fixture" and v.get("executable")]; assert len(e)==1; shutil.copyfile(e[0],"/out/delivery_fixture")'

FROM rust:1.98.1-bookworm@sha256:9a73a5088750b4c95158ab26629c854c3d6fc4b173cb7bc8079ad252d8ed7bfa AS s-build
ENV CARGO_BUILD_JOBS=2 CARGO_INCREMENTAL=0 CARGO_PROFILE_DEV_DEBUG=0
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
WORKDIR /source
COPY rx-solutions/Cargo.toml rx-solutions/Cargo.lock ./
COPY rx-solutions/sdk ./sdk
COPY rx-solutions/runtime ./runtime
COPY rx-solutions/drivers ./drivers
COPY rx-solutions/catalogs ./catalogs
COPY rx-solutions/native ./native
COPY rx-solutions/dependencies ./dependencies
COPY rx-solutions/interfaces ./interfaces
COPY rx-solutions/deployment/local-skills/host_runner.py rx-solutions/deployment/local-skills/python_environment.py ./deployment/local-skills/
COPY rx-solutions/deployment/external-adapters ./deployment/external-adapters
RUN --mount=type=cache,id=rx-m1-s-registry,target=/usr/local/cargo/registry \
    --mount=type=cache,id=rx-m1-s-target,target=/source/target \
    find /source -path /source/target -prune -o -type f -exec touch {} + && \
    cargo build --release --locked -p rx-host -p rx-executor -p rx-process-package -p rx-device-package -p rx-process && \
    mkdir /out && cp target/release/rx-hostd target/release/rx-executor-service target/release/rx-process-package target/release/rx-device-package target/release/rx-process-compile /out/ && \
    cargo test --locked -p rx-host --test external_process > /out/external-process.log && \
    cargo test --locked -p rx-host --features test-harness --test process_crash sigkill_at_both_journal_native_boundaries_never_replays_device_effect -- --exact > /out/host-recovery.log && \
    cargo test --locked -p rx-executor --test assignment_journal lost_run_initialization_reply_recovers_binding_without_reinitializing -- --exact > /out/executor-recovery.log && \
    cargo test --locked -p rx-executor --test assignment_journal run_creation_marker_cannot_change_after_header_initialization -- --exact > /out/executor-identity.log
RUN find /source -type f -not -path '/source/target/*' -print0 | sort -z | xargs -0 sha256sum > /out/source.sha256

FROM python:3.12-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e AS bt-build
RUN apt-get update && apt-get install -y --no-install-recommends g++ cmake make nlohmann-json3-dev libzmq3-dev libssl-dev && rm -rf /var/lib/apt/lists/*
COPY --from=btcpp / /btcpp/
COPY rx-solutions/native/executor /executor/
RUN --network=none cmake -S /executor -B /build -DCMAKE_BUILD_TYPE=Release -DBTCPP_SOURCE=/btcpp -DRX_BUILD_TEST_HARNESS=OFF && cmake --build /build --target rx-bt-engine -j2
COPY rx-solutions/examples/process/material-alignment/observer.cpp /observer.cpp
RUN g++ -std=c++17 -O2 -Wall -Wextra -Werror /observer.cpp -o /build/m1-observer -lcrypto

FROM node:26.5.0-bookworm-slim@sha256:2d49d876e96237d76de412761cf05dbfe5aee325cc4406a4d41d5824c5bb8beb AS ui-build
WORKDIR /src
COPY rx-solutions/apps/operator/package.json rx-solutions/apps/operator/package-lock.json ./
RUN npm ci
COPY rx-solutions/apps/operator/ ./
RUN npm run build

FROM python:3.12-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 libzmq5 libssl3 && rm -rf /var/lib/apt/lists/* && \
    mkdir -p /data /run/rx /run/rx-host /opt/rx/bin /opt/rx/test && chown -R 10001:10001 /data /run/rx /run/rx-host
COPY --from=p-build /out/rx-platformd /out/rx-package-store /usr/local/bin/
COPY --from=p-build /out/delivery_fixture /opt/rx/test/delivery_fixture
RUN chmod 755 /opt/rx/test/delivery_fixture
COPY --from=s-build /out/ /opt/rx/bin/
COPY --from=bt-build /build/rx-bt-engine /opt/rx/bin/
COPY --from=bt-build /build/m1-observer /opt/rx/bin/
COPY --from=ui-build /src/dist/ /opt/rx/operator/
COPY rx-solutions/LICENSE rx-solutions/NOTICE /opt/rx/
COPY --from=btcpp /LICENSE /opt/rx/licenses/BehaviorTree.CPP/LICENSE
COPY rx-solutions/deployment/local-skills/rx rx-solutions/deployment/local-skills/runtime_client.py rx-solutions/deployment/local-skills/image_identity.py rx-solutions/deployment/local-skills/python_environment.py rx-solutions/deployment/local-skills/definitions_client.py rx-solutions/deployment/local-skills/workflow_client.py rx-solutions/deployment/local-skills/execution_client.py /opt/rx/client/
COPY rx-solutions/deployment/local-skills/host_runner.py rx-solutions/deployment/local-skills/python_environment.py /opt/rx/python/
RUN cp /usr/local/bin/python3.12 /opt/rx/python/python && python3 -c 'import hashlib,json,pathlib; p=pathlib.Path("/opt/rx/python"); (p/"release.json").write_text(json.dumps({"schema":"rx.python-host-release.v1","interpreter_sha256":hashlib.sha256((p/"python").read_bytes()).hexdigest()}))'
COPY rx-solutions/tools/test_material_alignment_observer.py /opt/rx/observer-test/tools/
COPY rx-solutions/examples/process/material-alignment/ /opt/rx/observer-test/examples/process/material-alignment/
COPY rx-solutions/deployment/external-adapters/rx_external_adapter.py /opt/rx/observer-test/deployment/external-adapters/
USER 10001:10001
RUN RX_M1_OBSERVER_BINARY=/opt/rx/bin/m1-observer RX_M1_OBSERVER_DIAGNOSTICS=/data/observer-latency.json /opt/rx/python/python -B /opt/rx/observer-test/tools/test_material_alignment_observer.py
ENTRYPOINT ["/usr/local/bin/rx-platformd"]
