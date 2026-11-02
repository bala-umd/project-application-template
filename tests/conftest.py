"""
Shared pytest fixtures and helpers for the ENPM611 project test suite.

The application relies on a couple of module-level singletons (the loaded
issue list in data_loader and the parsed config in config) and on environment
variables for configuration. The autouse fixtures below reset that state
between tests so each test runs in isolation and never shows a chart window.
"""

import os
# Force a non-interactive matplotlib backend before pyplot is imported anywhere
# so chart generation works headlessly and never blocks on plt.show().
os.environ.setdefault('MPLBACKEND', 'Agg')

import json
import matplotlib
matplotlib.use('Agg')

import pytest

import config
import data_loader
from model import Issue


# Environment variables the application reads; cleaned up between tests.
_MANAGED_ENV_KEYS = [
    'ENPM611_PROJECT_DATA_PATH',
    'ENPM611_CHART_OUTPUT_DIR',
    'feature',
    'user',
    'label',
]


@pytest.fixture(autouse=True)
def _reset_state():
    """Reset singletons and managed environment variables around each test."""
    saved = {k: os.environ.get(k) for k in _MANAGED_ENV_KEYS}
    for k in _MANAGED_ENV_KEYS:
        os.environ.pop(k, None)
    data_loader._ISSUES = None
    config._config = None

    yield

    data_loader._ISSUES = None
    config._config = None
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def make_issue_dict(**overrides):
    """
    Build a JSON-like issue dict with sensible defaults. Override any field
    via keyword arguments, e.g. make_issue_dict(state='open', labels=['x']).
    """
    issue = {
        'url': 'https://example.com/issues/1',
        'creator': 'alice',
        'labels': ['kind/bug'],
        'state': 'closed',
        'assignees': [],
        'title': 'Sample issue',
        'text': 'Body text',
        'number': 1,
        'created_date': '2024-01-01T00:00:00+00:00',
        'updated_date': '2024-01-03T00:00:00+00:00',
        'timeline_url': 'https://example.com/issues/1/timeline',
        'events': [],
    }
    issue.update(overrides)
    return issue


def make_event(event_type, author=None, event_date=None, label=None, comment=None):
    """Build a JSON-like event dict."""
    return {
        'event_type': event_type,
        'author': author,
        'event_date': event_date,
        'label': label,
        'comment': comment,
    }


@pytest.fixture
def sample_issue_dicts():
    """
    A small, controlled dataset exercising the main code paths:
      - #1 closed bug, created 2024-01-01, closed 2024-01-03 (2 days), 2 comments
      - #2 closed bug, closed event 10 days after creation, 1 comment
      - #3 open feature, no close, 3 comments
      - #4 closed docs, no 'closed' event -> falls back to updated_date (5 days)
    """
    return [
        make_issue_dict(
            number=1, creator='alice', labels=['kind/bug'], state='closed',
            created_date='2024-01-01T00:00:00+00:00',
            updated_date='2024-01-03T00:00:00+00:00',
            events=[
                make_event('commented', 'bob', '2024-01-01T06:00:00+00:00'),
                make_event('commented', 'carol', '2024-01-02T06:00:00+00:00'),
                make_event('closed', 'alice', '2024-01-03T00:00:00+00:00'),
            ],
        ),
        make_issue_dict(
            number=2, creator='bob', labels=['kind/bug'], state='closed',
            created_date='2024-02-01T00:00:00+00:00',
            updated_date='2024-02-20T00:00:00+00:00',
            events=[
                make_event('commented', 'alice', '2024-02-02T00:00:00+00:00'),
                make_event('closed', 'bob', '2024-02-11T00:00:00+00:00'),
            ],
        ),
        make_issue_dict(
            number=3, creator='carol', labels=['kind/feature'], state='open',
            created_date='2024-03-01T00:00:00+00:00',
            updated_date='2024-03-10T00:00:00+00:00',
            events=[
                make_event('commented', 'alice', '2024-03-02T00:00:00+00:00'),
                make_event('commented', 'bob', '2024-03-03T00:00:00+00:00'),
                make_event('commented', 'alice', '2024-03-04T00:00:00+00:00'),
                make_event('labeled', 'carol', '2024-03-01T00:00:00+00:00',
                           label='kind/feature'),
            ],
        ),
        make_issue_dict(
            number=4, creator='alice', labels=['area/docs'], state='closed',
            created_date='2024-04-01T00:00:00+00:00',
            updated_date='2024-04-06T00:00:00+00:00',
            events=[
                make_event('commented', 'dave', '2024-04-02T00:00:00+00:00'),
            ],
        ),
    ]


@pytest.fixture
def sample_issues(sample_issue_dicts):
    """The sample dataset as parsed Issue objects."""
    return [Issue(d) for d in sample_issue_dicts]


@pytest.fixture
def data_file(tmp_path, sample_issue_dicts):
    """Write the sample dataset to a temp JSON file and point config at it."""
    path = tmp_path / 'issues.json'
    path.write_text(json.dumps(sample_issue_dicts))
    os.environ['ENPM611_PROJECT_DATA_PATH'] = str(path)
    return str(path)


@pytest.fixture
def chart_dir(tmp_path):
    """A temp directory charts are saved to, wired via the env var."""
    out = tmp_path / 'charts'
    os.environ['ENPM611_CHART_OUTPUT_DIR'] = str(out)
    return out
