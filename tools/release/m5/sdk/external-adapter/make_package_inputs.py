#!/usr/bin/env python3
"""Author data only. Installed rx-device-package remains the semantic validator."""
import argparse
import hashlib
import json
from pathlib import Path
import uuid


def inputs(context, program, product_pin):
    if context["architecture"] not in ("AMD64", "ARM64"):
        raise ValueError("supported Linux target architecture required")
    if str(uuid.UUID(context["installation"])) != context["installation"]:
        raise ValueError("fresh canonical installation UUID required")
    if not context["resources"] or not context["condition_ids"]:
        raise ValueError("explicit fresh site resource/condition context required")
    reference = product_pin["reference"]
    if reference["schema_id"] != "rx.external-process-program.v1":
        raise ValueError("installed external-program reference required")
    contract = {"implementation": "m5.counter", "version": "1.0.0", "primitive": "count",
                "parameters": {"increment": {"unit": "unitless", "value_type": "NUMBER", "frame": None}}}
    profile = {"schema": "rx.external-process-profile.v1", "protocol": "rx.external-process-channel.v1",
               "program": reference, "commands": {"count": contract},
               "observations": {name: {"schema": "boolean/v1", "unit": "unitless", "value_type": "BOOLEAN",
                    "maximum_age_ns": "1000000000", "maximum_uncertainty_ns": "0"} for name in ("ready", "done")},
               "conditions": {condition: "ready" for condition in context["condition_ids"]}}
    # documents() in the installed assembler normalizes these placeholders and
    # validates the real Program reference. This script does not duplicate that hash.
    intent = {"kind": "FINITE_ACTION", "target": "m5/counter", "profile_digest": "00" * 32,
              "site_config_digest": context["site_config_digest"], "calibration_digests": [],
              "resource_set": context["resources"], "execution_timeout_ms": "10000",
              "prepare_validity_ms": "1000", "completion_rule": "m5.counter.completed.v1",
              "cancel_rule": context.get("cancel_rule", "m5/no-native-retry"),
              "body": {"program": {"program": reference, "parameter_set": {
                  "schema_id": "rx.workflow-parameters.v2", "sha256": hashlib.sha256(b"{}").hexdigest(), "size_bytes": "2"}}}}
    catalog = {"schema": "rx.execution-template-catalog.v2", "installation": context["installation"],
               "cell": context["cell"], "environment": "SIMULATION", "documents": {},
               "templates": {"count": {"action": {"host": context["host"], "intent": intent}, "contract": contract}}}
    outcomes = {"schema": "rx.native-outcome-table.v1", "profile_digest": "00" * 32,
                "completion_rule": "m5.counter.completed.v1", "cases": [{"status_schema": "m5.counter.completed.v1", "statuses": ["0"], "conclusion": "SUCCEEDED"}]}
    assembly = {"schema": "rx.external-process-assembly.v1", "profile": profile, "program": program,
                "catalog": catalog, "outcomes": outcomes}
    recipe = {"schema": "rx.device-package-recipe.v1", "package": "m5/counter", "publisher": "m5-fixture-author", "version": "1.0.0",
              "targets": [{"architecture": context["architecture"], "os": "LINUX", "ros_distribution": None}]}
    return assembly, recipe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("context", "program", "program-reference", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    a = parser.parse_args()
    assembly, recipe = inputs(json.loads(a.context.read_bytes()), json.loads(a.program.read_bytes()), json.loads(a.program_reference.read_bytes()))
    a.output.mkdir(parents=True, exist_ok=False)
    for name, value in (("assembly.json", assembly), ("recipe.json", recipe)):
        (a.output / name).write_text(json.dumps(value, indent=2) + "\n")
    print(json.dumps({"status": "UNSIGNED_AUTHOR_INPUTS_ONLY", "assembly": str(a.output / "assembly.json"), "recipe": str(a.output / "recipe.json"), "activation_authorized": False}))


if __name__ == "__main__": main()
