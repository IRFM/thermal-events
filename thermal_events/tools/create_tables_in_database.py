from datetime import datetime

from thermal_events import (
    Base,
    LineOfSight,
    ThermalEventType,
    User,
    Dataset,
    AnalysisStatus,
    ThermalEventTypeLineOfSight,
)
from thermal_events.database import get_db

with get_db() as session:
    # Create the tables
    Base.metadata.create_all(session.bind)

    # Create content of table lines_of_sight
    session.add_all(
        [
            LineOfSight(name=name)
            for name in [
                "line of sight 1",
                "line of sight 2",
            ]
        ]
    )

    # Create content of table users
    session.add_all(
        [
            User(name=name)
            for name in [
                "user 1",
                "user 2",
            ]
        ]
    )

    # Create content of table thermal_event_types
    session.add_all(
        [
            ThermalEventType(name=name)
            for name in [
                "thermal event 1",
                "thermal event 2",
            ]
        ]
    )

    # Create content of table thermal_event_type_lines_of_sight
    session.add_all(
        [
            ThermalEventTypeLineOfSight(
                thermal_event_type="thermal event 1", line_of_sight="line of sight 1"
            ),
            ThermalEventTypeLineOfSight(
                thermal_event_type="thermal event 2", line_of_sight="line of sight 1"
            ),
            ThermalEventTypeLineOfSight(
                thermal_event_type="thermal event 1", line_of_sight="line of sight 2"
            ),
        ]
    )

    # Create content of table datasets
    session.add_all(
        [
            Dataset(
                creation_date=datetime(2000, 1, 1),
                annotation_type="all",
                description="Catch-all dataset",
            ),
        ]
    )

    # Create content of table analysis_status
    session.add_all(
        [
            AnalysisStatus(
                name="Not Analyzed", description="A thermal event not yet analyzed"
            ),
            AnalysisStatus(
                name="To Analyze", description="A thermal event that should be analyzed"
            ),
            AnalysisStatus(
                name="Analyzed (OK)",
                description="A thermal event that has been analyzed, and does not need follow-up analysis",
            ),
            AnalysisStatus(
                name="Analyzed (follow-up required)",
                description="A thermal event that has been analyzed, but which requires follow-up analysis",
            ),
            AnalysisStatus(
                name="Detection Error",
                description="A false positive, a detection which is not a thermal event",
            ),
            AnalysisStatus(
                name="Detection Problem",
                description="A thermal event which is detected, but not properly encompassed, classified and/or tracked",
            ),
        ]
    )
    session.commit()
