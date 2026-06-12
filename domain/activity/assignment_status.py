from enum import Enum


class AssignmentStatus(str, Enum):
    DRAFT = "DRAFT"
    PLANNED = "PLANNED"
    VALIDATED = "VALIDATED"
    EXPORTED = "EXPORTED"
    CANCELLED = "CANCELLED"
