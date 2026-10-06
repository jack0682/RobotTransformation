#!/usr/bin/env python3
"""Build a source-pinned local-simulation installer bundle; never publish it."""
import argparse
import hashlib
import json
import re
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def command(*args, **kwargs):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1")
    for key in list(env):
        if key in {"GIT_DIR", "GIT_COMMON_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE", "GIT_REPLACE_REF_BASE", "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS"} or key.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
            env.pop(key)
    return subprocess.check_output(args, text=True, env=env, **kwargs).strip()


def source_identity(path):
    path = path.resolve()
    git_root = Path(command("git", "-C", str(path), "rev-parse", "--show-toplevel")).resolve()
    component = path.relative_to(git_root).as_posix()
    repository = json.loads((git_root / "repository-settings.json").read_text())["repository"]
    if repository not in {"jack0682/RobotTransformation", "jack0682/rx-platform", "jack0682/rx-solutions"}:
        raise ValueError("Unsupported source repository identity")
    head = command("git", "-C", str(path), "rev-parse", "HEAD")
    if not re.fullmatch("[0-9a-f]{40}", head):
        raise ValueError("Full source commit required")
    if command("git", "-C", str(git_root), "status", "--porcelain"):
        raise ValueError("Release source must be a clean committed checkout")
    tree = command("git", "-C", str(git_root), "rev-parse", head + ("^{tree}" if component == "." else ":" + component))
    return {"repository": repository, "commit": head, "component_path": component, "tree_oid": tree}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--platform", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--architecture", choices=("arm64", "amd64"), required=True)
    p.add_argument("--version", default="0.4.0-dev.1")
    p.add_argument("--build-jobs", type=int, choices=(1, 2), default=2)
    p.add_argument("--cache-namespace", default="local")
    args = p.parse_args()
    if not re.fullmatch(r"[a-z0-9-]{1,64}", args.cache_namespace):
        raise ValueError("Invalid Cargo cache namespace")
    sources = {"platform": source_identity(args.platform), "solutions": source_identity(ROOT)}
    args.output.mkdir(parents=True, exist_ok=False)
    image = "rx-local-skills:" + args.version + "-" + args.architecture
    subprocess.run(["docker", "build", "--platform", "linux/" + args.architecture,
                    "--build-context", "platform=" + str(args.platform.resolve()),
                    "--build-arg", "CARGO_BUILD_JOBS=" + str(args.build_jobs),
                    "--build-arg", "RX_CARGO_CACHE_SCOPE=" + args.cache_namespace,
                    "-f", str(ROOT / "docker/Skills.Dockerfile"), "-t", image, str(ROOT)], check=True)
    bundle = args.output / "bundle"
    shutil.copytree(ROOT / "deployment/local-skills", bundle,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("LICENSE", "NOTICE"):
        shutil.copyfile(ROOT / name, bundle / name)
    (bundle / "rx").chmod(0o755)
    archive = bundle / "runtime.tar.gz"
    import gzip
    with archive.open("wb") as target:
        child = subprocess.Popen(["docker", "save", image], stdout=subprocess.PIPE)
        with gzip.GzipFile(fileobj=target, mode="wb", mtime=0) as stream:
            shutil.copyfileobj(child.stdout, stream)
        child.stdout.close()
        if child.wait(): raise RuntimeError("docker save failed")
    manifest = {"schema": "rx.local-sim.release.v1", "version": args.version,
                "architecture": args.architecture, "image": image,
                "image_id": command("docker", "image", "inspect", image, "--format", "{{.Id}}"),
                "image_sha256": hashlib.file_digest(archive.open("rb"), "sha256").hexdigest(),
                "platform_commit": sources["platform"]["commit"],
                "solutions_commit": sources["solutions"]["commit"],
                "source_dirty": False, "component_sources": sources,
                "build_jobs": args.build_jobs, "cache_namespace": args.cache_namespace,
                "physical_execution": "NOT_SUPPORTED"}
    if sources != {"platform": source_identity(args.platform), "solutions": source_identity(ROOT)}:
        raise ValueError("Source identity changed during the build")
    (bundle / "release.json").write_text(json.dumps(manifest, indent=2) + "\n")
    name = "rx-local-skills-" + args.version + "-linux-" + args.architecture + ".tar.gz"
    with tarfile.open(args.output / name, "w:gz") as stream:
        stream.add(bundle, arcname="rx-local-skills")
    digest = hashlib.file_digest((args.output / name).open("rb"), "sha256").hexdigest()
    (args.output / "CHECKSUMS.sha256").write_text(digest + "  " + name + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
