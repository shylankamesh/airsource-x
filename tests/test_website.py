from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
WEBSITE = ROOT / "website"


def test_site_reports_resolve_from_standalone_and_pages_roots():
    html = (WEBSITE / "index.html").read_text(encoding="utf-8")
    report_links = re.findall(r'href="([^"]+EXPERIMENT_RESULTS\.md)"', html)

    assert report_links == [
        "results/delhi_ito_2024_25/EXPERIMENT_RESULTS.md",
        "results/delhi_ito_2024_25/EXPERIMENT_RESULTS.md",
    ]
    for link in report_links:
        assert not link.startswith("../")
        assert (WEBSITE / link).is_file()


def test_local_site_assets_are_present():
    html = (WEBSITE / "index.html").read_text(encoding="utf-8")
    assert 'href="styles.css"' in html
    assert 'href="favicon.svg"' in html
    assert 'src="app.js"' in html
    for asset in ("styles.css", "favicon.svg", "app.js"):
        assert (WEBSITE / asset).is_file()


def test_pages_workflow_publishes_the_linked_results():
    workflow = (ROOT / ".github" / "workflows" / "deploy-pages.yml").read_text(encoding="utf-8")
    assert "cp -R website/. _site/" in workflow
    assert "cp results/delhi_ito_2024_25/EXPERIMENT_RESULTS.md _site/results/delhi_ito_2024_25/" in workflow
    assert "cp results/delhi_ito_2024_25/forecast_metrics.csv _site/results/delhi_ito_2024_25/" in workflow
