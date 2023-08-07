import random
import shutil
from copy import deepcopy
from datetime import date
from itertools import compress

import numpy as np
import pytest

from thermal_events import (
    AnalysisStatus,
    Base,
    Category,
    Dataset,
    Device,
    LineOfSight,
    Method,
    ParentChildRelationship,
    Severity,
    ThermalEvent,
    ThermalEventCategoryLineOfSight,
    User,
    crud,
)
from thermal_events.database import get_db, temp_folder_path

from .test_thermal_event import (
    analysis_status,
    categories,
    devices,
    lines_of_sight,
    methods,
    random_event,
    severity_types,
    users,
)

NB_DATASETS = 3


def create_genealogy():
    thermal_events = []
    for _ in range(10):
        thermal_events.append(random_event(10))
    crud.thermal_event.create(thermal_events)

    with get_db() as session:
        ids = session.query(ThermalEvent.id).all()
    ids = sorted([id[0] for id in ids])

    mat = np.random.choice(a=[False, True], size=(len(ids), len(ids)))
    np.fill_diagonal(mat, 0)

    genealogy = []
    for i in range(len(ids)):
        for j in range(len(ids)):
            if not mat[i, j]:
                continue

            genealogy.append(
                ParentChildRelationship(
                    parent=ids[i], child=ids[j], timestamp_ns=random.randrange(100)
                )
            )

    with get_db() as session:
        session.add_all(genealogy)
        session.commit()

    return ids, mat


@pytest.fixture(autouse=True)
def reset_temporary_database():
    yield

    # Clear the database
    with get_db() as session:
        # Ensure we work with the test database before emptying tables
        assert "test_database.sqlite" in str(session.bind.url)

        session.query(ParentChildRelationship).delete()
        session.query(ThermalEvent).delete()
        session.commit()


@pytest.fixture(scope="session", autouse=True)
def create_and_delete_temporary_database():
    users.append(crud.user._user_name())

    with get_db() as session:
        # Ensure we work with a test database before creating tables
        assert "test_database.sqlite" in str(session.bind.url)

        Base.metadata.create_all(session.bind)

        session.add_all([LineOfSight(name=x) for x in lines_of_sight])
        session.add_all([Device(name=x) for x in devices])
        session.add_all([Category(name=x) for x in categories])
        categories_lines_of_sight = []
        for category in categories:
            for line_of_sight in lines_of_sight:
                categories_lines_of_sight.append(
                    ThermalEventCategoryLineOfSight(
                        thermal_event_category=category, line_of_sight=line_of_sight
                    )
                )
        session.add_all(categories_lines_of_sight)
        session.add_all([Method(name=x) for x in methods])
        session.add_all([User(name=x) for x in users])
        session.add_all([Severity(name=x) for x in severity_types])
        session.add_all([AnalysisStatus(name=x) for x in analysis_status])
        session.add_all(
            [
                Dataset(creation_date=date.today(), annotation_type="bbox")
                for _ in range(NB_DATASETS)
            ]
        )

        session.commit()

    yield

    # Delete the temporary folder
    shutil.rmtree(temp_folder_path)


def test_thermal_event_create_read():
    thermal_event = random_event(10)

    # Make a copy of the thermal event (the original one is destroyed during the upload)
    thermal_event_write = deepcopy(thermal_event)

    # Send the thermal event to the database
    crud.thermal_event.create(thermal_event)

    # Find the event's id
    with get_db() as session:
        id = session.query(ThermalEvent.id).order_by(ThermalEvent.id.desc()).first()[0]

    # Read the thermal event from the database
    thermal_event_read = crud.thermal_event.get(id)

    assert (
        thermal_event_write.initial_timestamp_ns
        == thermal_event_read.initial_timestamp_ns
    )
    assert (
        thermal_event_write.final_timestamp_ns == thermal_event_read.final_timestamp_ns
    )
    assert thermal_event_write.duration_ns == thermal_event_read.duration_ns
    assert thermal_event_write.max_temperature_C == thermal_event_read.max_temperature_C
    assert len(thermal_event_write.instances) == len(thermal_event_read.instances)


