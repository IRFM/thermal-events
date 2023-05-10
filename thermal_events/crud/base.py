from contextlib import contextmanager
from typing import Any, Generic, List, Optional, Type, TypeVar, Union

from thermal_events import Base
from thermal_events.database import get_db

ModelType = TypeVar("ModelType", bound=Base)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
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
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLAlchemy model class
        """

        self.model = model

    def get(self, id: Any) -> Optional[ModelType]:
        with session_scope() as session:
            return session.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        with session_scope() as session:
            return session.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_in: Union[list, ModelType]) -> ModelType:
        if not isinstance(obj_in, list):
            obj_in = [obj_in]

        with session_scope() as session:
            session.add_all(obj_in)
            session.commit()
            return obj_in
