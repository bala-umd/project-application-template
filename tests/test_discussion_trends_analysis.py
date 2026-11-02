"""Tests for Feature 3: Discussion Trends Analysis."""

from model import Issue
from conftest import make_issue_dict, make_event
import discussion_trends_analysis as f3
from discussion_trends_analysis import (
    comment_count,
    comments_per_month,
    discussion_by_label,
    overall_stats,
    DiscussionTrendsAnalysis,
)


def test_comment_count(sample_issues):
    counts = {i.number: comment_count(i) for i in sample_issues}
    assert counts == {1: 2, 2: 1, 3: 3, 4: 1}


def test_comments_per_month(sample_issues):
    series = comments_per_month(sample_issues)
    assert series == [
        ('2024-01', 2),
        ('2024-02', 1),
        ('2024-03', 3),
        ('2024-04', 1),
    ]


def test_comments_per_month_ignores_undated_events():
    issue = Issue(make_issue_dict(events=[
        make_event('commented', 'bob', event_date=None),
        make_event('commented', 'bob', '2024-01-05T00:00:00+00:00'),
    ]))
    assert comments_per_month([issue]) == [('2024-01', 1)]


def test_overall_stats(sample_issues):
    stats = overall_stats(sample_issues)
    assert stats['total_comments'] == 7
    assert stats['issue_count'] == 4
    assert stats['avg_comments'] == 7 / 4
    assert stats['most_discussed'].number == 3  # 3 comments


def test_discussion_by_label_respects_minimum():
    # Three issues sharing a label, with 2, 4 and 6 comments -> avg 4.0.
    issues = []
    for n, c in [(1, 2), (2, 4), (3, 6)]:
        events = [make_event('commented', 'u', '2024-01-01T00:00:00+00:00')
                  for _ in range(c)]
        issues.append(Issue(make_issue_dict(
            number=n, labels=['area/solver'], events=events)))
    ranked = discussion_by_label(issues)
    as_dict = {label: avg for label, avg, _ in ranked}
    assert as_dict['area/solver'] == 4.0


def test_discussion_by_label_empty_on_small_sample(sample_issues):
    # No label in the sample reaches MIN_ISSUES_PER_LABEL issues.
    assert discussion_by_label(sample_issues) == []


def test_run_generates_chart(data_file, chart_dir):
    DiscussionTrendsAnalysis().run()
    assert (chart_dir / 'feature3_discussion_timeline.png').exists()


def test_run_empty_dataset_handled(chart_dir, capsys, monkeypatch):
    monkeypatch.setattr(f3.DataLoader, 'get_issues', lambda self: [])
    DiscussionTrendsAnalysis().run()
    out = capsys.readouterr().out
    assert 'no comment activity' in out.lower()
