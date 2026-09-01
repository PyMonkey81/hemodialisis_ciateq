import unittest
from unittest.mock import Mock

from core.ktv.ktv_controller import KtvController


class KtvConnectionWarningTest(unittest.TestCase):
    def test_connection_error_message_is_sent_only_once_per_measurement(self):
        controller = KtvController()
        controller._show_message_callback = Mock()
        controller._bioz_urea_controller = Mock()
        controller._bioz_urea_controller.is_enabled.return_value = False
        controller.grafcet.abort = Mock()

        controller._perform_send_bioz_command("SRTB")
        controller._perform_send_bioz_command("SRTB")

        self.assertEqual(controller._show_message_callback.call_count, 1)


if __name__ == "__main__":
    unittest.main()
