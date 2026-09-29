from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path

import pytest
import yaml

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Release workflows execute on Ubuntu.")

ROOT = Path(__file__).resolve().parents[2]
VERSION_FILE = "aws_lambda_powertools/shared/version.py"
RELEASE_FILES = ("pyproject.toml", "uv.lock", VERSION_FILE)
WORKFLOWS = {
    kind: yaml.safe_load((ROOT / ".github/workflows" / name).read_text())
    for kind, name in (("release", "release-v3.yml"), ("pre-release", "pre-release.yml"))
}


@pytest.fixture
def release_tree(tmp_path):
    root = tmp_path / "source"
    for name in RELEASE_FILES:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    return root


def snapshot(root):
    return {name: (root / name).read_text() for name in RELEASE_FILES}


def run_bump(root, kind, version):
    output = root / "github-output"
    output.write_text("")
    env = {**os.environ, "GITHUB_OUTPUT": str(output)}
    env["RELEASE_TAG_VERSION" if kind == "release" else "RELEASE_VERSION"] = version
    for step in WORKFLOWS[kind]["jobs"]["seal"]["steps"]:
        if step.get("id") not in ("release_version", "versioning"):
            continue
        result = subprocess.run(
            ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", step["run"]],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            return result
        if output.read_text():
            env["RELEASE_VERSION"] = output.read_text().strip().split("=", 1)[1]
    return result


def assert_release_versions(root, version, before):
    after = snapshot(root)
    project_before = tomllib.loads(before["pyproject.toml"])
    project_after = tomllib.loads(after["pyproject.toml"])
    assert project_after["project"].pop("version") == version
    project_before["project"].pop("version")
    assert project_after == project_before

    assignments = ast.parse(after[VERSION_FILE]).body
    assert (
        next(
            ast.literal_eval(node.value)
            for node in assignments
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "VERSION" for target in node.targets)
        )
        == version
    )

    lock_before = tomllib.loads(before["uv.lock"])
    lock_after = tomllib.loads(after["uv.lock"])
    package_before = next(p for p in lock_before["package"] if p["name"] == "aws-lambda-powertools")
    package_after = next(p for p in lock_after["package"] if p["name"] == "aws-lambda-powertools")
    assert package_after["version"] == version
    old_version = package_before["version"]
    assert after["uv.lock"] == before["uv.lock"].replace(
        f'name = "aws-lambda-powertools"\nversion = "{old_version}"',
        f'name = "aws-lambda-powertools"\nversion = "{version}"',
    )
    subprocess.run(
        ["uv", "lock", "--check", "--offline"],
        cwd=root,
        env={**os.environ, "UV_CACHE_DIR": str(root / "empty-cache")},
        check=True,
        capture_output=True,
    )
    assert (root / "github-output").read_text() == f"RELEASE_VERSION={version}\n"


@pytest.mark.parametrize(
    ("kind", "version"),
    [
        ("release", "v3.36.0"),
        ("release", "3.36.0"),
        ("release", "v4.0.0"),
        ("release", "v3.36.99"),
        ("release", "v3.36.0a0"),
        ("release", "v3.36.0b1"),
        ("release", "v3.36.0rc1"),
        ("pre-release", "3.36.0a0"),
        ("pre-release", "3.36.0a9"),
        ("pre-release", "3.36.0b0"),
        ("pre-release", "3.36.0rc1"),
    ],
)
def test_release_bump_changes_only_package_versions(release_tree, kind, version):
    before = snapshot(release_tree)

    result = run_bump(release_tree, kind, version)

    assert result.returncode == 0, result.stderr
    assert_release_versions(release_tree, version.removeprefix("v"), before)
    after = snapshot(release_tree)
    assert run_bump(release_tree, kind, version).returncode == 0
    assert snapshot(release_tree) == after


@pytest.mark.parametrize("kind", WORKFLOWS)
@pytest.mark.parametrize(
    "version",
    [
        "",
        "3.36",
        "vv3.36.0",
        "V3.36.0",
        " 3.36.0",
        "3.36.0 ",
        "3.36.0a",
        "03.36.0a0",
        "3.036.0a0",
        "3.36.00a0",
        "3.36.0a01",
        "3.36.0rc01",
        "3.36.0\nFORGED=1",
        '3.36.0"; touch unexpected; #',
        "$(touch unexpected)",
        "`touch unexpected`",
        "3.36.0/../../",
        "--help",
    ],
)
def test_invalid_version_fails_without_editing_files(release_tree, kind, version):
    before = snapshot(release_tree)

    result = run_bump(release_tree, kind, version)

    assert result.returncode != 0
    assert snapshot(release_tree) == before
    assert not (release_tree / "unexpected").exists()
    assert not (release_tree / "github-output").read_text()


