from aws_lambda_powertools.shared.lazy_import import LazyLoader


def test_lazy_loader_dir():
    lazy_loader = LazyLoader("enum", globals(), "enum")

    module_dir = lazy_loader.__dir__()
    assert isinstance(module_dir, list)
    assert "Enum" in module_dir
