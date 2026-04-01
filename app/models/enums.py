from enum import Enum
class Role(str, Enum):
    admin = "admin"; analyst = "analyst"; viewer = "viewer"
class RecordType(str, Enum):
    income = "income"; expense = "expense"
