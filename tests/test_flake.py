"""Тесты Nix-модели DL (flake.py)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from dl.errors import ParseError
from dl.flake import Output, build, build_to_files


class TestOutput:
    """Тесты класса Output."""

    def test_output_json(self):
        """Output с форматом json."""
        value = {"key": "value", "number": 42}
        output = Output("json", value)
        assert output.format == "json"
        assert output.value == value
        parsed = json.loads(output.serialized)
        assert parsed == value

    def test_output_toml(self):
        """Output с форматом toml."""
        value = {"key": "value", "number": 42}
        output = Output("toml", value)
        assert output.format == "toml"
        assert output.value == value
        assert 'key = "value"' in output.serialized
        assert "number = 42" in output.serialized

    def test_output_yaml(self):
        """Output с форматом yaml."""
        value = {"key": "value", "number": 42}
        output = Output("yaml", value)
        assert output.format == "yaml"
        assert output.value == value
        assert "key: value" in output.serialized
        assert "number: 42" in output.serialized

    def test_output_repr(self):
        """repr Output."""
        value = {"key": "value"}
        output = Output("json", value)
        repr_str = repr(output)
        assert "Output" in repr_str
        assert "json" in repr_str


class TestBuild:
    """Тесты функции build()."""

    def test_build_flake_simple(self, tmp_path: Path):
        """Простая сборка flake с одним output."""
        # Создаём flake.dl с новым синтаксисом: param_block => block
        config_dl = tmp_path / "flake.dl"
        config_dl.write_text("""
( $, $config ) => {
    outputs: {
        "opencode.json": {
            format: "json";
            value: {
                name: "test";
                version: 1;
            };
        };
    };
}
""")

        outputs = build(config_dl)
        assert len(outputs) == 1
        assert "opencode.json" in outputs
        output = outputs["opencode.json"]
        assert output.format == "json"
        assert output.value == {"name": "test", "version": 1}
        parsed = json.loads(output.serialized)
        assert parsed == {"name": "test", "version": 1}

    def test_build_flake_with_import(self, tmp_path: Path):
        """Сборка flake с импортом модуля."""
        # Модуль
        module_dl = tmp_path / "module.dl"
        module_dl.write_text("""
( $, $config ) => {
    data: {
        from_module: true;
    };
}
""")

        # Flake с импортом и сигнатурой
        config_dl = tmp_path / "flake.dl"
        config_dl.write_text(f"""
( $, $config ) => {{
    import ./module.dl;
    
    outputs: {{
        "result.json": {{
            format: "json";
            value: $config;
        }};
    }};
}}
""")

        outputs = build(config_dl)
        assert len(outputs) == 1
        result = outputs["result.json"]
        assert result.value["data"]["from_module"] is True

    def test_build_flake_imports_block(self, tmp_path: Path):
        """Сборка flake с imports блоком."""
        # Модуль
        module_dl = tmp_path / "module.dl"
        module_dl.write_text("""
( $, $config ) => {
    from_module: true;
}
""")

        # Flake с imports блоком и сигнатурой
        config_dl = tmp_path / "flake.dl"
        config_dl.write_text(f"""
( $, $config ) => {{
    imports [
        import ./module.dl;
    ];
    
    outputs: {{
        "result.json": {{
            format: "json";
            value: $config;
        }};
    }};
}}
""")

        outputs = build(config_dl)
        assert len(outputs) == 1
        result = outputs["result.json"]
        assert result.value["from_module"] is True

    def test_build_simple(self, tmp_path: Path):
        """Простая сборка со старым синтаксисом configuration.dl."""
        # Создаём configuration.dl со старым синтаксисом
        config_dl = tmp_path / "configuration.dl"
        config_dl.write_text("""
json( $ ) => {
    outputs: {
        "opencode.json": {
            format: "json";
            value: {
                name: "test";
                version: 1;
            };
        };
    };
}
""")

        outputs = build(config_dl)
        assert len(outputs) == 1
        assert "opencode.json" in outputs
        output = outputs["opencode.json"]
        assert output.format == "json"
        assert output.value == {"name": "test", "version": 1}
        parsed = json.loads(output.serialized)
        assert parsed == {"name": "test", "version": 1}

    def test_build_multiple_outputs(self, tmp_path: Path):
        """Сборка с несколькими outputs."""
        config_dl = tmp_path / "configuration.dl"
        config_dl.write_text("""
json( $ ) => {
    outputs: {
        "config.json": {
            format: "json";
            value: {
                app: "myapp";
            };
        };
        "settings.toml": {
            format: "toml";
            value: {
                debug: true;
            };
        };
    };
}
""")

        outputs = build(config_dl)
        assert len(outputs) == 2
        assert "config.json" in outputs
        assert "settings.toml" in outputs

        json_out = outputs["config.json"]
        assert json_out.format == "json"
        assert json_out.value == {"app": "myapp"}

        toml_out = outputs["settings.toml"]
        assert toml_out.format == "toml"
        assert toml_out.value == {"debug": True}

    def test_build_with_modules(self, tmp_path: Path):
        """Сборка с импортируемыми модулями."""
        # Модуль
        module_dl = tmp_path / "module.dl"
        module_dl.write_text("""
