from pathlib import Path

EXPECTED_AUTH_FILES = {
    Path("login.html"),
    Path("signup.html"),
    Path("forgot.html"),
    Path("update-password.html"),
    Path("Javascript/login.js"),
    Path("Javascript/signup.js"),
    Path("Javascript/forgot_password.js"),
    Path("CSS/login.css"),
    Path("CSS/signup.css"),
    Path("CSS/forgot_password.css"),
}

IGNORE_DIRS = {"backend", "tests", "dist", "docs", "scripts", "Assets", "node_modules", "public"}
ALLOWED_EXTS = {".html", ".js", ".css"}
AUTH_KEYWORDS = ["login", "signup", "forgot", "reset", "update-password"]


def test_no_extra_auth_flow_files():
    repo_root = Path(__file__).resolve().parents[1]
    unexpected = set()
    for path in repo_root.rglob("*"):
        if path.is_file() and path.suffix in ALLOWED_EXTS:
            rel = path.relative_to(repo_root)
            if any(part in IGNORE_DIRS for part in rel.parts[:-1]):
                continue
            name = path.name.lower()
            if any(k in name for k in AUTH_KEYWORDS):
                if rel not in EXPECTED_AUTH_FILES:
                    unexpected.add(rel)
    assert not unexpected, f"Unexpected auth flow files: {sorted(str(p) for p in unexpected)}"
