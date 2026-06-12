from infrastructure.repositories.base import InMemoryRepository
from domain.activity.season import Season
from domain.activity.period import Period
from domain.activity.activity import Activity
from domain.activity.place import Place
from domain.activity.timeslot import Timeslot
from domain.activity.assignment import Assignment


class SeasonRepository(InMemoryRepository[Season]):
    pass


class PeriodRepository(InMemoryRepository[Period]):
    def list_by_season_id(self, season_id: str) -> list[Period]:
        return [item for item in self.list_all() if item.season_id == season_id]


class ActivityRepository(InMemoryRepository[Activity]):
    pass


class PlaceRepository(InMemoryRepository[Place]):
    pass


class TimeslotRepository(InMemoryRepository[Timeslot]):
    def list_by_activity_id(self, activity_id: str) -> list[Timeslot]:
        return [item for item in self.list_all() if item.activity_id == activity_id]


class AssignmentRepository(InMemoryRepository[Assignment]):
    def list_by_person_id(self, person_id: str) -> list[Assignment]:
        return [item for item in self.list_all() if item.person_id == person_id]
