from typing import Union, List

from sqlalchemy import and_, not_, or_

from thermal_events import ThermalEvent, ParentChildRelationship
from thermal_events.crud.base import CRUDBase, session_scope


class CRUDThermalEvent(CRUDBase[ThermalEvent]):
    """CRUD operations for ThermalEvent objects."""

    def get_by_columns(
        self,
        return_columns: Union[list, None] = None,
        return_query: bool = False,
        **kwargs,
    ):
        """Retrieve ThermalEvent objects based on specified columns and filter
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
                Resulting ThermalEvent objects or columns based on the specified
                conditions.
                If `return_columns` is a list, a tuple of columns is returned.
                If `return_query` is True, the SQLAlchemy query object is returned.

        """
        with session_scope() as session:
            if isinstance(return_columns, list):
                query = session.query(
                    *[getattr(ThermalEvent, x) for x in return_columns]
                )
            else:
                query = session.query(ThermalEvent)

            if "experiment_id" in kwargs:
                kwargs["experiment_id"] = int(kwargs["experiment_id"])

            if "dataset" in kwargs:
                dataset = kwargs.pop("dataset")
                if isinstance(dataset, str):
                    dataset = [int(x) for x in dataset.split(",")]
                elif isinstance(dataset, int):
                    dataset = [dataset]

                cond = ()
                for dat in dataset:
                    cond += (
                        ThermalEvent.dataset.op("REGEXP")(rf"(^|,\s*)\s*{dat}\s*(,|$)"),
                    )
                query = query.filter(or_(*cond))

            if "method" in kwargs:
                method = kwargs.pop("method")
                query = query.filter(ThermalEvent.method.like(f"%{method}%"))

            if "comments" in kwargs:
                comments = kwargs.pop("comments")
                query = query.filter(ThermalEvent.comments.like(f"%{comments}%"))

            if "line_of_sight" in kwargs:
                line_of_sight = kwargs.pop("line_of_sight")
                query = query.filter(
                    ThermalEvent.line_of_sight.like(f"%{line_of_sight}%")
                )

            if "category" in kwargs:
                event = kwargs.pop("category")
                query = query.filter(ThermalEvent.category.like(f"%{event}%"))

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

    def get_by_columns_exclude_time_intervals(self, time_intervals: list, **kwargs):
        """Retrieve ThermalEvent objects excluding the ones that begin and end
        in specified time intervals. If a thermal event has only parts of its
        timestamps in an interval, it is not excluded.

        Args:
            time_intervals (list):
                List of time intervals to exclude, in nanosecond. Each interval
                should be given as a list with two elements [start_time, end_time].
            **kwargs:
                Additional filter conditions for the query.

        Returns:
            list:
                Resulting ThermalEvent objects excluding the specified time intervals.

        Raises:
            ValueError: If the time intervals are not given as a list of lists.

        """
        query = self.get_by_columns(return_query=True, **kwargs)
        with session_scope() as session:
            query = query.with_session(session)

            if not isinstance(time_intervals[0], list):
                time_intervals = [time_intervals]

            assert all(isinstance(el, list) for el in time_intervals), ValueError(
                "The time intervals must be given as a list of lists."
            )

            for interval in time_intervals:
                inf = interval[0]
                sup = interval[1]

                conds = []
                if inf is not None:
                    conds.append(ThermalEvent.initial_timestamp_ns >= inf)
                if sup is not None:
                    conds.append(ThermalEvent.final_timestamp_ns <= sup)

                if len(conds) == 1:
                    conds = conds[0]
                else:
                    conds = and_(*conds)

                query = query.filter(not_(conds))

            if "return_columns" in kwargs and isinstance(
                kwargs["return_columns"], list
            ):
                out = tuple(list(x) for x in zip(*query.all()))
                if len(out) == 1:
                    out = out[0]
                return out
            return query.all()

    def get_by_columns_in_time_intervals(self, time_intervals: list, **kwargs):
        """Retrieve ThermalEvent objects that happen in specified time intervals.

        Args:
            time_intervals (list):
                List of time intervals to include, in nanosecond. Each interval
                should be given as a list with two elements [start_time, end_time].
            **kwargs:
                Additional filter conditions for the query.

        Returns:
            list:
                Resulting ThermalEvent objects in the specified time intervals.

        Raises:
            ValueError: If the time intervals are not given as a list of lists.

        """
        query = self.get_by_columns(return_query=True, **kwargs)
        with session_scope() as session:
            query = query.with_session(session)

            if not isinstance(time_intervals[0], list):
                time_intervals = [time_intervals]

            assert all(isinstance(el, list) for el in time_intervals), ValueError(
                "The time intervals must be given as a list of lists."
            )

            conds = []
            for interval in time_intervals:
                inf = interval[0]
                sup = interval[1]

                cond = []
                if inf is not None:
                    cond.append(ThermalEvent.initial_timestamp_ns >= inf)
                if sup is not None:
                    cond.append(ThermalEvent.final_timestamp_ns <= sup)

                if len(cond) == 1:
                    cond = cond[0]
                else:
                    cond = and_(*cond)
                conds.append(cond)

            if len(conds) == 1:
                conds = conds[0]
            else:
                conds = or_(*conds)
            query = query.filter(conds)

            if "return_columns" in kwargs and isinstance(
                kwargs["return_columns"], list
            ):
                out = tuple(list(x) for x in zip(*query.all()))
                if len(out) == 1:
                    out = out[0]
                return out
            return query.all()

    def get_by_experiment_id(self, id_inf: int, id_sup: int = None, **kwargs):
        """Retrieve ThermalEvent objects based on experiment ids.

        Args:
            id_inf (int):
                Lower bound of the experiment ids. If id_sup is None, requires
                the exact experiment id.
            id_sup (int, optional):
                Upper bound of the experiment ids. Defaults to None.
            **kwargs:
                Additional filter conditions for the query.

        Returns:
            Union[list, tuple]:
                Resulting ThermalEvent objects or columns based on the specified
                experiment ids.

        """
        query = self.get_by_columns(return_query=True, **kwargs)

        with session_scope() as session:
            query = query.with_session(session)

            if id_sup is None:
                query = query.filter_by(experiment_id=int(id_inf))
            else:
                query = query.filter(
                    ThermalEvent.experiment_id.between(int(id_inf), int(id_sup))
                )

            if "return_columns" in kwargs and isinstance(
                kwargs["return_columns"], list
            ):
                out = tuple(list(x) for x in zip(*query.all()))

                # Case then the result of the query is empty
                if len(out) == 0:
                    out = tuple([] for _ in range(len(kwargs["return_columns"])))

                if len(out) == 1:
                    out = out[0]
                return out
            return query.all()

    def get_by_experiment_id_line_of_sight(
        self, experiment_id: int, line_of_sight: str, **kwargs
    ):
        """Retrieve ThermalEvent objects based on experiment id and line of sight.

        Args:
            experiment_id (int):
                Experiment id to match.
            line_of_sight (str):
                Line of sight value to match.
            **kwargs:
                Additional filter conditions for the query.

        Returns:
            Union[list, tuple]:
                Resulting ThermalEvent objects or columns based on the specified
                experiment id and line of sight.

        """
        return self.get_by_columns(
            experiment_id=int(experiment_id), line_of_sight=line_of_sight, **kwargs
        )

    def get_by_device(self, device: str, **kwargs):
        """Retrieve ThermalEvent objects based on device name.

        Args:
            device (str):
                Device to match.
            **kwargs:
                Additional filter conditions for the query.

        Returns:
            Union[list, tuple]:
                Resulting ThermalEvent objects or columns based on the specified
                device.

        """
        return self.get_by_columns(device=device, **kwargs)

    def get_by_dataset(self, dataset: int, **kwargs):
        """Retrieve ThermalEvent objects based on dataset id.

        Args:
            dataset (int):
                Dataset id to match.
            **kwargs:
                Additional filter conditions for the query.

        Returns:
            Union[list, tuple]:
                Resulting ThermalEvent objects or columns based on the specified
                dataset id.

        """
        return self.get_by_columns(dataset=dataset, **kwargs)

    def get_parents_of_thermal_event(self, id: int, **kwargs):
        """Retrieve the parents of a thermal event, based on its id.

        Args:
            id (int):
                The id of the child thermal event.
            **kwargs:
                Additional filter conditions for the query.

        Returns:
            Union[list, tuple]:
                Resulting ThermalEvent parents or columns based on the specified
                child's id.

        """
        with session_scope() as session:
            ids = (
                session.query(ParentChildRelationship.parent).filter_by(child=id).all()
            )

            out = []
            for id in ids:
                out_id = self.get_by_columns(id=id[0], **kwargs)
                if len(out_id) == 1:
                    out_id = out_id[0]
                out.append(out_id)

            return out

    def get_children_of_thermal_event(self, id: int, **kwargs):
        """Retrieve the children of a thermal event, based on its id.

        Args:
            id (int):
                The id of the parent thermal event.
            **kwargs:
                Additional filter conditions for the query.

        Returns:
            Union[list, tuple]:
                Resulting ThermalEvent parents or columns based on the specified
                parent's id.

        """
        with session_scope() as session:
            ids = (
                session.query(ParentChildRelationship.child).filter_by(parent=id).all()
            )

            out = []
            for id in ids:
                out_id = self.get_by_columns(id=id[0], **kwargs)
                if len(out_id) == 1:
                    out_id = out_id[0]
                out.append(out_id)

            return out

    def change_analysis_status(self, event_id: int, new_status: str):
        """Change the analysis status of a ThermalEvent.

        Args:
            event_id (int):
                id of the ThermalEvent to update.
            new_status (str):
                New analysis status value.

        """
        with session_scope() as session:
            session.query(ThermalEvent).filter_by(id=event_id).update(
                {"analysis_status": new_status}
            )

    def change_severity(self, event_id: int, new_severity: str):
        """Change the severity of a ThermalEvent.

        Args:
            event_id (int):
                id of the ThermalEvent to update.
            new_severity (str):
                New severity value.

        """
        with session_scope() as session:
            session.query(ThermalEvent).filter_by(id=event_id).update(
                {"severity": new_severity}
            )

    def update(self, obj_in: Union[ThermalEvent, List[ThermalEvent]]) -> None:
        """Update an existing object or a list of ThermalEvent objects.

        Args:
            obj_in (Union[ThermalEvent, List[ThermalEvent]]): The object(s) to update.

        """

        if not isinstance(obj_in, list):
            obj_in = [obj_in]

        with session_scope() as session:
            for obj in obj_in:
                if len(obj.instances) == 0:
                    session.delete(obj)
                else:
                    session.merge(obj)

    def delete(self, events: Union[list, ThermalEvent, int]):
        """Delete ThermalEvent objects from the database.

        Args:
            events (Union[list, ThermalEvent, int]):
                List of ThermalEvent objects, single ThermalEvent object, or id(s) of
                ThermalEvent(s) to delete.

        """
        if not isinstance(events, list):
            events = [events]

        with session_scope() as session:
            for event in events:
                if isinstance(event, ThermalEvent):
                    event = event.id

                session.query(ThermalEvent).filter_by(id=event).delete()


thermal_event = CRUDThermalEvent(ThermalEvent)
