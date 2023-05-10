from typing import Union

from sqlalchemy import and_, not_, or_

from thermal_events import ThermalEvent
from thermal_events.crud.base import CRUDBase, session_scope


class CRUDThermalEvent(CRUDBase[ThermalEvent]):
    def get_by_columns(
        self,
        return_columns: Union[list, None] = None,
        return_query: bool = False,
        **kwargs,
    ):
        with session_scope() as session:
            if isinstance(return_columns, list):
                query = session.query(
                    *[getattr(ThermalEvent, x) for x in return_columns]
                )
            else:
                query = session.query(ThermalEvent)

            if "pulse" in kwargs:
                kwargs["pulse"] = float(kwargs["pulse"])

            if "dataset" in kwargs:
                dataset = kwargs.pop("dataset")
                if isinstance(dataset, list):
                    cond = ()
                    for dat in dataset:
                        cond += (ThermalEvent.dataset.like(f"%{dat}%"),)
                    query = query.filter(or_(*cond))
                else:
                    query = query.filter(ThermalEvent.dataset.like(f"%{dataset}%"))

            if "method" in kwargs:
                method = kwargs.pop("method")
                query = query.filter(ThermalEvent.method.like(f"%{method}%"))

            if "line_of_sight" in kwargs:
                line_of_sight = kwargs.pop("line_of_sight")
                query = query.filter(
                    ThermalEvent.line_of_sight.like(f"%{line_of_sight}%")
                )

            if "thermal_event" in kwargs:
                event = kwargs.pop("thermal_event")
                query = query.filter(ThermalEvent.thermal_event.like(f"%{event}%"))

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
                    conds.append(ThermalEvent.initial_timestamp > inf)
                if sup is not None:
                    conds.append(ThermalEvent.final_timestamp < sup)

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

    def get_by_pulse(self, pulse_inf: float, pulse_sup: float = None, **kwargs):
        query = self.get_by_columns(return_query=True, **kwargs)

        with session_scope() as session:
            query = query.with_session(session)

            if pulse_sup is None:
                query = query.filter_by(pulse=float(pulse_inf))
            else:
                query = query.filter(
                    ThermalEvent.pulse.between(float(pulse_inf), float(pulse_sup))
                )

            if "return_columns" in kwargs and kwargs["return_columns"] != []:
                return [list(x) for x in zip(*query.all())]
            return query.all()

    def get_by_pulse_line_of_sight(self, pulse: float, line_of_sight: str, **kwargs):
        return self.get_by_columns(
            pulse=float(pulse), line_of_sight=line_of_sight, **kwargs
        )

    def get_by_dataset(self, dataset: int, **kwargs):
        return self.get_by_columns(dataset=dataset, **kwargs)

    def change_analysis_status(self, event_id: int, new_status: str):
        with session_scope() as session:
            session.query(ThermalEvent).filter_by(id=event_id).update(
                {"analysis_status": new_status}
            )
            session.commit()

    def delete(self, events: Union[list, ThermalEvent, int]):
        if not isinstance(events, list):
            events = [events]

        with session_scope() as session:
            for event in events:
                if isinstance(event, ThermalEvent):
                    event = event.id

                session.query(ThermalEvent).filter_by(id=event).delete()
            session.commit()


thermal_event = CRUDThermalEvent(ThermalEvent)
