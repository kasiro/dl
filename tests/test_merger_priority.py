"""Тесты приоритетов слияния в merger.py.

Проверка функций mkDefault/mkForce и обработки приоритетов в deep_merge().
"""

import pytest

from dl.errors import ConflictError
from dl.merger import deep_merge


def _mk_default(value):
    """Создать значение с приоритетом 1000 (mkDefault)."""
    return {"priority": 1000, "value": value}


def _mk_force(value):
    """Создать значение с приоритетом 0 (mkForce)."""
    return {"priority": 0, "value": value}


class TestPriorityBasic:
    """Базовые тесты приоритетов."""

    def test_mkforce_wins_over_mkdefault(self):
        """mkForce (priority=0) побеждает mkDefault (priority=1000)."""
        base = {"key": _mk_default("default_value")}
        override = {"key": _mk_force("force_value")}
        result = deep_merge(base, override)
        assert result["key"] == _mk_force("force_value")

    def test_mkdefault_vs_mkdefault_conflict(self):
        """mkDefault vs mkDefault — конфликт E003."""
        base = {"key": _mk_default("value1")}
        override = {"key": _mk_default("value2")}
        with pytest.raises(ConflictError, match="E003 ConflictError"):
            deep_merge(base, override)

    def test_mkforce_vs_mkforce_conflict(self):
        """mkForce vs mkForce — конфликт E003."""
        base = {"key": _mk_force("value1")}
        override = {"key": _mk_force("value2")}
        with pytest.raises(ConflictError, match="E003 ConflictError"):
            deep_merge(base, override)


class TestPriorityMixed:
    """Тесты смешанных приоритетов и обычных значений."""

    def test_priority_vs_normal(self):
        """Приоритетное значение vs обычное — обычное переопределяет."""
        base = {"key": _mk_default("default_value")}
        override = {"key": "normal_value"}
        result = deep_merge(base, override)
        assert result["key"] == "normal_value"

    def test_normal_vs_priority(self):
        """Обычное значение vs приоритетное — приоритетное переопределяет."""
        base = {"key": "normal_value"}
        override = {"key": _mk_force("force_value")}
        result = deep_merge(base, override)
        assert result["key"] == _mk_force("force_value")

    def test_normal_vs_normal(self):
        """Обычное vs обычное — переопределение (поздний wins)."""
        base = {"key": "base_value"}
        override = {"key": "override_value"}
        result = deep_merge(base, override)
        assert result["key"] == "override_value"


class TestPriorityNested:
    """Тесты вложенных приоритетов."""

    def test_nested_mkforce_wins(self):
        """Вложенный mkForce побеждает вложенный mkDefault."""
        base = {
            "nested": {
                "key": _mk_default("default_value"),
            }
        }
        override = {
            "nested": {
                "key": _mk_force("force_value"),
            }
        }
        result = deep_merge(base, override)
        assert result["nested"]["key"] == _mk_force("force_value")

    def test_nested_conflict_same_priority(self):
        """Вложенные одинаковые приоритеты — конфликт."""
        base = {
            "nested": {
                "key": _mk_default("value1"),
            }
        }
        override = {
            "nested": {
                "key": _mk_default("value2"),
            }
        }
        with pytest.raises(ConflictError, match="E003 ConflictError"):
            deep_merge(base, override)

    def test_deep_nesting_priority(self):
        """Глубокая вложенность с приоритетами."""
        base = {
            "level1": {
                "level2": {
                    "level3": {
                        "key": _mk_default("default"),
                    }
                }
            }
        }
        override = {
            "level1": {
                "level2": {
                    "level3": {
                        "key": _mk_force("force"),
                    }
                }
            }
        }
        result = deep_merge(base, override)
        assert result["level1"]["level2"]["level3"]["key"] == _mk_force("force")


class TestPriorityComplex:
    """Сложные сценарии слияния приоритетов."""

    def test_multiple_keys_different_priorities(self):
        """Несколько ключей с разными приоритетами."""
        base = {
            "key1": _mk_default("default1"),
            "key2": _mk_force("force2"),
            "key3": "normal3",
        }
        override = {
            "key1": _mk_force("force1"),  # побеждает (0 < 1000)
            "key2": _mk_default("default2"),  # проигрывает (1000 > 0)
            "key3": "override3",  # обычное переопределение
        }
        result = deep_merge(base, override)
        assert result["key1"] == _mk_force("force1")
        assert result["key2"] == _mk_force("force2")
        assert result["key3"] == "override3"

    def test_priority_with_nested_objects(self):
        """Приоритетное значение содержит вложенный объект."""
        base = {"key": _mk_default({"nested": "base"})}
        override = {"key": _mk_force({"nested": "override"})}
        result = deep_merge(base, override)
        assert result["key"] == _mk_force({"nested": "override"})

    def test_partial_override_with_priority(self):
        """Частичное переопределение с приоритетами."""
        base = {
            "nested": {
                "key1": _mk_default("default1"),
                "key2": "base2",
            }
        }
        override = {
            "nested": {
                "key1": _mk_force("force1"),
                "key3": "new3",
            }
        }
        result = deep_merge(base, override)
        assert result["nested"]["key1"] == _mk_force("force1")
        assert result["nested"]["key2"] == "base2"
        assert result["nested"]["key3"] == "new3"

    def test_empty_source(self):
        """Пустой source — без изменений."""
        base = {"key": _mk_default("value")}
        override = {}
        result = deep_merge(base, override)
        assert result == base

    def test_empty_target(self):
        """Пустой target — копируется source."""
        base = {}
        override = {"key": _mk_force("value")}
        result = deep_merge(base, override)
        assert result["key"] == _mk_force("value")
