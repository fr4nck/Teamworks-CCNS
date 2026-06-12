from datetime import date, datetime, time

from domain.activity.season import Season
from domain.activity.period import Period
from domain.activity.activity import Activity
from domain.activity.place import Place
from domain.activity.timeslot import Timeslot
from domain.activity.assignment import Assignment
from domain.activity.time_nature import TimeNature


def test_season_creation():
    season = Season(code="2026-2027", label="Saison 2026-2027", start_date=date(2026, 9, 1), end_date=date(2027, 8, 31))
    assert season.code == "2026-2027"


def test_timeslot_creation():
    slot = Timeslot(
        activity_id="activity-1",
        place_id="place-1",
        code="EMS-MON-01",
        label="Lundi EMS",
        weekday=0,
        start_time=time(18, 0),
        end_time=time(19, 30),
        prep_ratio=0.3333,
    )
    assert slot.prep_ratio == 0.3333


def test_assignment_computes_gross_duration_and_prep():
    assignment = Assignment(
        person_id="person-1",
        period_id="period-1",
        activity_id="activity-1",
        title="Séance sport",
        starts_at=datetime(2026, 9, 7, 18, 0),
        ends_at=datetime(2026, 9, 7, 21, 0),
        break_minutes=0,
        prep_ratio=0.3333,
        time_nature=TimeNature.FACE_PUBLIC,
        contract_id="contract-1",
    )
    assert assignment.compute_gross_duration_minutes() == 180
    assert assignment.compute_auto_prep_minutes() == 60


def test_assignment_rejects_multiple_main_supports():
    try:
        Assignment(
            person_id="person-1",
            period_id="period-1",
            activity_id="activity-1",
            title="Séance",
            contract_id="contract-1",
            volunteer_engagement_id="vol-1",
        )
    except ValueError:
        assert True
    else:
        assert False
