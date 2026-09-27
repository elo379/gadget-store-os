from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_core_api_domains_are_registered():
    router = ROOT / "backend" / "app" / "api" / "router.py"
    assert router.exists()

    source = router.read_text()

    required = [
        "products",
        "inventory",
        "devices",
        "sales",
        "purchasing",
        "suppliers",
        "finance",
        "customers",
        "staff",
        "reports",
    ]

    for name in required:
        assert name in source


def test_auth_dependency_exists():
    auth_dir = ROOT / "backend" / "app" / "auth"
    assert auth_dir.exists()

    sources = list(auth_dir.glob("*.py"))
    assert sources

    combined = "\n".join(path.read_text() for path in sources)
    assert "get_current_user" in combined


def test_customer_api_exists():
    api_dir = ROOT / "backend" / "app" / "api"
    customer_files = list(api_dir.glob("*customer*.py"))

    assert customer_files

    source = "\n".join(path.read_text() for path in customer_files)

    assert "@router." in source
    assert "customer" in source.lower()
