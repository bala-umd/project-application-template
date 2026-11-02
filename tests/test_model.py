"""Tests for the model module (Issue and Event parsing)."""

from datetime import datetime

from model import Issue, Event, State
from conftest import make_issue_dict, make_event


def test_issue_parses_core_fields():
    issue = Issue(make_issue_dict(number=42, creator='alice', state='closed'))
    assert issue.number == 42
    assert issue.creator == 'alice'
    assert issue.state == State.closed
    assert isinstance(issue.created_date, datetime)
    assert issue.labels == ['kind/bug']


def test_issue_parses_events():
    issue = Issue(make_issue_dict(events=[
        make_event('commented', 'bob', '2024-01-01T00:00:00+00:00'),
        make_event('closed', 'alice', '2024-01-02T00:00:00+00:00'),
    ]))
    assert len(issue.events) == 2
    assert issue.events[0].event_type == 'commented'
    assert issue.events[0].author == 'bob'
    assert isinstance(issue.events[1].event_date, datetime)


def test_issue_missing_state_does_not_crash():
    # Defensive parsing: a missing state should load as None, not raise.
    issue = Issue(make_issue_dict(state=None))
    assert issue.state is None


def test_issue_unknown_state_does_not_crash():
    issue = Issue(make_issue_dict(state='archived'))
    assert issue.state is None


def test_issue_invalid_dates_are_none():
    issue = Issue(make_issue_dict(
        created_date='not-a-date', updated_date=None))
    assert issue.created_date is None
    assert issue.updated_date is None


def test_event_missing_date_is_none():
    event = Event(make_event('commented', 'bob', event_date=None))
    assert event.event_date is None
    assert event.comment is None


def test_empty_issue_has_defaults():
    issue = Issue()
    assert issue.number == -1
    assert issue.events == []
    assert issue.labels == []
