import random
import shutil
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
    StrikeLineDescriptor,
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
    severity_types,
    users,
)

from .test_thermal_event import random_event as _random_event
from .test_strike_line_descriptor import random_strike_line_descriptor

# Number of different datasets
NB_DATASETS = 3

# Random matrix encoding the compatibility between the lines of sights and the
# thermal event categories
rows = len(lines_of_sight)
cols = len(categories)
COMPATIBILITY = np.random.randint(0, 2, size=(rows, cols), dtype=bool)
row_sums = COMPATIBILITY.sum(axis=1)
row_indices = np.where(row_sums == 0)
COMPATIBILITY[row_indices, np.random.randint(0, cols, len(row_indices))] = True


def random_event(*args):
    return _random_event(*args, COMPATIBILITY)


def create_genealogy():
    """Generate random thermal events, send them to the database and create a
        random genealogy between the thermal events

    Returns:
        list: The ids of the randomly created thermal events, sorted
        numpy.ndarray: A matrix that encodes the parent / child relationship
            between the thermal events. The rows correspond to parents and the
            columns to children, so that mat[i, j] == True indicates that
            thermal event i is a parent of thermal event j
    """
    thermal_events = []
    for _ in range(10):
        thermal_events.append(random_event(10))
    crud.thermal_event.create(thermal_events)

    ids = sorted([x.id for x in thermal_events])

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


@pytest.fixture(scope="session", autouse=True)
def create_and_delete_temporary_database():
    """Create an temporary SQLITE database at the beginning of the test session,
    with all the necessary tables and values, and delete the database file at the
    end of the session
    """
    users.append([crud.user._user_name(), "current_user@domain.org"])

    with get_db() as session:
        # Ensure we work with a test database before creating tables
        assert "test_database.sqlite" in str(session.bind.url)

        Base.metadata.create_all(session.bind)

        session.add_all([LineOfSight(name=x) for x in lines_of_sight])
        session.add_all([Device(name=x) for x in devices])
        session.add_all([Category(name=x) for x in categories])
        categories_lines_of_sight = []
        for ind_category, category in enumerate(categories):
            for ind_los, line_of_sight in enumerate(lines_of_sight):
                if not COMPATIBILITY[ind_los, ind_category]:
                    continue
                categories_lines_of_sight.append(
                    ThermalEventCategoryLineOfSight(
                        thermal_event_category=category, line_of_sight=line_of_sight
                    )
                )
        session.add_all(categories_lines_of_sight)
        session.add_all([Method(name=x) for x in methods])
        session.add_all([User(name=x[0], email=x[1]) for x in users])
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


@pytest.fixture(autouse=True)
def reset_temporary_database():
    """Reset the temporary database after each test by emptying the tables linked
    to the thermal events (thermal_events, thermal_events_instances,
    thermal_events_genealogy)
    """
    yield

    # Clear the database
    with get_db() as session:
        # Ensure we work with the test database before emptying tables
        assert "test_database.sqlite" in str(session.bind.url)

        session.query(ParentChildRelationship).delete()
        session.query(ThermalEvent).delete()
        session.query(StrikeLineDescriptor).delete()
        session.commit()


def test_thermal_event_create_read():
    # Generate a random thermal event
    expected = random_event(10)

    # Send the thermal event to the database
    crud.thermal_event.create(expected)

    # Read the thermal event from the database
    actual = crud.thermal_event.get(expected.id)

    assert expected.initial_timestamp_ns == actual.initial_timestamp_ns
    assert expected.final_timestamp_ns == actual.final_timestamp_ns
    assert expected.duration_ns == actual.duration_ns
    assert expected.max_temperature_C == actual.max_temperature_C
    assert len(expected.instances) == len(actual.instances)


def test_thermal_event_get_multi():
    # Generate random thermal events
    nb = 5
    thermal_events = [random_event(10) for _ in range(nb)]

    # Send the thermal events to the database
    crud.thermal_event.create(thermal_events)

    # Store their ids
    expected = [x.id for x in thermal_events]

    # Retrieve the thermal events and their ids
    thermal_events_read = crud.thermal_event.get_multi(limit=nb)
    actual = [x.id for x in thermal_events_read]

    assert actual == expected