@pytest.mark.parametrize("version", ["3.36.0", "v3.36.0a0"])
def test_pre_release_rejects_stable_versions_and_tag_prefix(release_tree, version):
    before = snapshot(release_tree)

    assert run_bump(release_tree, "pre-release", version).returncode != 0
    assert snapshot(release_tree) == before


@pytest.mark.parametrize("kind", WORKFLOWS)
@pytest.mark.parametrize(
    ("file", "old", "new"),
    [
        ("pyproject.toml", 'version = "', "version = '"),
        ("pyproject.toml", 'version = "', 'version  = "'),
        (VERSION_FILE, 'VERSION = "', "VERSION = '"),
        (VERSION_FILE, "VERSION =", "PACKAGE_VERSION ="),
        ("uv.lock", 'name = "aws-lambda-powertools"\n', 'name = "aws-lambda-powertools"\n# comment\n'),
    ],
)
def test_unmatched_version_field_stops_before_sealing(release_tree, kind, file, old, new):
    path = release_tree / file
    text = path.read_text()
    if new.endswith("'"):
        # Valid TOML/Python with single quotes must not silently retain the old version.
        line = next(line for line in text.splitlines() if line.startswith(old))
        text = text.replace(line, line.replace('"', "'"), 1)
    else:
        text = text.replace(old, new, 1)
    path.write_text(text)

    result = run_bump(release_tree, kind, "3.36.0a0")

    assert result.returncode != 0


@pytest.mark.parametrize("kind", WORKFLOWS)
def test_unrelated_tool_version_is_preserved(release_tree, kind):
    project = release_tree / "pyproject.toml"
    project.write_text(project.read_text() + '\n[tool.release_probe]\nversion = "9.8.7"\n')
    before = snapshot(release_tree)

    result = run_bump(release_tree, kind, "3.36.0a0")

    assert result.returncode == 0, result.stderr
    assert_release_versions(release_tree, "3.36.0a0", before)


def test_prerelease_progression_and_promotion_to_stable(release_tree):
    for version in ("3.36.0a0", "3.36.0a1", "3.36.0b0", "3.36.0rc1", "3.36.0"):
        before = snapshot(release_tree)
        kind = "release" if version == "3.36.0" else "pre-release"
        result = run_bump(release_tree, kind, version)
        assert result.returncode == 0, result.stderr
        assert_release_versions(release_tree, version, before)


