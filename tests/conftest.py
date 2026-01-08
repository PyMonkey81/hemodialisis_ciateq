# tests/conftest.py
import pytest
from unittest.mock import MagicMock

class MockSerial:
    def conectar(self): return False
    def iniciar_lectura(self): pass
    def detener(self): pass
    def join(self, timeout=None): pass

@pytest.fixture(autouse=True)
def mock_dependencies(monkeypatch):
    monkeypatch.setattr("connection.comunicacion_serial.ComunicacionSerial", MockSerial)
    # Si sistema_alarmas también usa hilos pesados:
    # monkeypatch.setattr("core.alarmas.SistemaAlarmas", MagicMock)