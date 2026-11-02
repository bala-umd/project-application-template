"""Tests for Feature 1: Issue Resolution Analysis."""

import os

import pytest

from model import Issue
from conftest import make_issue_dict, make_event
import issue_resolution_analysis as f1
from issue_resolution_analysis import (
    resolution_days,
    collect_resolution_times,
    summary_stats,
    median_resolution_by_label,
    IssueResolutionAnalysis,
)


# ---- resolution_days -------------------------------------------------------

def test_resolution_days_uses_closed_event(sample_issues):
    # Issue #1: created 2024-01-01, closed event 2024-01-03 -> 2 days.
    issue1 = next(i for i in sample_issues if i.number == 1)
    assert resolution_days(issue1) == pytest.approx(2.0)


def test_resolution_days_falls_back_to_updated_date(sample_issues):
    # Issue #4 is closed but has no 'closed' event -> uses updated_date (5 days).
    issue4 = next(i for i in sample_issues if i.number == 4)
    assert resolution_days(issue4) == pytest.approx(5.0)


def test_resolution_days_none_for_open_issue(sample_issues):
    issue3 = next(i for i in sample_issues if i.number == 3)
    assert resolution_days(issue3) is None


def test_resolution_days_none_without_created_date():
    issue = Issue(make_issue_dict(created_date=None, state='closed'))
    assert resolution_days(issue) is None


def test_resolution_days_rejects_negative_duration():
    # Close date precedes creation date -> inconsistent data, returns None.
    issue = Issue(make_issue_dict(
        created_date='2024-05-10T00:00:00+00:00',
        state='closed',
        events=[make_event('closed', 'alice', '2024-05-01T00:00:00+00:00')],
    ))
    assert resolution_days(issue) is None


# ---- collect_resolution_times & summary_stats ------------------------------

def test_collect_filters_by_label(sample_issues):
    pairs = collect_resolution_times(sample_issues, label='kind/bug')
    numbers = sorted(issue.number for issue, _ in pairs)
    assert numbers == [1, 2]  # only closed bug issues with computable time


def test_collect_without_label_includes_all_resolved(sample_issues):
    pairs = collect_resolution_times(sample_issues)
    # #1, #2, #4 are resolved; #3 is open.
    assert sorted(issue.number for issue, _ in pairs) == [1, 2, 4]


def test_summary_stats_values(sample_issues):
    pairs = collect_resolution_times(sample_issues, label='kind/bug')
    stats = summary_stats([days for _, days in pairs])
    assert stats['count'] == 2
    assert stats['min'] == pytest.approx(2.0)
    assert stats['max'] == pytest.approx(10.0)
    assert stats['median'] == pytest.approx(6.0)


def test_summary_stats_empty():
    assert summary_stats([]) == {}


# ---- median_resolution_by_label --------------------------------------------

def test_median_resolution_by_label(sample_issues):
    summary = median_resolution_by_label(sample_issues)
    as_dict = {label: median for label, median, _ in summary}
    assert as_dict['kind/bug'] == pytest.approx(6.0)
    assert as_dict['area/docs'] == pytest.approx(5.0)
    # The open-only 'kind/feature' label has no resolved issues.
    assert 'kind/feature' not in as_dict
    # Sorted shortest median first.
    assert summary[0][0] == 'area/docs'


# ---- run() chart generation & edge cases -----------------------------------

def test_run_without_label_generates_chart(data_file, chart_dir):
    IssueResolutionAnalysis().run()
    assert (chart_dir / 'feature1_median_by_label.png').exists()


def test_run_with_label_generates_chart(data_file, chart_dir):
    os.environ['label'] = 'kind/bug'
    IssueResolutionAnalysis().run()
    assert (chart_dir / 'feature1_resolution_distribution.png').exists()


def test_run_with_unknown_label_no_chart(data_file, chart_dir, capsys):
    os.environ['label'] = 'nonexistent/label'
    IssueResolutionAnalysis().run()
    out = capsys.readouterr().out
    assert 'No closed issues' in out
    assert not (chart_dir / 'feature1_resolution_distribution.png').exists()


def test_empty_dataset_handled(tmp_path, chart_dir, capsys, monkeypatch):
    # No resolved issues -> friendly message, no crash, no chart.
    monkeypatch.setattr(f1.DataLoader, 'get_issues', lambda self: [])
    IssueResolutionAnalysis().run()
    out = capsys.readouterr().out
    assert 'No closed issues' in out
