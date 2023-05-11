from contextlib import contextmanager
from typing import Any, Generic, List, Optional, Type, TypeVar, Union

from thermal_events import Base
from thermal_events.database import get_db

ModelType = TypeVar("ModelType", bound=Base)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations.

    Yields:
        Session: The database session.

    Raises:
        Exception: Any exception raised during the operations.

    """
    session = get_db()
    try:
        yield session
        # session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class CRUDBase(Generic[ModelType]):
    """CRUD operations for SQLAlchemy models.

    Args:
        model (Type[ModelType]): A SQLAlchemy model class.

    """

    def __init__(self, model: Type[ModelType]):
        """Initialize the CRUDBase with the given model.

        Args:
            model (Type[ModelType]): A SQLAlchemy model class.

        """
        self.model = model

    def get(self, id: Any) -> Optional[ModelType]:
        """Get a single object by ID.

        Args:
            id (Any): The ID of the object to retrieve.

        Returns:
            Optional[ModelType]: The retrieved object, if found. Otherwise, None.

        """
        with session_scope() as session:
            return session.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get multiple objects with optional pagination.

        Args:
            skip (int, optional): The number of objects to skip. Defaults to 0.
            limit (int, optional): The maximum number of objects to retrieve. Defaults
            to 100.

        Returns:
            List[ModelType]: The list of retrieved objects.

        """
        with session_scope() as session:
            return session.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_in: Union[list, ModelType]) -> ModelType:
        """Create a new object or a list of objects.

        Args:
            obj_in (Union[list, ModelType]): The object(s) to create.

        Returns:
            ModelType: The created object.

        """
        if not isinstance(obj_in, list):
            obj_in = [obj_in]

        with session_scope() as session:
            session.add_all(obj_in)
            session.commit()
            return obj_in
