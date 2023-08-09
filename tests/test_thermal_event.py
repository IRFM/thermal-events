import random
from itertools import compress

import numpy as np

from thermal_events import ThermalEvent, ThermalEventInstance

lines_of_sight = [
    "line of sight 1",
    "line of sight 2",
]
devices = [
    "device 1",
    "device 2",
]
categories = [
    "thermal event 1",
    "thermal event 2",
    "thermal event 3",
]
methods = [
    "method 1",
    "method 2",
]
users = [
    "user 1",
    "user 2",
]
severity_types = [
    "severity type 1",
    "severity type 2",
]
analysis_status = [
    "analysis status 1",
    "analysis status 2",
]


def random_instance():
    # Generate a thermal event instance with random bounding box, timestamp and
    # maximum temperature
    rect = [
        random.randrange(100),
        random.randrange(100),
        random.randrange(50) + 1,
        random.randrange(50) + 1,
    ]
    timestamp_ns = random.randrange(10000)
    instance = ThermalEventInstance.from_rectangle(rect, timestamp_ns)
    instance.max_temperature_C = random.randrange(1000)

    return instance


def random_event(n_instances=10, compat=None):
    # Generate a thermal event with random attributes and instances
    if compat is None:
        compat = np.ones((len(lines_of_sight), len(categories)), dtype=bool)

    # Pick a couple (line_of_sight, category) compatible with the compatibility matrix
    line_of_sight = random.choice(lines_of_sight)
    category = random.choice(
        list(compress(categories, compat[lines_of_sight.index(line_of_sight), :]))
    )

    thermal_event = ThermalEvent(
        experiment_id=random.randrange(100000),
        line_of_sight=line_of_sight,
        device=random.choice(devices),
        category=category,
        is_automatic_detection=False,
        method=random.choice(methods),
        user=random.choice(users),
        severity=random.choice(severity_types),
        analysis_status=random.choice(analysis_status),
    )

    for _ in range(n_instances):
        thermal_event.add_instance(random_instance())

    if len(thermal_event.instances):
        thermal_event.compute()

    return thermal_event


def test_ordered_datasets():
    thermal_event = ThermalEvent(dataset=[5, 1, 3])

    assert thermal_event.dataset == "1, 3, 5"


def test_add_instance():
    thermal_event = ThermalEvent()
    thermal_event.add_instance(random_instance())

    assert len(thermal_event.instances) == 1
    assert isinstance(thermal_event.instances[0], ThermalEventInstance)


def test_to_from_json(tmp_path):
    json_path = tmp_path / "thermal_event.json"

    thermal_event_write = random_event(10)
    thermal_event_write.to_json(json_path)
    thermal_event_read = ThermalEvent.from_json(json_path)

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


def test_compute():
    thermal_event = random_event(10)

    min_timestamp = min([x.timestamp_ns for x in thermal_event.instances])
    max_timestamp = max([x.timestamp_ns for x in thermal_event.instances])
    assert thermal_event.initial_timestamp_ns == min_timestamp
    assert thermal_event.final_timestamp_ns == max_timestamp
    assert thermal_event.duration_ns == max_timestamp - min_timestamp

    max_ind = np.argmax([x.max_temperature_C for x in thermal_event.instances])
    assert (
        thermal_event.max_temperature_C
        == thermal_event.instances[max_ind].max_temperature_C
    )

    assert (
        thermal_event.max_T_timestamp_ns
        == thermal_event.instances[max_ind].timestamp_ns
    )


def test_timestamps():
    thermal_event = random_event(10)

    # The timestamps should be sorted
    timestamps_ns = sorted([x.timestamp_ns for x in thermal_event.instances])
    assert thermal_event.timestamps_ns == timestamps_ns
