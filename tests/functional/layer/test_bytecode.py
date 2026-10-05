import calendar
import importlib.machinery
import os
import py_compile
import types
import zipfile

import pytest

from layer_v3.layer.canary.bytecode_monitor import track_layer_compilation, verify_layer_bytecode


def load_module(source):
    loader = importlib.machinery.SourceFileLoader("canary_bytecode_test", str(source))
    module = types.ModuleType(loader.name)
    exec(loader.get_code(loader.name), module.__dict__)
    return module


@pytest.mark.parametrize("archive_roundtrip", [False, True])
@pytest.mark.parametrize("mode", ["source", "timestamp", "checked_hash"])
def test_layer_bytecode_after_packaging(tmp_path, mode, archive_roundtrip):
    layer = tmp_path / "build"
    layer.mkdir()
    source = layer / "sample.py"
    source.write_text("value = 42\n")
    # ZIP timestamps cannot represent this odd second.
    os.utime(source, (1_700_000_001, 1_700_000_001))
    if mode != "source":
        invalidation = {
            "timestamp": py_compile.PycInvalidationMode.TIMESTAMP,
            "checked_hash": py_compile.PycInvalidationMode.CHECKED_HASH,
        }[mode]
        py_compile.compile(str(source), doraise=True, invalidation_mode=invalidation)

    if archive_roundtrip:
        archive_path = tmp_path / "layer.zip"
        with zipfile.ZipFile(archive_path, "w") as archive:
            for path in layer.rglob("*"):
                if path.is_file():
                    archive.write(path, path.relative_to(layer))
        layer = tmp_path / "extracted"
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(layer)
            for info in archive.infolist():
                timestamp = calendar.timegm(info.date_time)
                os.utime(layer / info.filename, (timestamp, timestamp))
        source = layer / "sample.py"

    original_loader = importlib.machinery.SourceFileLoader.source_to_code
    with track_layer_compilation(str(layer)) as compiled:
        module = load_module(source)
    assert module.value == 42
    assert source.read_text() == "value = 42\n"
    assert importlib.machinery.SourceFileLoader.source_to_code is original_loader
    if mode == "source" or (mode == "timestamp" and archive_roundtrip):
        assert compiled == [str(source)]
        with pytest.raises(ValueError, match="Layer recompiled 1 source files"):
            verify_layer_bytecode(compiled)
    else:
        assert compiled == []
        verify_layer_bytecode(compiled)


def test_checked_hash_rejects_stale_code_with_same_size_and_timestamp(tmp_path):
    source = tmp_path / "sample.py"
    source.write_text("value = 1\n")
    timestamp = source.stat().st_mtime_ns
    py_compile.compile(str(source), doraise=True, invalidation_mode=py_compile.PycInvalidationMode.CHECKED_HASH)
    source.write_text("value = 2\n")
    os.utime(source, ns=(timestamp, timestamp))

    with track_layer_compilation(str(tmp_path)) as compiled:
        module = load_module(source)

    assert module.value == 2
    assert compiled == [str(source)]


def test_unrelated_imports_are_not_layer_compilations(tmp_path):
    layer = tmp_path / "layer"
    layer.mkdir()
    neighbor = tmp_path / "layer-other"
    neighbor.mkdir()
    source = neighbor / "sample.py"
    source.write_text("value = 42\n")

    with track_layer_compilation(str(layer)) as compiled:
        assert load_module(source).value == 42

    assert compiled == []


def test_loader_is_restored_after_failed_import(tmp_path):
    source = tmp_path / "invalid.py"
    source.write_text("def invalid(\n")
    original_loader = importlib.machinery.SourceFileLoader.source_to_code

    with pytest.raises(SyntaxError), track_layer_compilation(str(tmp_path)) as compiled:
        load_module(source)

    assert compiled == [str(source)]
    assert importlib.machinery.SourceFileLoader.source_to_code is original_loader
