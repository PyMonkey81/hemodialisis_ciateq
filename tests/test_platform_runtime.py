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
    get_runtime_data_dir,
    get_runtime_data_path,
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


class TestGetRuntimeDataDir(unittest.TestCase):
    """Tests para get_runtime_data_dir() - directorio de datos escribibles."""

    def test_frozen_uses_executable_directory(self):
        """Un programa congelado (PyInstaller) debe usar la carpeta del ejecutable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_exe = Path(tmpdir) / "HemodialisisApp.exe"
            fake_exe.touch()
            
            # Mock: sys.frozen = True, sys.executable = ruta del exe temporal
            with patch.object(sys, "frozen", True, create=True):
                with patch.object(sys, "executable", str(fake_exe)):
                    # Limpiar CIATEQ_DATA_DIR para que no interfiera
                    with patch.dict(os.environ, {}, clear=True):
                        result = get_runtime_data_dir()
                        # Debe ser el padre del ejecutable (tmpdir)
                        self.assertEqual(result, Path(tmpdir))

    def test_ciateq_data_dir_when_set(self):
        """Debe usar CIATEQ_DATA_DIR cuando está definida y es escribible."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"CIATEQ_DATA_DIR": tmpdir}, clear=False):
                result = get_runtime_data_dir()
                self.assertEqual(result, Path(tmpdir))

    def test_not_frozen_uses_repo_root(self):
        """Sin frozen, debe usar la raíz del repositorio."""
        # Garantizar que sys.frozen no existe o es False
        with patch.object(sys, "frozen", False, create=True):
            with patch.dict(os.environ, {}, clear=True):
                result = get_runtime_data_dir()
                expected = Path(__file__).resolve().parent.parent
                self.assertEqual(result, expected)

    def test_never_uses_meipass_for_writing(self):
        """Incluso congelado, NUNCA debe usar sys._MEIPASS para escribir."""
        # Verificar que la función NO menciona sys._MEIPASS en el path de escritura
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_exe = Path(tmpdir) / "app.exe"
            fake_exe.touch()
            
            with patch.object(sys, "frozen", True, create=True):
                with patch.object(sys, "executable", str(fake_exe)):
                    with patch.object(sys, "_MEIPASS", "/fake/meipass", create=True):
                        with patch.dict(os.environ, {}, clear=True):
                            result = get_runtime_data_dir()
                            # Nunca debe ser _MEIPASS
                            self.assertNotEqual(result, Path("/fake/meipass"))
                            # Debe ser la carpeta del ejecutable
                            self.assertEqual(result, Path(tmpdir))


class TestGetRuntimeDataPath(unittest.TestCase):
    """Tests para get_runtime_data_path(*parts) - construir rutas de datos."""

    def test_constructs_path_with_parts(self):
        """Debe construir rutas correctamente con múltiples partes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"CIATEQ_DATA_DIR": tmpdir}, clear=False):
                result = get_runtime_data_path("logs", "tratamiento_hemodialisis", "file.csv")
                expected = Path(tmpdir) / "logs" / "tratamiento_hemodialisis" / "file.csv"
                self.assertEqual(result, expected)

    def test_single_part(self):
        """Debe funcionar con una sola parte."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"CIATEQ_DATA_DIR": tmpdir}, clear=False):
                result = get_runtime_data_path("exports")
                expected = Path(tmpdir) / "exports"
                self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()

