from domain.common.duration import calculate_signed_duration


def test_negative_duration_keeps_sign_below_one_hour():
    result = calculate_signed_duration("00:30", "00:00")
    assert result.ok is True
    assert result.value_minutes == -30
    assert result.display == "-0:30"
    assert result.error is None


def test_positive_zero_and_negative_durations():
    assert calculate_signed_duration("00:30", "02:00").value_minutes == 90
    assert calculate_signed_duration("01:00", "01:00").display == "0:00"
    assert calculate_signed_duration("02:00", "00:30").display == "-1:30"


def test_missing_time_returns_business_error():
    result = calculate_signed_duration(None, "10:00")
    assert result.ok is False
    assert result.value_minutes is None
    assert result.display is None
    assert result.error.code == "MISSING_TIME"
    assert result.error.field == "debut"


def test_bad_format_returns_business_error():
    result = calculate_signed_duration("8h30", "10:00")
    assert result.ok is False
    assert result.error.code == "INVALID_TIME_FORMAT"
    assert result.error.field == "debut"


def test_out_of_range_time_returns_business_error():
    result = calculate_signed_duration("10:00", "25:99")
    assert result.ok is False
    assert result.error.code == "INVALID_TIME_VALUE"
    assert result.error.field == "fin"


def test_unexpected_type_returns_business_error():
    result = calculate_signed_duration([], "10:00")
    assert result.ok is False
    assert result.error.code == "INVALID_TIME_TYPE"
    assert result.error.field == "debut"


def test_overnight_is_only_applied_when_explicitly_requested():
    normal = calculate_signed_duration("23:30", "00:30")
    overnight = calculate_signed_duration("23:30", "00:30", allow_overnight=True)
    assert normal.value_minutes == -23 * 60
    assert normal.display == "-23:00"
    assert overnight.value_minutes == 60
    assert overnight.display == "1:00"
