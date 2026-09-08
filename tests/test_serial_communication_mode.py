import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from connection.serial_communication import SerialCommunication
from utilities.platform_runtime import get_operation_mode


class SerialCommunicationModeTests(unittest.TestCase):
    def test_operation_mode_precedence(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_operation_mode(True), "simulation")

        with patch.dict(os.environ, {"CIATEQ_OPERATION_MODE": "production"}, clear=True):
            self.assertEqual(get_operation_mode(True), "production")

        with patch.dict(os.environ, {"CIATEQ_OPERATION_MODE": "simulation"}, clear=True):
            self.assertEqual(get_operation_mode(False), "simulation")

    def test_production_auto_does_not_use_virtual_main_serial_port(self):
        controller = SerialCommunication()
        controller._simulation_enabled = False
        ftdi = SimpleNamespace(device="/dev/ttyUSB0", manufacturer="FTDI", description="FTDI USB")

        with patch.dict(os.environ, {"MAIN_SERIAL_PORT": os.path.expanduser("~/.hemodialisis/ppal")}, clear=True), \
             patch("connection.serial_communication.serial.tools.list_ports.comports", return_value=[ftdi]), \
             patch.object(controller, "_execute_connection", return_value=True) as execute:
            self.assertTrue(controller._find_and_connect_auto())

        execute.assert_called_once_with("/dev/ttyUSB0")

    def test_linux_simulation_missing_socat_is_a_retryable_failure(self):
        controller = SerialCommunication()
        controller._simulation_enabled = True

        with patch("connection.serial_communication.platform.system", return_value="Linux"), \
             patch("connection.serial_communication.os.path.exists", return_value=False), \
             patch("connection.serial_communication.os.path.lexists", return_value=False):
            self.assertFalse(controller.connect_port())

        self.assertFalse(controller.is_connected)


if __name__ == "__main__":
    unittest.main()
