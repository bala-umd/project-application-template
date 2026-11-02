"""Tests for Feature 2: Contributor Activity Analysis."""

import os

import contributor_activity_analysis as f2
from contributor_activity_analysis import (
    total_events_by_author,
    event_breakdown_by_author,
    user_activity,
    _categorize,
    ContributorActivityAnalysis,
    HIGHLIGHT_EVENT_TYPES,
)
from collections import Counter


def test_total_events_by_author(sample_issues):
    totals = total_events_by_author(sample_issues)
    # alice authors: closed(#1), commented(#2), commented x2(#3) = 4
    assert totals['alice'] == 4
    assert totals['bob'] == 3
    assert totals['carol'] == 2
    assert totals['dave'] == 1


def test_event_breakdown_by_author(sample_issues):
    breakdown = event_breakdown_by_author(sample_issues)
    assert breakdown['alice']['commented'] == 3
    assert breakdown['alice']['closed'] == 1


def test_user_activity_profile(sample_issues):
    activity = user_activity(sample_issues, 'alice')
    assert activity['total_events'] == 4
    assert activity['issues_created'] == 2       # issues #1 and #4
    assert activity['issues_participated'] == 3   # touched #1, #2, #3
    assert activity['per_type']['commented'] == 3


def test_user_activity_unknown_user(sample_issues):
    activity = user_activity(sample_issues, 'nobody')
    assert activity['total_events'] == 0
    assert activity['issues_created'] == 0


def test_categorize_groups_other():
    counter = Counter({'commented': 5, 'labeled': 2, 'closed': 1,
                       'subscribed': 4, 'mentioned': 3})
    categorized = _categorize(counter)
    for etype in HIGHLIGHT_EVENT_TYPES:
        assert etype in categorized
    assert categorized['other'] == 7  # subscribed + mentioned


def test_run_without_user_generates_chart(data_file, chart_dir):
    ContributorActivityAnalysis().run()
    assert (chart_dir / 'feature2_top_contributors.png').exists()


def test_run_with_user_generates_chart(data_file, chart_dir):
    os.environ['user'] = 'alice'
    ContributorActivityAnalysis().run()
    assert (chart_dir / 'feature2_user_activity.png').exists()


def test_run_with_unknown_user_no_chart(data_file, chart_dir, capsys):
    os.environ['user'] = 'nobody'
    ContributorActivityAnalysis().run()
    out = capsys.readouterr().out
    assert 'No activity' in out
    assert not (chart_dir / 'feature2_user_activity.png').exists()


def test_empty_dataset_handled(chart_dir, capsys, monkeypatch):
    monkeypatch.setattr(f2.DataLoader, 'get_issues', lambda self: [])
    ContributorActivityAnalysis().run()
    out = capsys.readouterr().out
    assert 'No contributor activity' in out
