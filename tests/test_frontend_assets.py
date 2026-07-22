import os

def test_static_files_exist():
    assert os.path.exists("src/static/index.html")
    assert os.path.exists("src/static/styles.css")
    assert os.path.exists("src/static/app.js")

def test_css_design_tokens():
    with open("src/static/styles.css", "r", encoding="utf-8") as f:
        content = f.read()
    assert "#FBF8F3" in content
    assert "#020002" in content
    assert "--radius-pill" in content
