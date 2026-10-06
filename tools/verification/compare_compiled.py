#!/usr/bin/env python3
"""Compare supplied compiled-probe outputs; this module does not itself compile."""
import hashlib
import json

BASELINE_SHA256 = "e2016d2af1bdb63cdef079738ffba5ebaf47a66f78ae0391b8ed02e85a0334f5"
ROLES = {
    "platform": ("rx-application", {"P.workflow-resolver", "P.workflow-materializer", "P.process-source-validator"}),
    "device": ("rx-device-package", {"host.MELSEC", "host.JTC", "host.DYNAMIXEL", "driver.MELSEC", "driver.JTC", "driver.python-sdk", "driver.python-library", "driver.python-execution", "driver.external-process", "S.device-package-validator.unix"}),
    "process": ("rx-process-package", {"S.process-package-validator"}),
}
NONUNIX = "S.device-package-validator.nonunix"
# Frozen S SDK manifests; calculation/source provenance is PUBLIC_WIRE_INPUTS.json.
PUBLIC_PROTOCOLS = {
    "base/v1": "d32519ffd33cc02f5e6f82406ad2fe253421527dc047b807c11beb11a8f7583c",
    "cell/v1": "5e75ab4d3d72d4b22082003dbec5e2ca54562cc4302d2e306b07ce64d215d71b",
}


class Refusal(RuntimeError):
    pass


def require(condition, reason):
    if not condition:
        raise Refusal(reason)


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(Refusal("nonfinite JSON")))


def load_baseline(raw):
    require(hashlib.sha256(raw).hexdigest() == BASELINE_SHA256, "frozen static baseline hash differs")
    baseline = strict_json(raw)
    require(baseline.get("schema") == "rx.migration-named-source-identities.v1", "baseline schema")
    return baseline


def compare_outputs(baseline, outputs):
    """A MATCH means only that supplied values agree. The runner owns execution evidence."""
    require(set(outputs) == set(ROLES), "missing/extra probe role")
    expected = baseline["baseline"]["named_identities"]
    observed = {}; targets = []
    for role, output in outputs.items():
        require(isinstance(output, dict), "probe output must be an object")
        require(output.get("schema") == "rx.compiled-source-identities.v1" and output.get("role") == role, "probe schema/role differs")
        target = output.get("target", {})
        require(isinstance(target,dict), "target metadata must be an object")
        require(target.get("cfg_unix") is True and target.get("os") == "linux", "Unix Linux target required")
        require(target.get("arch") in ("x86_64", "aarch64"), "unsupported probe target architecture")
        targets.append(target)
        package, names = ROLES[role]
        require(output.get("package") == {"name": package, "version": "0.1.0"}, "probe package identity/version differs")
        values = output.get("values")
        require(isinstance(values, dict) and set(values) == names, "missing/extra named identity in " + role)
        for name, actual in values.items():
            require(name in expected and expected[name]["calculation_status"] == "CALCULATED_SOURCE_ONLY", "static named identity unavailable")
            require(actual == expected[name]["value"], "compiled value differs: " + name)
            require(name not in observed, "duplicate identity across roles")
            observed[name] = actual
    require(all(target == targets[0] for target in targets), "probe architectures/targets differ")
    require(outputs["platform"].get("fixture_outcomes") == {"resolver": "BLOCKED", "source_validator": "DOCUMENT_SHAPE"}, "identity-only refusal fixtures differ")
    require(outputs["device"].get("unobserved") == {NONUNIX: "NOT_COMPILED_FOR_THIS_TARGET"}, "non-Unix identity must remain unobserved")
    expected_binding=baseline['baseline']['bindings']['executor-execution/v2']
    require(expected_binding['consumed_wire_identity_status']=='CALCULATED_SOURCE_ONLY', 'Executor-v2 static binding unavailable')
    require(outputs['platform'].get('bindings')=={'executor-execution/v2':expected_binding['consumed_wire_digest']},'compiled Executor-v2 binding differs')
    require(not outputs['device'].get('bindings') and not outputs['process'].get('bindings'),'unexpected binding claims')
    require(outputs['device'].get('public_protocol_manifests')==PUBLIC_PROTOCOLS,'compiled base/cell public protocol manifest hash differs')
    require(len(observed) == 14 and set(expected) - set(observed) == {NONUNIX}, "coverage differs from declared Unix profile")
    return {"status": "MATCH_FROM_PROVIDED_PROBE_OUTPUTS", "target": targets[0],
            "observed_applicable_names": sorted(observed), "observed_count": 14,
            "static_baseline_names": 15, "not_compiled_for_this_target": [NONUNIX],
            "compiled_public_binding_functions": ["executor-execution/v2"],
            "compiled_public_protocol_manifests": sorted(PUBLIC_PROTOCOLS),
            "unobserved_binding_families": sorted(set(baseline['baseline']['bindings'])-{'executor-execution/v2'}),
            "binding_transport_negotiation": "NOT_EXERCISED_BY_PURE_FUNCTION_PROBE",
            "shipping_daemon_artifact_identity": "NOT_ESTABLISHED_BY_LIBRARY_EXAMPLE",
            "physical_acceptance": "NOT_PERFORMED"}
