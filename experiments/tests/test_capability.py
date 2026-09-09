import copy
import json

import pytest

from experiments import capability as cap, capability_mcp as gateway
from experiments.repair import inventory
from experiments.runner import sha256


def setup(tmp_path):
    sources = {
        "contracts/protocol.json": json.dumps(
            {"$defs": {"command": {"properties": {"type": {"enum": []}}}}}
        ),
        "contracts/test_schemas.py": "def test_protocol_envelope():\n    expected_commands = []\n",
        "server/src/rhinomcp/keep.py": "untouched = True\n",
    }
    for name, text in sources.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    before = inventory(tmp_path)
    creates = [
        "server/src/rhinomcp/tools/foo.py",
        "plugin/Functions/Foo.cs",
        "contracts/commands/foo.json",
        "server/tests/test_foo.py",
    ]
    writes = ["contracts/protocol.json", "contracts/test_schemas.py"]
    scope = {
        "id": "foo",
        "baseline_revision": "HEAD",
        "commands": {"foo": "Foo"},
        "read_paths": creates + writes,
        "create_paths": creates,
        "write_paths": writes,
        "instructions": "Add foo for the reviewed evidence.",
    }
    return scope, before


def fill(tmp_path, scope):
    sources = {
        "contracts/protocol.json": json.dumps(
            {"$defs": {"command": {"properties": {"type": {"enum": ["foo"]}}}}}
        ),
        "contracts/test_schemas.py": "def test_protocol_envelope():\n    expected_commands = ['foo']\n",
        "server/src/rhinomcp/tools/foo.py": '@mcp.tool()\ndef foo():\n    return send_command("foo", {})\n',
        "plugin/Functions/Foo.cs": '[McpCommand("foo")] public object Foo() => null;',
        "contracts/commands/foo.json": '{"type":"object","additionalProperties":false}',
        "server/tests/test_foo.py": "def test_foo():\n    assert True\n",
    }
    for name, text in sources.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def test_complete_command_and_exact_parent_directories(tmp_path):
    scope, before = setup(tmp_path)
    cap.validate_scope(scope, before)
    fill(tmp_path, scope)
    report = cap.check_candidate(tmp_path, before, scope)
    assert report["protocol_complete"] is True
    assert report["promotion_authorized"] is False


@pytest.mark.parametrize(
    "corruption",
    [
        "extra",
        "protected",
        "symlink",
        "mode",
        "missing",
        "schema",
        "envelope",
        "transport",
        "handler",
    ],
)
def test_incomplete_or_out_of_scope_candidate_rejected(tmp_path, corruption):
    scope, before = setup(tmp_path)
    fill(tmp_path, scope)
    if corruption == "extra":
        (tmp_path / "undeclared").write_text("bad")
    elif corruption == "protected":
        (tmp_path / "server/src/rhinomcp/keep.py").write_text("bad")
    elif corruption == "symlink":
        (tmp_path / "link").symlink_to("/tmp")
    elif corruption == "mode":
        (tmp_path / "contracts/protocol.json").chmod(0o755)
    elif corruption == "missing":
        (tmp_path / "plugin/Functions/Foo.cs").unlink()
    elif corruption == "schema":
        (tmp_path / "contracts/commands/foo.json").write_text('{"type":"object"}')
    elif corruption == "envelope":
        (tmp_path / "contracts/test_schemas.py").write_text(
            "def test_protocol_envelope():\n    expected_commands = []\n"
        )
    elif corruption == "transport":
        (tmp_path / "server/src/rhinomcp/tools/foo.py").write_text(
            '@mcp.tool()\ndef foo():\n    return send_command("wrong", {})\n'
        )
    else:
        (tmp_path / "plugin/Functions/Foo.cs").write_text('[McpCommand("wrong")]')
    with pytest.raises(ValueError):
        cap.check_candidate(tmp_path, before, scope)


def test_scope_cannot_omit_tier_or_grant_arbitrary_writes(tmp_path):
    scope, before = setup(tmp_path)
    bad = copy.deepcopy(scope)
    bad["create_paths"].pop()
    with pytest.raises(ValueError):
        cap.validate_scope(bad, before)
    bad = copy.deepcopy(scope)
    bad["write_paths"].append("server/src/rhinomcp/keep.py")
    bad["read_paths"].append("server/src/rhinomcp/keep.py")
    with pytest.raises(ValueError):
        cap.validate_scope(bad, before)


def test_gateway_create_no_overwrite_compare_write_and_manifest_pin(
    tmp_path, monkeypatch
):
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    scope, _ = setup(candidate)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({**scope, "candidate": str(candidate)}))
    monkeypatch.setenv("BUILDER_MANIFEST", str(manifest))
    monkeypatch.setenv("BUILDER_MANIFEST_SHA256", sha256(manifest))
    monkeypatch.setattr(gateway, "calls", 0)
    name = scope["create_paths"][0]
    result = gateway.create_source(name, "new")
    with pytest.raises(ValueError, match="exists"):
        gateway.create_source(name, "overwrite")
    with pytest.raises(ValueError, match="changed since"):
        gateway.replace_source(name, "incorrect", "bad")
    gateway.replace_source(name, result["sha256"], "revised")
    assert gateway.read_source(name)["content"] == "revised"
    with pytest.raises(ValueError, match="outside"):
        gateway.create_source("experiments/evaluator.py", "bad")
    manifest.write_text("{}")
    with pytest.raises(ValueError, match="manifest changed"):
        gateway.read_source(name)


def test_declared_candidate_enters_existing_trial_without_weakening_edit_gate(tmp_path):
    import subprocess
    from experiments.runner import save
    from experiments.trial import prepare, read

    source = tmp_path / "candidate"
    source.mkdir()
    scope, _ = setup(source)
    for args in [
        ["init", "-q"],
        ["add", "."],
        [
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-qm",
            "baseline",
        ],
    ]:
        subprocess.run(["git", *args], cwd=source, check=True, capture_output=True)
    before = inventory(source)
    save(tmp_path / "baseline_inventory.json", before)
    fill(source, scope)
    report = cap.check_candidate(source, before, scope)
    manifest = {**scope, "scope_version": 2, "candidate": str(source)}
    save(tmp_path / "manifest.json", manifest)
    (tmp_path / "candidate.patch").write_bytes(cap.review_patch(source, scope))
    save(
        tmp_path / "checkpoint.json",
        {
            **report,
            "stage": "candidate_ready_for_review",
            "manifest_sha256": sha256(tmp_path / "manifest.json"),
            "patch_sha256": sha256(tmp_path / "candidate.patch"),
        },
    )
    (tmp_path / "baseline.rhp").write_bytes(b"baseline")
    (tmp_path / "adapter.py").write_text("# test adapter, not executed")
    save(tmp_path / "suite.json", {"cases": ["preserve"]})
    trial = prepare(
        tmp_path,
        tmp_path / "baseline.rhp",
        "baseline",
        tmp_path / "suite.json",
        tmp_path / "adapter.py",
        tmp_path / "runtime.lock",
        "Reviewed test candidate",
    )
    assert (trial / "source/plugin/Functions/Foo.cs").exists()
    assert b"new file mode" in (trial / "reviewed.patch").read_bytes()
    assert read(trial / "state.json")["stage"] == "ready"
