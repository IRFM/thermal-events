from thermal_events.crud.base import CRUDBase, session_scope
from thermal_events import (
    LineOfSight,
    Category,
    ThermalEventCategoryLineOfSight,
    User,
    Dataset,
    AnalysisStatus,
    Method,
    Device,
    Severity,
)


class CRUDUser(CRUDBase[User]):
    """CRUD operations for User objects."""

    def list(self):
        """List all user names.

        Returns:
            List[str]: The list of user names.

        """
        with session_scope() as session:
            res = session.query(User.name).all()
            return [x[0] for x in res]

    def has_write_rights(self):
        """Check if the current user has write rights.

        Returns:
            bool: True if the current user has write rights, False otherwise.

        """
        users = self.list()
        current_user = CRUDUser._user_name()
        return current_user in users

    def has_read_rights(self):
        """Check if the current user has read rights.

        Returns:
            bool: True if the current user has read rights, False otherwise.

        """
        return self.has_write_rights()

    @staticmethod
    def _user_name() -> str:
        """
        Returns the current user name.

        Returns:
            str: The current user name.

        """
        import getpass

        return getpass.getuser()


class CRUDThermalEventCategory(CRUDBase[Category]):
    """CRUD operations for ThermalEventCategory objects."""

    def list(self):
        """List all thermal event types.

        Returns:
            List[str]: The list of thermal event types.

        """
        with session_scope() as session:
            res = session.query(Category.name).all()
            return [x[0] for x in res]

    def compatible_lines_of_sight(self, category: str):
        """Get the compatible lines of sight for a given thermal event category.

        Args:
            category (str): The thermal event category.

        Returns:
            List[str]: The list of compatible lines of sight.

        """
        with session_scope() as session:
            res = (
                session.query(ThermalEventCategoryLineOfSight.line_of_sight)
                .filter_by(thermal_event_category=category)
                .all()
            )
            return [x[0] for x in res]


class CRUDDataset(CRUDBase[Dataset]):
    """CRUD operations for Dataset objects."""

    def list(self):
        """List all dataset IDs.

        Returns:
            List[int]: The list of dataset IDs.

        """
        with session_scope() as session:
            res = session.query(Dataset.id).all()
            return [x[0] for x in res]


class CRUDAnalysisStatus(CRUDBase[AnalysisStatus]):
    """CRUD operations for AnalysisStatus objects."""

    def list(self):
        """List all analysis status names.

        Returns:
            List[str]: The list of analysis status names.

        """
        with session_scope() as session:
            res = session.query(AnalysisStatus.name).all()
            return [x[0] for x in res]


class CRUDLineOfSight(CRUDBase[LineOfSight]):
    """CRUD operations for LineOfSight objects."""

    def list(self):
        """List all line of sight names.

        Returns:
            List[str]: The list of line of sight names.

        """
        with session_scope() as session:
            res = session.query(LineOfSight.name).all()
            return [x[0] for x in res]


class CRUDMethod(CRUDBase[Method]):
    """CRUD operations for Method objects."""

    def list(self):
        """List all method names.

        Returns:
            List[str]: The list of method names.

        """
        with session_scope() as session:
            res = session.query(Method.name).all()
            return [x[0] for x in res]


class CRUDDevice(CRUDBase[Device]):
    """CRUD operations for Device objects."""

    def list(self):
        """List all device names.

        Returns:
            List[str]: The list of device names.

        """
        with session_scope() as session:
            res = session.query(Device.name).all()
            return [x[0] for x in res]


class CRUDSeverity(CRUDBase[Severity]):
    """CRUD operations for Severity objects."""

    def list(self):
        """List all severity types.

        Returns:
            List[str]: The list of everity types.

        """
        with session_scope() as session:
            res = session.query(Severity.name).all()
            return [x[0] for x in res]


user = CRUDUser(User)
thermal_event_category = CRUDThermalEventCategory(Category)
dataset = CRUDDataset(Dataset)
analysis_status = CRUDAnalysisStatus(AnalysisStatus)
line_of_sight = CRUDLineOfSight(LineOfSight)
method = CRUDMethod(Method)
device = CRUDDevice(Device)
severity = CRUDSeverity(Severity)