( $ ) => {
    data: {
        from_module: true;
    };
}
""")

        # Конфигурация (объявляем $config в сигнатуре)
        config_dl = tmp_path / "configuration.dl"
        config_dl.write_text(f"""
json( $, $config ) => {{
    let mod = import ./module.dl;
    ...mod();
    outputs: {{
        "result.json": {{
            format: "json";
            value: $config;
        }};
    }};
}}
""")

        outputs = build(config_dl)
        assert len(outputs) == 1
        result = outputs["result.json"]
        assert result.value["data"]["from_module"] is True

    def test_build_two_pass(self, tmp_path: Path):
        """Двухфазное вычисление: модуль добавляет данные, корневой использует $config."""
        # Модуль просто добавляет данные (не читает $config)
        module_dl = tmp_path / "module.dl"
        module_dl.write_text("""
( $, $config ) => {
    derived: {
        from_module: true;
    };
}
""")

        # Конфигурация: сначала initial, потом модуль, потом используем $config в outputs
        config_dl = tmp_path / "configuration.dl"
        config_dl.write_text(f"""
json( $, $config ) => {{
    let mod = import ./module.dl;
    initial: "value";
    ...mod();
    outputs: {{
        "result.json": {{
            format: "json";
            value: $config;
        }};
    }};
}}
""")

        outputs = build(config_dl)
        assert len(outputs) == 1
        result = outputs["result.json"]
        # $config должен включать и initial, и derived из модуля
        assert result.value["initial"] == "value"
        assert result.value["derived"]["from_module"] is True

    def test_build_missing_format(self, tmp_path: Path):
        """Ошибка: output без format."""
        config_dl = tmp_path / "configuration.dl"
        config_dl.write_text("""
json( $ ) => {
    outputs: {
        "file.json": {
            value: { test: 1 };
        };
    };
}
""")

        with pytest.raises(ParseError) as exc_info:
            build(config_dl)
        assert "missing 'format'" in str(exc_info.value)

    def test_build_missing_value(self, tmp_path: Path):
        """Ошибка: output без value."""
        config_dl = tmp_path / "configuration.dl"
        config_dl.write_text("""
json( $ ) => {
    outputs: {
        "file.json": {
            format: "json";
        };
    };
}
""")

        with pytest.raises(ParseError) as exc_info:
            build(config_dl)
        assert "missing 'value'" in str(exc_info.value)

    def test_build_file_not_found(self, tmp_path: Path):
        """Ошибка: файл не найден."""
        nonexistent = tmp_path / "nonexistent.dl"
        with pytest.raises(ParseError) as exc_info:
            build(nonexistent)
        assert "file not found" in str(exc_info.value)


class TestBuildToFiles:
    """Тесты функции build_to_files()."""

    def test_build_to_files_simple(self, tmp_path: Path):
        """Запись одного output в файл."""
        config_dl = tmp_path / "configuration.dl"
        config_dl.write_text("""
json( $ ) => {
    outputs: {
        "opencode.json": {
            format: "json";
            value: {
                name: "test";
            };
        };
    };
}
""")

        written = build_to_files(config_dl, tmp_path)
        assert len(written) == 1
        output_file = tmp_path / "opencode.json"
        assert output_file.exists()
        content = json.loads(output_file.read_text())
        assert content == {"name": "test"}

    def test_build_to_files_nested(self, tmp_path: Path):
        """Запись output в подкаталог."""
        config_dl = tmp_path / "configuration.dl"
        config_dl.write_text("""
json( $ ) => {
    outputs: {
        "subdir/config.json": {
            format: "json";
            value: {
                nested: true;
            };
        };
    };
}
""")

        written = build_to_files(config_dl, tmp_path)
        assert len(written) == 1
        output_file = tmp_path / "subdir" / "config.json"
        assert output_file.exists()
        content = json.loads(output_file.read_text())
        assert content == {"nested": True}

    def test_build_to_files_multiple(self, tmp_path: Path):
        """Запись нескольких outputs."""
        config_dl = tmp_path / "configuration.dl"
        config_dl.write_text("""
json( $ ) => {
    outputs: {
        "a.json": {
            format: "json";
            value: { a: 1 };
        };
        "b.json": {
            format: "json";
            value: { b: 2 };
        };
    };
}
""")

        written = build_to_files(config_dl, tmp_path)
        assert len(written) == 2
        assert (tmp_path / "a.json").exists()
        assert (tmp_path / "b.json").exists()
