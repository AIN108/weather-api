"""requirements.txt가 스크립트들이 import하는 외부 패키지를 모두 담는지 검사한다."""
import ast
import re

from conftest import ROOT

# import 이름 → 배포 패키지 이름
DIST = {"requests": "requests", "schedule": "schedule", "xmltodict": "xmltodict",
        "bs4": "beautifulsoup4", "RPi": "RPi.GPIO"}
SCRIPTS = ["itscseoul.py", "seoulfinal.py", "seoul.py"]


def third_party_imports(path):
    names = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names & DIST.keys()


def requirement_names():
    text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    return {re.split(r"[<>=;!~ ]", line.strip(), maxsplit=1)[0]
            for line in text.splitlines() if line.strip() and not line.startswith("#")}


def test_requirements_cover_script_imports():
    required = requirement_names()
    for script in SCRIPTS:
        for module in third_party_imports(ROOT / script):
            assert DIST[module] in required, f"{script}: {DIST[module]} 누락"
    assert "lxml" in required  # seoul.py가 BeautifulSoup(..., "lxml") 파서를 쓴다


def test_rpi_gpio_only_on_raspberry_pi():
    line = next(l for l in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
                if l.startswith("RPi.GPIO"))
    assert "platform_machine" in line  # x86 PC·CI에서는 설치하지 않는다


def test_readme_uses_requirements_file():
    assert "pip install -r requirements.txt" in (ROOT / "README.md").read_text(encoding="utf-8")
