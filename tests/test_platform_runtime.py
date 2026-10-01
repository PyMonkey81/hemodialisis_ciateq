"""Tests para utilities/platform_runtime.py - configuración multiplataforma y puertos."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Agregar el directorio raíz al path para imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utilities.platform_runtime import (
    get_runtime_config_dir,
    sanitize_port_for_platform,
    is_linux,
    is_windows,
)


class TestSanitizePortForPlatform(unittest.TestCase):
    """Tests para sanitize_port_for_platform() - normalización de puertos."""

    def test_windows_port_unchanged_on_windows(self):
        """En Windows, COMn debe pasar sin cambios."""
        with patch("utilities.platform_runtime.is_linux", return_value=False):
            result = sanitize_port_for_platform("COM3")
            self.assertEqual(result, "COM3")

    def test_dev_port_unchanged_on_windows(self):
        """En Windows, /dev/ttyUSB0 debe pasar sin cambios."""
        with patch("utilities.platform_runtime.is_linux", return_value=False):
            result = sanitize_port_for_platform("/dev/ttyUSB0")
            self.assertEqual(result, "/dev/ttyUSB0")

    def test_auto_unchanged_on_windows(self):
        """En Windows, 'Auto' debe pasar sin cambios."""
        with patch("utilities.platform_runtime.is_linux", return_value=False):
            result = sanitize_port_for_platform("Auto")
            self.assertEqual(result, "Auto")

    def test_com_port_rejected_on_linux(self):
        """En Linux, COMn debe rechazarse y retornar 'Auto'."""
        with patch("utilities.platform_runtime.is_linux", return_value=True):
            with patch(
                "utilities.platform_runtime.feature_enabled", return_value=True
            ):
                result = sanitize_port_for_platform("COM3")
                self.assertEqual(result, "Auto")

    def test_dev_port_accepted_on_linux(self):
        """En Linux, /dev/* debe aceptarse."""
        with patch("utilities.platform_runtime.is_linux", return_value=True):
            with patch(
                "utilities.platform_runtime.feature_enabled", return_value=True
            ):
                result = sanitize_port_for_platform("/dev/ttyUSB0")
                self.assertEqual(result, "/dev/ttyUSB0")

    def test_auto_accepted_on_linux(self):
        """En Linux, 'Auto' debe aceptarse."""
        with patch("utilities.platform_runtime.is_linux", return_value=True):
            with patch(
                "utilities.platform_runtime.feature_enabled", return_value=True
            ):
                result = sanitize_port_for_platform("Auto")
                self.assertEqual(result, "Auto")

    def test_invalid_port_rejected_on_linux(self):
        """En Linux, puerto sin /dev/ (salvo 'Auto') debe rechazarse."""
        with patch("utilities.platform_runtime.is_linux", return_value=True):
            with patch(
                "utilities.platform_runtime.feature_enabled", return_value=True
            ):
                result = sanitize_port_for_platform("INVALID_PORT")
                self.assertEqual(result, "Auto")

    def test_sanitize_disabled_returns_original(self):
        """Si sanitize_linux_com_ports está deshabilitado, devuelve original."""
        with patch("utilities.platform_runtime.is_linux", return_value=True):
            with patch(
                "utilities.platform_runtime.feature_enabled", return_value=False
            ):
                result = sanitize_port_for_platform("COM3")
                self.assertEqual(result, "COM3")

    def test_none_port_defaults_to_auto(self):
        """Puerto None debe convertirse a 'Auto'."""
        with patch("utilities.platform_runtime.is_linux", return_value=False):
            result = sanitize_port_for_platform(None)
            self.assertEqual(result, "Auto")

    def test_empty_string_defaults_to_auto(self):
        """Cadena vacía debe convertirse a 'Auto'."""
        with patch("utilities.platform_runtime.is_linux", return_value=False):
            result = sanitize_port_for_platform("")
            self.assertEqual(result, "Auto")


class TestGetRuntimeConfigDirBasic(unittest.TestCase):
    """Tests básicos para get_runtime_config_dir() cuando no está frozen."""

    def test_ciateq_config_dir_when_set(self):
        """Debe usar CIATEQ_CONFIG_DIR cuando está definida y es escribible."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"CIATEQ_CONFIG_DIR": tmpdir}, clear=False):
                result = get_runtime_config_dir()
                self.assertEqual(result, Path(tmpdir))

    def test_uses_repo_config_when_not_frozen_no_env(self):
        """Sin CIATEQ_CONFIG_DIR y sin frozen, debe usar repo config."""
        # Guardar valor actual de CIATEQ_CONFIG_DIR si existe
        old_val = os.environ.get("CIATEQ_CONFIG_DIR")
        try:
            # Limpiar la variable
            if "CIATEQ_CONFIG_DIR" in os.environ:
                del os.environ["CIATEQ_CONFIG_DIR"]
            
            # Si no está frozen, debe retornar repo config
            if not getattr(sys, "frozen", False):
                result = get_runtime_config_dir()
                expected = Path(__file__).resolve().parent.parent / "config"
                self.assertEqual(result, expected)
        finally:
            if old_val:
                os.environ["CIATEQ_CONFIG_DIR"] = old_val


if __name__ == "__main__":
    unittest.main()