def test_thermal_event_update():
    # Generate a random thermal event
    thermal_event = random_event(10)

    # Send the thermal event to the database
    crud.thermal_event.create(thermal_event)

    # Update its method with a different, randomly chosen one
    expected = random.choice([m for m in methods if m != thermal_event.method])
    thermal_event.method = expected
    crud.thermal_event.update(thermal_event)

    # Retrieve the event and check if its method has been updated
    thermal_event_db = crud.thermal_event.get(thermal_event.id)

    assert thermal_event_db.method == expected

    # Delete the event through an update by emptying its instances
    thermal_event_db.instances = []
    crud.thermal_event.update(thermal_event_db)

    assert crud.thermal_event.get(thermal_event_db.id) is None


def test_thermal_event_delete():
    # Generate a random thermal event
    thermal_event = random_event(10)

    # Send the thermal event to the database
    crud.thermal_event.create(thermal_event)

    # Delete the event and check it is deleted in the database
    crud.thermal_event.delete(thermal_event)

    assert crud.thermal_event.get(thermal_event.id) is None


def test_thermal_event_get_by_columns():
    # Generate a random thermal event with specific values for some attributes
    thermal_event = random_event(10)

    line_of_sight = random.choice(lines_of_sight)
    category = random.choice(
        list(
            compress(categories, COMPATIBILITY[lines_of_sight.index(line_of_sight), :])
        )
    )

    thermal_event.user = users[0][0]
    thermal_event.experiment_id = 123
    thermal_event.method = methods[0]
    thermal_event.line_of_sight = line_of_sight
    thermal_event.category = category

    # Send the thermal event to the database
    crud.thermal_event.create(thermal_event)

    events = crud.thermal_event.get_by_columns(user=users[0][0])
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
        dataset="1", line_of_sight=line_of_sight, category=category
    )
    assert len(events) == 1


def test_thermal_event_get_by_columns_exclude_time_intervals():
    # Generate random thermal events with different initial and final timestamps
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

    # Send the thermal events to the database
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
    # Create random thermal events with different experiment ids
    thermal_events = []
    for experiment_id in range(100, 140):
        thermal_events.append(random_event(10))
        thermal_events[-1].experiment_id = experiment_id

    # Send the thermal events to the database
    crud.thermal_event.create(thermal_events)

    expected = [x.id for x in thermal_events if x.experiment_id == 100]
    actual = crud.thermal_event.get_by_experiment_id(100, return_columns=["id"])
    assert actual == expected

    expected = [x.id for x in thermal_events if 120 <= x.experiment_id <= 130]
    events = crud.thermal_event.get_by_experiment_id(120, 130)
    actual = [x.id for x in events]
    assert actual == expected


def test_thermal_event_get_by_experiment_id_line_of_sight():
    # Create random thermal events with different experiment ids and lines of sight
    ids = [100, 101]
    id_counts = [random.randrange(1, 10) for _ in ids]

    thermal_events = []
    for ind, experiment_id in enumerate(ids):
        for _ in range(id_counts[ind]):
            thermal_event = random_event(10)
            thermal_event.experiment_id = experiment_id
            thermal_event.line_of_sight = lines_of_sight[0]
            category = random.choice(
                list(
                    compress(
                        categories,
                        COMPATIBILITY[
                            lines_of_sight.index(thermal_event.line_of_sight), :
                        ],
                    )
                )
            )
            thermal_event.category = category
            thermal_events.append(thermal_event)

    # Send the thermal events to the database
    crud.thermal_event.create(thermal_events)

    expected = [
        x.id
        for x in thermal_events
        if x.experiment_id == ids[0]
        if x.line_of_sight == lines_of_sight[0]
    ]
    actual = crud.thermal_event.get_by_experiment_id_line_of_sight(
        ids[0], lines_of_sight[0], return_columns=["id"]
    )
    assert actual == expected

    events = crud.thermal_event.get_by_experiment_id_line_of_sight(
        ids[1], lines_of_sight[1]
    )
    assert len(events) == 0


