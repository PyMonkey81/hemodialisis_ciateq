import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from gui.appMainHemodialysis import HemodialysisHMI


class InvalidPrimingStatusGuardTest(unittest.TestCase):
    def test_invalid_priming_status_does_not_crash(self):
        hmi = HemodialysisHMI.__new__(HemodialysisHMI)
        hmi.current_values = {"treatmentModeSelection": 0}
        hmi._last_priming_status = -1
        hmi.alarm_system = None
        hmi.current_process_status = type(
            "StatusLabel",
            (),
            {"setText": lambda *args, **kwargs: None, "setStyleSheet": lambda *args, **kwargs: None},
        )()
        hmi.state = type(
            "State",
            (),
            {"current_phase": None, "set_phase": lambda *args, **kwargs: True},
        )()
        hmi.screen_state_manager = type(
            "ScreenStateManager",
            (),
            {"update_all_screens": lambda *args, **kwargs: None},
        )()
        hmi.hardware_mapper = type(
            "Mapper",
            (),
            {"get_phase": lambda *args, **kwargs: None, "get_display_text": lambda *args, **kwargs: "STATUS"},
        )()
        hmi.timer_manager = type("TimerManager", (), {"sync_with_hardware": lambda *args, **kwargs: None})()
        hmi.treatment_controller = None
        hmi.show_info_message = lambda *args, **kwargs: None

        hmi.update_value("primingProcessStatus", "bad-status")

        self.assertEqual(hmi._last_priming_status, -1)


if __name__ == "__main__":
    unittest.main()
