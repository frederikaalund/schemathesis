import json
import tarfile
from contextlib import contextmanager
from io import BytesIO

import attr

import schemathesis
from schemathesis.service.metadata import Metadata
from schemathesis.service.report import ReportWriter


@contextmanager
def read_report(data):
    buffer = BytesIO()
    buffer.write(data)
    buffer.seek(0)
    with tarfile.open(mode="r:gz", fileobj=buffer) as tar:
        yield tar


def test_add_events(openapi3_schema_url):
    schema = schemathesis.from_uri(openapi3_schema_url, validate_schema=False)
    payload = BytesIO()
    with tarfile.open(mode="w:gz", fileobj=payload) as tar:
        report = ReportWriter(tar)
        for event in schemathesis.runner.from_schema(schema).execute():
            report.add_event(event)
    data = payload.getvalue()
    with read_report(data) as tar:
        members = tar.getmembers()
        assert len(members) == 6
        expected = (
            "Initialized",
            "BeforeExecution",
            "AfterExecution",
            "BeforeExecution",
            "AfterExecution",
            "Finished",
        )
        for event_type, member in zip(expected, members):
            event = json.load(tar.extractfile(member.name))
            assert event_type in event


def test_metadata():
    payload = BytesIO()
    with tarfile.open(mode="w:gz", fileobj=payload) as tar:
        report = ReportWriter(tar)
        metadata = Metadata()
        report.add_metadata(
            api_name="test", location="http://127.0.0.1", base_url="http://127.0.0.1", metadata=metadata
        )
    data = payload.getvalue()
    with read_report(data) as tar:
        assert len(tar.getmembers()) == 1
        assert attr.asdict(metadata) == json.load(tar.extractfile("metadata.json"))["environment"]
