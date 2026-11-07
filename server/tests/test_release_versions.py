"""Server, plugin and Claude Code plugin ship as one version.

The server compares its own version to the plugin's to decide whether to warn
about skew, so a release that bumps one file and not the others reports skew
between two halves of the same release.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _match(path: str, pattern: str) -> str:
    return re.search(pattern, (ROOT / path).read_text(), re.M).group(1)


def release_versions():
    cc_plugin = json.loads((ROOT / "cc-plugin/.claude-plugin/plugin.json").read_text())
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    return {
        "server/pyproject.toml": _match(
            "server/pyproject.toml", r'^version\s*=\s*"([^"]+)"'
        ),
        "plugin/manifest.yml": _match("plugin/manifest.yml", r"^version:\s*(\S+)"),
        "plugin/rhinomcp.csproj": _match(
            "plugin/rhinomcp.csproj", r"<Version>([^<]+)</Version>"
        ),
        "cc-plugin/.claude-plugin/plugin.json": cc_plugin["version"],
        ".claude-plugin/marketplace.json": marketplace["plugins"][0]["version"],
    }


def test_every_release_file_names_the_same_version():
    assert set(release_versions().values()) == {"0.5.0"}, release_versions()


def test_the_changelog_opens_with_the_release_version():
    changelog = (ROOT / "CHANGELOG.md").read_text()
    assert re.search(r"^## (\S+)", changelog, re.M).group(1) == "0.5.0"
