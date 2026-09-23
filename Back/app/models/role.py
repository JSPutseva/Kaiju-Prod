from enum import Enum


class UserRole(str, Enum):
    QC = "QC"
    LC = "LC"
    CD = "CD"