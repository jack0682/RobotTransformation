"""Authored finite SIM counter. Uses the released helper, never RX core source.

The mutable simulator files are native facts, not an authority/recovery ledger.
The deliberate fault modes are for isolated CI only. This provider never retries
an operation or decides that UNKNOWN can be released.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys

SDK_PATH = Path(__file__).with_name("rx_external_adapter.py")
module = importlib.util.spec_from_file_location("released_external_sdk", SDK_PATH)
sdk = importlib.util.module_from_spec(module)
module.loader.exec_module(sdk)
if len(sys.argv) < 5 or sys.argv[1] != "--simulation-dir":
    raise ValueError("pinned --simulation-dir and Host-owned protocol arguments required")
SIM = Path(sys.argv[2])
if not SIM.is_absolute() or SIM.is_symlink() or not SIM.is_dir():
    raise ValueError("existing isolated simulation directory required")


def load(name, default):
    path = SIM / name
    if not path.exists():
        return default
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1_048_576:
        raise ValueError("regular bounded simulator file required")
    return json.loads(path.read_bytes())


def fault():
    mode = load("fault.json", {"mode": "none"}).get("mode")
    if mode not in ("none", "after_entry_exit", "drop_completion"):
        raise ValueError("unknown isolated fault mode")
    return mode


def boundary_marker(name, correlation):
    # Independent simulator marker, never a Host/P authority or completion decision.
    value = {"operation": correlation["operation"], "invocation": correlation["invocation"],
             "selection": correlation["selection"], "acquired_at": sdk.now()}
    with (SIM / name).open("ab") as stream:
        stream.write(sdk.encoded(value) + b"\n"); stream.flush(); os.fsync(stream.fileno())


class Counter:
    def after_entry(self, correlation):
        boundary_marker("entries.jsonl", correlation)
        if fault() == "after_entry_exit":
            os._exit(31)  # Deliberate process loss before the simulated effect.

    def execute(self, envelope, correlation):
        if envelope.get("primitive") != "count":
            raise ValueError("undeclared primitive")
        increment = envelope["values"]["increment"]
        bounds = increment.get("data", {}).get("range", {})
        if (increment.get("unit") != "unitless" or increment.get("data", {}).get("kind") != "NUMBER"
                or set(bounds) != {"min", "max"} or any(type(bounds[k]) not in (int, float) or bounds[k] != 1 for k in bounds)):
            raise ValueError("counter supports only the approved concrete increment 1")
        state = load("state.json", {"count": 0})
        before = state["count"]
        if type(before) is not int or before < 0:
            raise ValueError("counter state invalid")
        event = {"operation": correlation["operation"], "invocation": correlation["invocation"],
                 "selection": correlation["selection"], "primitive": "count", "increment": 1,
                 "count_before": before, "count_after": before + 1, "acquired_at": sdk.now()}
        # This independent native effect trace is distinct from Host/P journals.
        with (SIM / "effects.jsonl").open("ab") as stream:
            stream.write(sdk.encoded(event) + b"\n"); stream.flush(); os.fsync(stream.fileno())
        temporary = SIM / ".counter-next.json"
        with temporary.open("wb") as stream:
            stream.write(sdk.encoded({"count": before + 1})); stream.flush(); os.fsync(stream.fileno())
        temporary.replace(SIM / "state.json")
        directory = os.open(SIM, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(directory)
        finally: os.close(directory)
        return {"status_schema": "m5.counter.completed.v1", "status": 0}

    def after_completion(self, correlation):
        boundary_marker("completions.jsonl", correlation)
        if fault() == "drop_completion":
            os._exit(32)  # SDK completion is durable; the reply is deliberately lost.

    def observe(self, sources):
        count = load("state.json", {"count": 0})["count"]
        values = {"ready": True, "done": count > 0}
        if any(source not in values for source in sources):
            raise ValueError("undeclared observation")
        acquired = sdk.now()  # Actual file-state read time; no cached-time refresh.
        return {source: sdk.sample({"boolean": values[source]}, acquired_at=acquired) for source in sources}

    def custody(self):
        return {key: True for key in ("no_pending_commands", "control_available", "support_stable", "safe_to_drop")}


sdk.serve(Counter())
