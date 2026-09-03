from teamworks.Utils import UTILS_Responsive


def test_ultrawide_half_screen_stays_two_columns_at_100_percent():
    assert UTILS_Responsive.form_column_count(1720, 100) == 2


def test_standard_half_screen_stacks_at_100_percent():
    assert UTILS_Responsive.form_column_count(960, 100) == 1


def test_strong_zoom_can_stack_an_ultrawide_half_screen():
    assert UTILS_Responsive.form_column_count(1720, 200) == 1


def test_future_220_percent_zoom_is_already_supported_by_the_rule():
    assert UTILS_Responsive.form_column_count(1720, 220) == 1


def test_invalid_scale_falls_back_to_100_percent():
    assert UTILS_Responsive.logical_width(1000, 0) == 1000.0
