from pathlib import Path
import re


def test_every_sidebar_workspace_has_a_page_handler():
    app=(Path(__file__).resolve().parents[1]/"app.py").read_text(encoding="utf-8")
    nav=re.search(r'page = st\.radio\("WORKSPACE", \[(.*?)\]',app,re.S)
    assert nav
    labels=re.findall(r'"([^"]+)"',nav.group(1))
    handlers=set(re.findall(r'(?:if|elif) page == "([^"]+)"',app))
    assert set(labels)==handlers
