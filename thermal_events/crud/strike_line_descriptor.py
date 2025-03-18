from typing import List, Union

from thermal_events import StrikeLineDescriptor
from thermal_events.crud.base import CRUDBase, session_scope


class CRUDStrikeLineDescriptor(CRUDBase[StrikeLineDescriptor]):
    def get_by_columns(
        self,
        return_columns: Union[list, None] = None,
        return_query: bool = False,
        **kwargs,
    ):
        """Retrieve StrikeLineDescriptor objects based on specified columns and filter
        conditions.

        Args:
            return_columns (Union[list, None], optional):
                List of columns to include in the result. Defaults to None.
            return_query (bool, optional):
                Whether to return the SQLAlchemy query object. Defaults to False.
            **kwargs:
                Filter conditions for the query.

        Returns:
            Union[list, tuple, sqlalchemy.orm.query.Query]:
                Resulting StrikeLineDescriptor objects or columns based on the specified
                conditions.
                If `return_columns` is a list, a tuple of columns is returned.
                If `return_query` is True, the SQLAlchemy query object is returned.

        """
        with session_scope() as session:
            if isinstance(return_columns, list):
                query = session.query(
                    *[getattr(StrikeLineDescriptor, x) for x in return_columns]
                )
            else:
                query = session.query(StrikeLineDescriptor)

            query = query.filter_by(**kwargs)

            if return_query:
                return query
            if isinstance(return_columns, list):
                out = tuple(list(x) for x in zip(*query.all()))

                # Case then the result of the query is empty
                if len(out) == 0:
                    out = tuple([] for _ in range(len(return_columns)))

                if len(out) == 1:
                    out = out[0]
                return out
            return query.all()

    def get_by_flag_RT(self, flag_RT=True):
        """Retrieve StrikeLineDescriptor objects based on the value of flag_RT.

        Args:
            flag_RT (str):
                Flag indicating if the descriptor was created during an experiment or not.

        Returns:
            Union[list, tuple]:
                Resulting StrikeLineDescriptor objects or columns based on the specified
                device.

        """
        with session_scope() as session:
            return (
                session.query(StrikeLineDescriptor)
                .filter(StrikeLineDescriptor.flag_RT == flag_RT)
                .all()
            )

    def update(
        self, obj_in: Union[StrikeLineDescriptor, List[StrikeLineDescriptor]]
    ) -> None:
        """Update an existing object or a list of StrikeLineDescriptor objects.

        Args:
            obj_in (Union[StrikeLineDescriptor, List[StrikeLineDescriptor]]): The
            object(s) to update.

        """

        if not isinstance(obj_in, list):
            obj_in = [obj_in]

        with session_scope() as session:
            for obj in obj_in:
                session.merge(obj)

    def delete(self, obj_in: Union[list, StrikeLineDescriptor, int]):
        """Delete StrikeLineDescriptor objects from the database.

        Args:
            events (Union[list, StrikeLineDescriptor, int]):
                List of StrikeLineDescriptor objects, single StrikeLineDescriptor
                object, or id(s) of StrikeLineDescriptor(s) to delete.

        """
        if not isinstance(obj_in, list):
            obj_in = [obj_in]

        with session_scope() as session:
            for obj in obj_in:
                if isinstance(obj, StrikeLineDescriptor):
                    obj = obj.id

                session.query(StrikeLineDescriptor).filter_by(id=obj).delete()


strike_line_descriptor = CRUDStrikeLineDescriptor(StrikeLineDescriptor)