def test_thermal_event_get_multi():
    nb = 5
    thermal_events = [random_event(10) for _ in range(nb)]

    crud.thermal_event.create(thermal_events)

    with get_db() as session:
        ids = (
            session.query(ThermalEvent.id)
            .order_by(ThermalEvent.id.asc())
            .limit(nb)
            .all()
        )
        ids = sorted([x[0] for x in ids])

    thermal_events_read = crud.thermal_event.get_multi(limit=nb)

    assert [x.id for x in thermal_events_read] == ids


def test_thermal_event_update():
    thermal_event = random_event(10)

    # Send the thermal event to the database
    crud.thermal_event.create(thermal_event)

    # Update the event
    with get_db() as session:
        thermal_event = (
            session.query(ThermalEvent).order_by(ThermalEvent.id.desc()).first()
        )

    new_method = random.choice(methods)
    thermal_event.method = new_method
    crud.thermal_event.update(thermal_event)

    # Find the event's id
    with get_db() as session:
        thermal_event_read = (
            session.query(ThermalEvent).order_by(ThermalEvent.id.desc()).first()
        )

    assert thermal_event_read.method == new_method

    # Delete the event through an update
    thermal_event_read.instances = []
    crud.thermal_event.update(thermal_event_read)


def test_thermal_event_delete():
    thermal_event = random_event(10)

    # Send the thermal event to the database
    crud.thermal_event.create(thermal_event)

    # Find the event's id
    with get_db() as session:
        id = session.query(ThermalEvent.id).order_by(ThermalEvent.id.desc()).first()[0]

    # Delete the event
    crud.thermal_event.delete(id)

    assert crud.thermal_event.get(id) is None


def test_thermal_event_get_by_columns():
    thermal_event = random_event(10)

    thermal_event.user = users[0]
    thermal_event.experiment_id = 123
    thermal_event.method = methods[0]
    thermal_event.line_of_sight = lines_of_sight[0]
    thermal_event.category = categories[0]

    crud.thermal_event.create(thermal_event)

    events = crud.thermal_event.get_by_columns(user=users[0])
    assert len(events) == 1

    ids = crud.thermal_event.get_by_columns(experiment_id=123, return_columns=["id"])
    assert len(ids) == 1

    x, y = crud.thermal_event.get_by_columns(
        method=methods[0], return_columns=["experiment_id", "line_of_sight"]
    )
    assert len(x) == 1
    assert len(y) == 1

    ids = crud.thermal_event.get_by_columns(
        dataset=["xxx", "yyy"], return_columns=["id"]
    )
    assert len(ids) == 0

    events = crud.thermal_event.get_by_columns(
        dataset="1", line_of_sight=lines_of_sight[0], category=categories[0]
    )
    assert len(events) == 1


def test_thermal_event_get_by_columns_exclude_time_intervals():
    thermal_events = []
    thermal_events.append(random_event(10))
    thermal_events[-1].initial_timestamp_ns = 10
    thermal_events[-1].final_timestamp_ns = 20

    thermal_events.append(random_event(10))
    thermal_events[-1].initial_timestamp_ns = 15
    thermal_events[-1].final_timestamp_ns = 30

    thermal_events.append(random_event(10))
    thermal_events[-1].initial_timestamp_ns = 25
    thermal_events[-1].final_timestamp_ns = 50

    crud.thermal_event.create(thermal_events)

    events = crud.thermal_event.get_by_columns_exclude_time_intervals(
        dataset=1, time_intervals=[15, None], return_columns=["id"]
    )
    assert len(events) == 1

    events = crud.thermal_event.get_by_columns_exclude_time_intervals(
        dataset=1,
        time_intervals=[None, 25],
    )
    assert len(events) == 2

    events = crud.thermal_event.get_by_columns_exclude_time_intervals(
        dataset=1,
        time_intervals=[[None, 20], [25, 60]],
    )
    assert len(events) == 1


def test_thermal_event_get_by_experiment_id():
    thermal_events = []
    for experiment_id in range(100, 140):
        thermal_events.append(random_event(10))
        thermal_events[-1].experiment_id = experiment_id

    crud.thermal_event.create(thermal_events)

    id = crud.thermal_event.get_by_experiment_id(100, return_columns=["id"])
    assert len(id) == 1

    events = crud.thermal_event.get_by_experiment_id(120, 130)
    assert len(events) == 11