def test_thermal_event_get_by_device():
    # Generate random thermal events with different devices
    device_counts = [random.randrange(10) for _ in devices]

    thermal_events = []
    for ind, device in enumerate(devices):
        for _ in range(device_counts[ind]):
            thermal_events.append(random_event(10))
            thermal_events[-1].device = device

    # Send the thermal events to the database
    crud.thermal_event.create(thermal_events)

    for ind, device in enumerate(devices):
        expected = [x.id for x in thermal_events if x.device == device]
        actual = crud.thermal_event.get_by_device(device, return_columns=["id"])
        assert actual == expected


def test_thermal_event_get_by_dataset():
    # Generate random thermal events with different datasets
    datasets = ["1", "2", "3", "1, 2", "2, 3"]
    dataset_counts = [random.randrange(1, 10) for _ in datasets]

    thermal_events = []
    for ind, dataset in enumerate(datasets):
        for _ in range(dataset_counts[ind]):
            thermal_events.append(random_event(10))
            thermal_events[-1].dataset = dataset

    # Send the thermal events to the database
    crud.thermal_event.create(thermal_events)

    for ind, dataset in enumerate(datasets):
        expected = [x.id for x in thermal_events if dataset in x.dataset]

        actual = crud.thermal_event.get_by_dataset(dataset, return_columns=["id"])
        assert sorted(actual) == sorted(expected)


def test_thermal_event_get_parents_of_thermal_event():
    # Create random thermal events with random parent/child relationships
    ids, mat = create_genealogy()

    for ind, id in enumerate(ids):
        parents = crud.thermal_event.get_parents_of_thermal_event(id)
        expected = list(compress(ids, mat[:, ind]))
        actual = [x.id for x in parents]

        assert actual == expected


def test_thermal_event_get_children_of_thermal_event():
    # Create random thermal events with random parent/child relationships
    ids, mat = create_genealogy()

    for ind, id in enumerate(ids):
        children = crud.thermal_event.get_children_of_thermal_event(id)
        actual = [x.id for x in children]
        expected = list(compress(ids, mat[ind, :]))

        assert actual == expected


def test_thermal_event_change_analysis_status():
    # Create a random thermal event
    thermal_event = random_event(10)

    # Send the thermal event to the database
    crud.thermal_event.create(thermal_event)

    # Change the status with a random one
    expected = random.choice(
        [m for m in analysis_status if m != thermal_event.analysis_status]
    )
    crud.thermal_event.change_analysis_status(thermal_event.id, expected)

    actual = crud.thermal_event.get_by_columns(
        id=thermal_event.id, return_columns=["analysis_status"]
    )[0]

    assert actual == expected


def test_strike_line_descriptor_create_read():
    # Generate a random strike line descriptor
    expected = random_strike_line_descriptor()

    # Send the descriptor to the database
    crud.strike_line_descriptor.create(expected)

    # Read the descriptor from the database
    actual = crud.strike_line_descriptor.get(expected.id)

    assert actual.instance.bbox_x == expected.instance.bbox_x
    assert actual.instance.bbox_y == expected.instance.bbox_y
    assert actual.instance.bbox_width == expected.instance.bbox_width
    assert actual.instance.bbox_height == expected.instance.bbox_height
    assert actual.instance.timestamp_ns == expected.instance.timestamp_ns

    assert actual.segmented_points_as_list == expected.segmented_points_as_list
    assert actual.angle == expected.angle
    assert actual.curve == expected.curve
    assert actual.flag_RT == expected.flag_RT


def test_strike_line_descriptor_get_multi():
    # Generate random descriptors
    nb = 5
    descriptors = [random_strike_line_descriptor() for _ in range(nb)]

    # Send the descriprots to the database
    crud.strike_line_descriptor.create(descriptors)

    # Store their ids
    expected = [x.id for x in descriptors]

    # Retrieve the descriptors and their ids
    descriptors_read = crud.strike_line_descriptor.get_multi(limit=nb)
    actual = [x.id for x in descriptors_read]

    assert actual == expected


