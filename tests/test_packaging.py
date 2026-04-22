import tomllib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_declares_explicit_build_backend():
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())

    build_system = pyproject.get("build-system")
    assert build_system is not None
    assert build_system["build-backend"] == "hatchling.build"
    assert any(requirement.startswith("hatchling") for requirement in build_system["requires"])


def test_pyproject_declares_src_package_layout():
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())

    wheel_packages = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"]
    assert wheel_packages == ["src/open_notebook"]