def test_thermal_event_get_by_experiment_id_line_of_sight():
    ids = [100, 101]
    id_counts = [random.randrange(10) for _ in ids]

    thermal_events = []
    for ind, experiment_id in enumerate(ids):
        for _ in range(id_counts[ind]):
            thermal_events.append(random_event(10))
            thermal_events[-1].experiment_id = experiment_id
            thermal_events[-1].line_of_sight = lines_of_sight[0]

    crud.thermal_event.create(thermal_events)

    id = crud.thermal_event.get_by_experiment_id_line_of_sight(
        ids[0], lines_of_sight[0], return_columns=["id"]
    )
    assert len(id) == id_counts[0]

    events = crud.thermal_event.get_by_experiment_id_line_of_sight(
        ids[1], lines_of_sight[1]
    )
    assert len(events) == 0


def test_thermal_event_get_by_device():
    device_counts = [random.randrange(10) for _ in devices]

    thermal_events = []
    for ind, device in enumerate(devices):
        for _ in range(device_counts[ind]):
            thermal_events.append(random_event(10))
            thermal_events[-1].device = device

    crud.thermal_event.create(thermal_events)

    for ind, device in enumerate(devices):
        ids = crud.thermal_event.get_by_device(device, return_columns=["id"])
        assert len(ids) == device_counts[ind]


def test_thermal_event_get_by_dataset():
    datasets = ["1", "2", "3", "1, 2", "2, 3"]
    dataset_counts = [random.randrange(1, 10) for _ in datasets]

    thermal_events = []
    for ind, dataset in enumerate(datasets):
        for _ in range(dataset_counts[ind]):
            thermal_events.append(random_event(10))
            thermal_events[-1].dataset = dataset

    crud.thermal_event.create(thermal_events)

    for ind, dataset in enumerate(datasets):
        ids = crud.thermal_event.get_by_dataset(dataset, return_columns=["id"])
        if len(dataset) == 1:
            # Compute the numbers of thermal events with the id in their dataset,
            # covering the case where an event belongs to multiple datasets
            expected = sum(
                [
                    dataset_counts[i]
                    for i in range(len(datasets))
                    if dataset in datasets[i]
                ]
            )
        else:
            expected = dataset_counts[ind]
        assert len(ids) == expected


def test_thermal_event_get_parents_of_thermal_event():
    ids, mat = create_genealogy()

    for ind, id in enumerate(ids):
        parents = crud.thermal_event.get_parents_of_thermal_event(id)
        actual = [x.id for x in parents]
        expected = list(compress(ids, mat[:, ind]))

        assert actual == expected


def test_thermal_event_get_children_of_thermal_event():
    ids, mat = create_genealogy()

    for ind, id in enumerate(ids):
        children = crud.thermal_event.get_children_of_thermal_event(id)
        actual = [x.id for x in children]
        expected = list(compress(ids, mat[ind, :]))

        assert actual == expected


def test_thermal_event_change_analysis_status():
    thermal_event = random_event(10)

    thermal_event.analysis_status = analysis_status[0]
    crud.thermal_event.create(thermal_event)

    # Find the event's id
    with get_db() as session:
        id = session.query(ThermalEvent.id).order_by(ThermalEvent.id.desc()).first()[0]

    expected = analysis_status[1]
    crud.thermal_event.change_analysis_status(id, expected)

    actual = crud.thermal_event.get_by_columns(
        id=id, return_columns=["analysis_status"]
    )[0]

    assert actual == expected


def test_user():
    assert crud.user.list() == sorted(users, key=lambda s: s.lower())

    assert crud.user.has_read_rights()
    assert crud.user.has_write_rights()


def test_thermal_event_category():
    assert crud.thermal_event_category.list() == categories

    los = crud.thermal_event_category.compatible_lines_of_sight(categories[0])
    assert los == lines_of_sight


def test_dataset():
    assert len(crud.dataset.list()) == NB_DATASETS


def test_analysis_status():
    assert crud.analysis_status.list() == analysis_status


def test_line_of_sight():
    assert crud.line_of_sight.list() == lines_of_sight


def test_method():
    assert crud.method.list() == methods


def test_device():
    assert crud.device.list() == devices


def test_severity():
    assert crud.severity.list() == severity_types