def test_strike_line_descriptor_update():
    # Generate a random descriptor
    descriptor = random_strike_line_descriptor()

    # Send the descriptor to the database
    crud.strike_line_descriptor.create(descriptor)

    # Update its angle with a different, randomly chosen one
    expected = random.randrange(90)
    descriptor.angle = expected
    crud.strike_line_descriptor.update(descriptor)

    # Retrieve the descriptor and check if its angle has been updated
    descriptor_db = crud.strike_line_descriptor.get(descriptor.id)

    assert descriptor_db.angle == expected


def test_strike_line_descriptor_delete():
    # Generate a random descriptor
    descriptor = random_strike_line_descriptor()

    # Send the descriptor to the database
    crud.strike_line_descriptor.create(descriptor)

    # Delete the descriptor and check it is deleted in the database
    crud.strike_line_descriptor.delete(descriptor)

    assert crud.strike_line_descriptor.get(descriptor.id) is None


def test_strike_line_descriptor_get_by_columns():
    # Generate a random descriptor
    (
        descriptor,
        instance,
        segmented_points,
        angle,
        curve,
        flag_RT,
    ) = random_strike_line_descriptor(return_parameters=True)

    # Send the descriptor to the database
    crud.strike_line_descriptor.create(descriptor)

    # Query with the angle
    actual = crud.strike_line_descriptor.get_by_columns(angle=angle)
    assert len(actual) == 1

    # Query with the curve
    actual = crud.strike_line_descriptor.get_by_columns(curve=curve + 1)
    assert len(actual) == 0
    actual = crud.strike_line_descriptor.get_by_columns(
        curve=curve, return_columns=["id"]
    )
    assert len(actual) == 1

    # Query with both angle and curve
    actual = crud.strike_line_descriptor.get_by_columns(angle=angle, curve=curve)
    assert len(actual) == 1


def test_strike_line_descriptor_get_by_flag_RT():
    # Generate a random descriptor
    descriptor = random_strike_line_descriptor()
    descriptor.flag_RT = True

    # Send the descriptor to the database
    crud.strike_line_descriptor.create(descriptor)

    # Query the descriptors with flag_RT == True
    actual = crud.strike_line_descriptor.get_by_flag_RT(True)
    assert len(actual) == 1

    # Query the descriptors with flag_RT == False
    actual = crud.strike_line_descriptor.get_by_flag_RT(False)
    assert len(actual) == 0


def test_user():
    # Check the users list
    assert crud.user.list() == sorted([x[0] for x in users], key=lambda s: s.lower())

    # Check that the current user has read and write rights
    assert crud.user.has_read_rights()
    assert crud.user.has_write_rights()

    # Check that the user's email address is correctly retrieved
    assert crud.user.email_address(users[0][0]) == users[0][1]
    assert crud.user.email_address(crud.user._user_name()) == users[-1][1]
    assert crud.user.email_address("fake user") is None


def test_thermal_event_category():
    # Check the categories list
    assert crud.thermal_event_category.list() == categories

    # Check the compatibilities between lines of sight and thermal event categories
    for ind, category in enumerate(categories):
        expected = list(compress(lines_of_sight, COMPATIBILITY[:, ind]))
        actual = crud.thermal_event_category.compatible_lines_of_sight(category)
        assert actual == expected


def test_dataset():
    # Check the number of datasets
    assert len(crud.dataset.list()) == NB_DATASETS


def test_analysis_status():
    # Check the analysis status list
    assert crud.analysis_status.list() == analysis_status


def test_line_of_sight():
    # Check the lines of sight list
    assert crud.line_of_sight.list() == lines_of_sight


def test_method():
    # Check the methods list
    assert crud.method.list() == methods


def test_device():
    # Check the devices list
    assert crud.device.list() == devices


def test_severity():
    # Check the severity types list
    assert crud.severity.list() == severity_types
