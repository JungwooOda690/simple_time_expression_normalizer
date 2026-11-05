import unittest
from datetime import datetime

from simple_time_expression_normalizer import normalize, normalize_or_none


class FixedClock:
    """A clock that always returns the same instant.

    Tests never touch the real wall clock, so they cannot flake on a slow
    machine or around midnight.
    """

    def __init__(self, moment: datetime) -> None:
        self._moment = moment

    def __call__(self) -> datetime:
        return self._moment


class NormalizeTests(unittest.TestCase):
    def setUp(self) -> None:
        # 2024-03-15 was a Friday; the exact weekday does not matter, but the
        # date is fixed so offsets are easy to read.
        self.clock = FixedClock(datetime(2024, 3, 15, 9, 30, 0))

    def test_now_returns_clock_instant(self) -> None:
        self.assertEqual(
            normalize("now", now=self.clock),
            datetime(2024, 3, 15, 9, 30, 0),
        )

    def test_today_is_midnight(self) -> None:
        self.assertEqual(
            normalize("today", now=self.clock),
            datetime(2024, 3, 15, 0, 0, 0),
        )

    def test_tomorrow_is_midnight_next_day(self) -> None:
        self.assertEqual(
            normalize("tomorrow", now=self.clock),
            datetime(2024, 3, 16, 0, 0, 0),
        )

    def test_yesterday_is_midnight_previous_day(self) -> None:
        self.assertEqual(
            normalize("yesterday", now=self.clock),
            datetime(2024, 3, 14, 0, 0, 0),
        )

    def test_today_at_five(self) -> None:
        self.assertEqual(
            normalize("today at 5", now=self.clock),
            datetime(2024, 3, 15, 5, 0, 0),
        )

    def test_tomorrow_at_1730(self) -> None:
        self.assertEqual(
            normalize("tomorrow at 17:30", now=self.clock),
            datetime(2024, 3, 16, 17, 30, 0),
        )

    def test_yesterday_at_530am(self) -> None:
        self.assertEqual(
            normalize("yesterday at 5:30 am", now=self.clock),
            datetime(2024, 3, 14, 5, 30, 0),
        )

    def test_bare_pm_time_anchors_to_today(self) -> None:
        self.assertEqual(
            normalize("5pm", now=self.clock),
            datetime(2024, 3, 15, 17, 0, 0),
        )

    def test_bare_24_hour_time_anchors_to_today(self) -> None:
        self.assertEqual(
            normalize("17:30", now=self.clock),
            datetime(2024, 3, 15, 17, 30, 0),
        )

    def test_noon_and_midnight_meridiem(self) -> None:
        self.assertEqual(
            normalize("12pm", now=self.clock),
            datetime(2024, 3, 15, 12, 0, 0),
        )
        self.assertEqual(
            normalize("12am", now=self.clock),
            datetime(2024, 3, 15, 0, 0, 0),
        )

    def test_case_and_whitespace_are_ignored(self) -> None:
        self.assertEqual(
            normalize("  TOMORROW   AT   5 PM  ", now=self.clock),
            datetime(2024, 3, 16, 17, 0, 0),
        )

    def test_invalid_expressions_raise_value_error(self) -> None:
        for bad in ["", "   ", "soon", "today at", "at 5", "25:00", "5:75", "13pm"]:
            with self.subTest(expression=bad):
                with self.assertRaises(ValueError):
                    normalize(bad, now=self.clock)

    def test_non_string_raises_type_error(self) -> None:
        with self.assertRaises(TypeError):
            normalize(None, now=self.clock)  # type: ignore[arg-type]

    def test_normalize_or_none_returns_none_on_invalid(self) -> None:
        self.assertIsNone(normalize_or_none("soon", now=self.clock))
        self.assertIsNone(normalize_or_none("", now=self.clock))
        self.assertIsNone(normalize_or_none(None, now=self.clock))  # type: ignore[arg-type]

    def test_normalize_or_none_returns_value_on_valid(self) -> None:
        self.assertEqual(
            normalize_or_none("today at 5", now=self.clock),
            datetime(2024, 3, 15, 5, 0, 0),
        )


if __name__ == "__main__":
    unittest.main()
