"""
Integration tests against the real Poetry dataset.

These tests only run when the actual dataset is available. Point the
ENPM611_PROJECT_DATA_PATH environment variable at the downloaded
`poetry_issues.json` (or place it at `data/poetry_issues.json`) to enable
them; otherwise they are skipped with an explanatory message.
"""

import os

import pytest

import config
import data_loader
from data_loader import DataLoader
import issue_resolution_analysis as f1
import contributor_activity_analysis as f2
import discussion_trends_analysis as f3


def _resolve_dataset_path():
    """Return a usable dataset path, or None if the dataset is not present."""
    candidates = []
    env_path = os.environ.get('ENPM611_PROJECT_DATA_PATH')
    if env_path:
        candidates.append(env_path)
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates.append(os.path.join(here, 'data', 'poetry_issues.json'))
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None


@pytest.fixture
def real_dataset():
    path = _resolve_dataset_path()
    if path is None:
        pytest.skip(
            'Real Poetry dataset not found. Set ENPM611_PROJECT_DATA_PATH or '
            'place the file at data/poetry_issues.json to run integration '
            'tests.')
    os.environ['ENPM611_PROJECT_DATA_PATH'] = path
    data_loader._ISSUES = None
    config._config = None
    return path


def test_dataset_loads(real_dataset):
    issues = DataLoader().get_issues()
    assert len(issues) > 0
    # Spot-check that the model populated the expected fields.
    assert any(issue.labels for issue in issues)
    assert any(issue.events for issue in issues)


def test_all_features_run_on_real_data(real_dataset, chart_dir):
    f1.IssueResolutionAnalysis().run()
    f2.ContributorActivityAnalysis().run()
    f3.DiscussionTrendsAnalysis().run()
    produced = list(chart_dir.glob('*.png'))
    # Each project-level feature should have produced at least one chart.
    assert len(produced) >= 3
