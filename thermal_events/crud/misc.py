from thermal_events.crud.base import CRUDBase, session_scope
from thermal_events import (
    LineOfSight,
    ThermalEventType,
    ThermalEventTypeLineOfSight,
    User,
    Dataset,
    AnalysisStatus,
)


class CRUDUser(CRUDBase[User]):
    def list(self):
        with session_scope() as session:
            res = session.query(User.name).all()
            return [x[0] for x in res]

    def has_write_rights(self):
        users = self.list()
        current_user = CRUDUser._user_name()
        return current_user in users

    def has_read_rights(self):
        return self.has_write_rights()

    @staticmethod
    def _user_name() -> str:
        """
        Returns the current user name
        """
        import getpass
        return getpass.getuser()


class CRUDThermalEventType(CRUDBase[ThermalEventType]):
    def list(self):
        with session_scope() as session:
            res = session.query(ThermalEventType.name).all()
            return [x[0] for x in res]

    def compatible_lines_of_sight(self, thermal_event: str):
        with session_scope() as session:
            res = (
                session.query(ThermalEventTypeLineOfSight.line_of_sight)
                .filter_by(thermal_event_type=thermal_event)
                .all()
            )
            return [x[0] for x in res]


class CRUDDataset(CRUDBase[Dataset]):
    def list(self):
        with session_scope() as session:
            res = session.query(Dataset.id).all()
            return [x[0] for x in res]


class CRUDAnalysisStatus(CRUDBase[AnalysisStatus]):
    def list(self):
        with session_scope() as session:
            res = session.query(AnalysisStatus.name).all()
            return [x[0] for x in res]


class CRUDLineOfSight(CRUDBase[LineOfSight]):
    def list(self):
        with session_scope() as session:
            res = session.query(LineOfSight.name).all()
            return [x[0] for x in res]


user = CRUDUser(User)
thermal_event_type = CRUDThermalEventType(ThermalEventType)
dataset = CRUDDataset(Dataset)
analysis_status = CRUDAnalysisStatus(AnalysisStatus)
line_of_sight = CRUDLineOfSight(LineOfSight)
