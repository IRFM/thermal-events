from typing import Union

from sqlalchemy import or_

from thermal_events import (
    AnalysisStatus,
    Category,
    Dataset,
    Device,
    LineOfSight,
    Method,
    ProcessedMovie,
    Severity,
    ThermalEventCategoryLineOfSight,
    User,
)
from thermal_events.crud.base import CRUDBase, session_scope


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

    def email_address(self, user):
        """Return the email address of a user.

        Args:
            user (str): The name of the user

        Returns:
            str: The email address of the user. Returns None if the user does not exist
        """
        with session_scope() as session:
            res = session.query(User.email).filter(User.name == user).first()
            if res is not None:
                res = res[0]
            return res

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


class CRUDProcessedMovie(CRUDBase[ProcessedMovie]):
    """CRUD operations for ProcessedMovie objects."""

    def get_by_columns(
        self,
        **kwargs,
    ):
        """Retrieve ProcessedMovie objects based on specified columns and filter
        conditions.

        Args:
            **kwargs:
                Filter conditions for the query.

        Returns:
            list:
                Resulting ProcessedMovie objects.

        """
        with session_scope() as session:

            query = session.query(ProcessedMovie)

            if "experiment_id" in kwargs:
                kwargs["experiment_id"] = int(kwargs["experiment_id"])

            if "dataset" in kwargs:
                dataset = kwargs.pop("dataset")
                if isinstance(dataset, list):
                    cond = ()
                    for dat in dataset:
                        cond += (ProcessedMovie.dataset.like(f"%{dat}%"),)
                    query = query.filter(or_(*cond))
                else:
                    query = query.filter(ProcessedMovie.dataset.like(f"%{dataset}%"))

            if "method" in kwargs:
                method = kwargs.pop("method")
                query = query.filter(ProcessedMovie.method.like(f"%{method}%"))

            if "line_of_sight" in kwargs:
                line_of_sight = kwargs.pop("line_of_sight")
                query = query.filter(
                    ProcessedMovie.line_of_sight.like(f"%{line_of_sight}%")
                )

            if "category" in kwargs:
                event = kwargs.pop("category")
                query = query.filter(ProcessedMovie.category.like(f"%{event}%"))

            query = query.filter_by(**kwargs)

            return query.all()

    def delete(self, processed_movies: Union[list, ProcessedMovie, int]):
        """Delete ProcessedMovie objects from the database.

        Args:
            processed_movies (Union[list, ProcessedMovie, int]):
                List of ProcessedMovie objects, single ProcessedMovie object, or id(s) of
                ProcessedMovie(s) to delete.

        """
        if not isinstance(processed_movies, list):
            processed_movies = [processed_movies]

        with session_scope() as session:
            for processed_movie in processed_movies:
                if isinstance(processed_movie, ProcessedMovie):
                    processed_movie = processed_movie.id

                session.query(ProcessedMovie).filter_by(id=processed_movie).delete()
            session.commit()


user = CRUDUser(User)
thermal_event_category = CRUDThermalEventCategory(Category)
dataset = CRUDDataset(Dataset)
analysis_status = CRUDAnalysisStatus(AnalysisStatus)
line_of_sight = CRUDLineOfSight(LineOfSight)
method = CRUDMethod(Method)
device = CRUDDevice(Device)
severity = CRUDSeverity(Severity)
processed_movie = CRUDProcessedMovie(ProcessedMovie)
