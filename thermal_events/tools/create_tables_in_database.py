from datetime import datetime

from thermal_events import (
    Base,
    LineOfSight,
    ThermalEventType,
    Device,
    User,
    Dataset,
    AnalysisStatus,
    ThermalEventTypeLineOfSight,
)
from thermal_events.database import get_db

with get_db() as session:
    # Create the tables
    Base.metadata.create_all(session.bind)

    # Create content of table devices
    session.add_all(
        [
            Device(name=name)
            for name in [
                "device 1",
                "device 2",
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

    # Create content of table lines_of_sight
    lines_of_sight = [
        "line of sight 1",
        "line of sight 2",
    ]
    session.add_all([LineOfSight(name=name) for name in lines_of_sight])

    # Create content of table thermal_event_types
    thermal_event_types = [
        "thermal event 1",
        "thermal event 2",
        "thermal event 3",
    ]
    session.add_all([ThermalEventType(name=name) for name in thermal_event_types])

    # Compatibility matrix (line of sight, thermal event type)
    compat = [
        [1, 1, 0],
        [1, 0, 1],
    ]

    # Create content of table thermal_event_type_lines_of_sight
    thermal_event_type_lines_of_sight = []
    for ind_los, compat_los in enumerate(compat):
        for ind_type, flag in enumerate(compat_los):
            if not flag:
                continue
            thermal_event_type_lines_of_sight.append(
                ThermalEventTypeLineOfSight(
                    thermal_event_type=thermal_event_types[ind_type],
                    line_of_sight=lines_of_sight[ind_los],
                ),
            )
    session.add_all(thermal_event_type_lines_of_sight)

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
                description="A thermal event that has been analyzed, and does "
                + "not need follow-up analysis",
            ),
            AnalysisStatus(
                name="Analyzed (follow-up required)",
                description="A thermal event that has been analyzed, but which "
                + "requires follow-up analysis",
            ),
            AnalysisStatus(
                name="Detection Error",
                description="A false positive, a detection which is not a "
                + "thermal event",
            ),
            AnalysisStatus(
                name="Detection Problem",
                description="A thermal event which is detected, but not properly "
                + "encompassed, classified and/or tracked",
            ),
        ]
    )
    session.commit()
