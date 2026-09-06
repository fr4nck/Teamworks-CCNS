from domain.common.duration import (
    calculate_time_difference,
    operate_signed_durations,
    parse_clock_time,
    parse_signed_duration,
)
from teamworks.Utils.UTILS_Duration import duree_presence_wx, operation_heures_wx


def test_clock_time_is_limited_to_one_day():
    assert parse_clock_time("23:59", "debut").ok is True
    result = parse_clock_time("30:00", "debut")
    assert result.ok is False
    assert result.error.code == "INVALID_TIME_VALUE"


def test_signed_duration_can_exceed_24_hours():
    result = parse_signed_duration("+45:00", "value_a")
    assert result.ok is True
    assert result.value_minutes == 45 * 60


def test_common_clock_difference_keeps_negative_sub_hour_value():
    result = calculate_time_difference("00:30", "00:00")
    assert result.ok is True
    assert result.value_minutes == -30
    assert result.display == "-0:30"


def test_common_accumulated_duration_operation_has_no_23_hour_limit():
    result = operate_signed_durations("+30:00", "+15:00", "addition")
    assert result.ok is True
    assert result.value_minutes == 45 * 60
    assert result.display == "45:00"


def test_wx_operation_adapter_preserves_historical_format():
    assert operation_heures_wx(None, None)[0] == "+0:00"
    assert operation_heures_wx("+10:00", "+02:30", "addition")[0] == "+12:30"
    assert operation_heures_wx("+00:00", "+00:30", "soustraction")[0] == "-0:30"
    assert operation_heures_wx("+02:00", "+00:30", "soustraction")[0] == "+1:30"
    assert operation_heures_wx("+00:30", "+02:00", "soustraction")[0] == "-1:30"
    assert operation_heures_wx("-01:00", "+00:30", "addition")[0] == "-0:30"
    assert operation_heures_wx("+30:00", "+15:00", "addition")[0] == "+45:00"


def test_wx_presence_adapter_treats_inputs_as_clock_times():
    display, result = duree_presence_wx("09:00", "08:30")
    assert result.ok is True
    assert result.value_minutes == -30
    assert display == "-0:30"


def test_wx_adapters_return_structured_error_without_ui_exception():
    display, result = duree_presence_wx("25:00", "08:30")
    assert display is None
    assert result.ok is False
    assert result.error.code == "INVALID_TIME_VALUE"

    display, result = operation_heures_wx("30:00", "+01:00", "addition")
    assert display is None
    assert result.ok is False
    assert result.error.code == "INVALID_DURATION_FORMAT"