@pytest.mark.parametrize(
    ("version", "tamper"),
    [("3.36.0", False), ("3.36.0a0", False), ("3.36.0b1", False), ("3.36.0rc1", False), ("3.36.0", True)],
)
def test_sealed_source_builds_matching_sdist_and_wheel(release_tree, tmp_path, version, tamper):
    for name in ("README.md", "LICENSE", "THIRD-PARTY-LICENSES"):
        shutil.copyfile(ROOT / name, release_tree / name)
    shutil.copytree(
        ROOT / "aws_lambda_powertools",
        release_tree / "aws_lambda_powertools",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    before = snapshot(release_tree)
    kind = "release" if version == "3.36.0" else "pre-release"
    assert run_bump(release_tree, kind, version).returncode == 0
    assert_release_versions(release_tree, version, before)

    # Run the actual local action commands; artifacts stay in this temporary directory.
    actions = {
        name: yaml.safe_load((ROOT / f".github/actions/{name}/action.yml").read_text())["runs"]["steps"]
        for name in ("seal", "seal-restore")
    }
    output = tmp_path / "seal-output"
    env = {**os.environ, "ARTIFACT_NAME": str(tmp_path / "sealed"), "GITHUB_OUTPUT": str(output)}
    for step in actions["seal"]:
        if step.get("id") in ("compress_all", "integrity_hash"):
            subprocess.run(
                ["bash", "-eo", "pipefail", "-c", step["run"]],
                cwd=release_tree,
                env=env,
                check=True,
                capture_output=True,
            )
    env["PROVIDED_HASH"] = output.read_text().strip().split("=", 1)[1]
    if tamper:
        with (tmp_path / "sealed.tar").open("ab") as archive:
            archive.write(b"tampered")
    restored = tmp_path / "restored"
    restored.mkdir()
    output.write_text("")
    for step in actions["seal-restore"]:
        if step.get("id") not in ("integrity_hash", "verify_hash", "overwrite"):
            continue
        result = subprocess.run(
            ["bash", "-eo", "pipefail", "-c", step["run"]],
            cwd=restored,
            env=env,
            check=False,
            capture_output=True,
        )
        if tamper and step.get("id") == "verify_hash":
            assert result.returncode != 0
            assert not list(restored.iterdir())
            return
        assert result.returncode == 0, result.stderr
        if step.get("id") == "integrity_hash":
            env["CURRENT_HASH"] = output.read_text().strip().split("=", 1)[1]
    assert snapshot(restored) == snapshot(release_tree)
    build_step = next(
        step
        for step in WORKFLOWS[kind]["jobs"]["build"]["steps"]
        if step.get("name") == "Build python package and wheel"
    )
    subprocess.run(["bash", "-eo", "pipefail", "-c", build_step["run"]], cwd=restored, check=True, capture_output=True)

    wheel = next((restored / "dist").glob("*.whl"))
    with zipfile.ZipFile(wheel) as package:
        metadata_path = next(name for name in package.namelist() if name.endswith(".dist-info/METADATA"))
        assert BytesParser().parsebytes(package.read(metadata_path))["Version"] == version
        assert f'VERSION = "{version}"' in package.read(VERSION_FILE).decode()
        assert "aws_lambda_powertools/py.typed" in package.namelist()
    with tarfile.open(next((restored / "dist").glob("*.tar.gz"))) as package:
        metadata_path = next(name for name in package.getnames() if name.endswith("/PKG-INFO"))
        assert BytesParser().parsebytes(package.extractfile(metadata_path).read())["Version"] == version


def test_release_tag_and_version_pr_include_the_lockfile():
    tag_step = next(
        step for step in WORKFLOWS["release"]["jobs"]["create_tag"]["steps"] if step.get("name") == "Create Git Tag"
    )
    staged_files = next(line for line in tag_step["run"].splitlines() if line.startswith("git add ")).split()[2:]
    assert set(RELEASE_FILES) <= set(staged_files)
    for workflow in WORKFLOWS.values():
        pr_step = next(step for step in workflow["jobs"]["bump_version"]["steps"] if step.get("id") == "create-pr")
        assert set(RELEASE_FILES) <= set(pr_step["with"]["files"].split())


def test_release_tag_contains_all_updated_versions(release_tree, tmp_path):
    # The workflow can push only to this local bare repository.
    remote = tmp_path / "remote.git"
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Release test",
        "GIT_AUTHOR_EMAIL": "release@example.invalid",
        "GIT_COMMITTER_NAME": "Release test",
        "GIT_COMMITTER_EMAIL": "release@example.invalid",
    }
    for command in (
        ["git", "init", "--bare", str(remote)],
        ["git", "init"],
        ["git", "remote", "add", "origin", str(remote)],
        ["git", "add", *RELEASE_FILES],
        ["git", "-c", "core.hooksPath=/dev/null", "commit", "-m", "Before release"],
    ):
        subprocess.run(command, cwd=release_tree, env=env, check=True, capture_output=True)
    before = snapshot(release_tree)
    current = tomllib.loads(before["pyproject.toml"])["project"]["version"]
    version = f"{int(current.split('.')[0]) + 1}.0.0"
    assert run_bump(release_tree, "release", f"v{version}").returncode == 0
    tag_step = next(
        step for step in WORKFLOWS["release"]["jobs"]["create_tag"]["steps"] if step.get("name") == "Create Git Tag"
    )
    subprocess.run(
        ["bash", "-eo", "pipefail", "-c", tag_step["run"]],
        cwd=release_tree,
        env={**env, "RELEASE_VERSION": version},
        check=True,
        capture_output=True,
    )
    for name in RELEASE_FILES:
        tagged = subprocess.check_output(["git", "--git-dir", str(remote), "show", f"v{version}:{name}"], text=True)
        assert tagged == (release_tree / name).read_text()
    assert_release_versions(release_tree, version, before)
