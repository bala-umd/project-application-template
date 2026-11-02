"""
Feature 3: Discussion Trends Analysis.

Question answered:
    How has discussion activity on the project's issues changed over time, and
    which categories of issues attract the most discussion?

Method:
    Comment events carry a timestamp, so the analysis buckets every 'commented'
    event by calendar month to build a time series of discussion volume. It
    also measures discussion intensity (comments per issue) overall and per
    label. This is a project-level insight that requires no user input.

Input:
    None. This analysis always reports on the whole project.
"""

import os
from collections import Counter
from typing import List, Optional, Dict, Tuple

import matplotlib.pyplot as plt

import config
from data_loader import DataLoader
from model import Issue


# Number of labels to compare for discussion intensity.
TOP_LABELS: int = 10
# Minimum issues a label must have to be ranked by average discussion, so a
# single very noisy issue does not dominate the ranking.
MIN_ISSUES_PER_LABEL: int = 3


def comment_count(issue: Issue) -> int:
    """Return how many 'commented' events an issue has."""
    return sum(1 for event in issue.events if event.event_type == 'commented')


def comments_per_month(issues: List[Issue]) -> List[Tuple[str, int]]:
    """
    Bucket every dated 'commented' event by calendar month.
    Returns a chronologically sorted list of ('YYYY-MM', count) pairs.
    """
    buckets: Counter = Counter()
    for issue in issues:
        for event in issue.events:
            if event.event_type == 'commented' and event.event_date is not None:
                buckets[event.event_date.strftime('%Y-%m')] += 1
    return sorted(buckets.items())


def discussion_by_label(
    issues: List[Issue], top_n: int = TOP_LABELS
) -> List[Tuple[str, float, int]]:
    """
    For labels used on at least MIN_ISSUES_PER_LABEL issues, compute the
    average number of comments per issue. Returns a list of
    (label, avg_comments, issue_count) sorted by average descending.
    """
    totals: Dict[str, int] = {}
    counts: Dict[str, int] = {}
    for issue in issues:
        comments = comment_count(issue)
        for label in issue.labels:
            totals[label] = totals.get(label, 0) + comments
            counts[label] = counts.get(label, 0) + 1

    averages = [
        (label, totals[label] / counts[label], counts[label])
        for label in totals
        if counts[label] >= MIN_ISSUES_PER_LABEL
    ]
    averages.sort(key=lambda item: (-item[1], item[0]))
    return averages[:top_n]


def overall_stats(issues: List[Issue]) -> Dict[str, object]:
    """Compute overall discussion statistics across all issues."""
    comments = [comment_count(issue) for issue in issues]
    total = sum(comments)
    most_discussed = max(
        issues, key=comment_count, default=None
    ) if issues else None
    return {
        'total_comments': total,
        'issue_count': len(issues),
        'avg_comments': (total / len(issues)) if issues else 0.0,
        'most_discussed': most_discussed,
    }


class DiscussionTrendsAnalysis:
    """
    Analyzes how issue discussion volume evolves over time and by label.
    """

    def __init__(self):
        """Constructor. This analysis takes no user input."""
        pass

    def run(self):
        """Starting point for this analysis."""
        issues: List[Issue] = DataLoader().get_issues()

        print('\n=== Feature 3: Discussion Trends Analysis ===')
        print('Question: How has discussion volume changed over time, and '
              'which labels attract the most discussion?')
        print('Method: Bucketing comment events by month and measuring '
              'comments per issue overall and by label.')

        stats = overall_stats(issues)
        if stats['issue_count'] == 0 or stats['total_comments'] == 0:
            print('Finding: The dataset contains no comment activity to '
                  'analyze.')
            return

        print(f'\nTotal comments:           {stats["total_comments"]}')
        print(f'Issues analyzed:          {stats["issue_count"]}')
        print(f'Average comments/issue:   {stats["avg_comments"]:.2f}')
        most = stats['most_discussed']
        if most is not None:
            print(f'Most discussed issue:     #{most.number} '
                  f'({comment_count(most)} comments) - {most.title}')

        self._report_label_intensity(issues)
        monthly = comments_per_month(issues)
        self._report_timeline(monthly)
        self._plot_timeline(monthly)

    def _report_label_intensity(self, issues: List[Issue]):
        """Print the labels with the highest average discussion."""
        ranked = discussion_by_label(issues)
        if not ranked:
            return
        print('\nAverage comments per issue, by label (most discussed first):')
        print(f'  {"Label":<28}{"Avg comments":>14}{"Issues":>9}')
        for label, avg, count in ranked:
            print(f'  {label:<28}{avg:>14.2f}{count:>9}')
        print(f'Finding: "{ranked[0][0]}" issues generate the most discussion '
              f'(avg {ranked[0][1]:.2f} comments per issue).')

    def _report_timeline(self, monthly: List[Tuple[str, int]]):
        """Print the busiest discussion month."""
        if not monthly:
            return
        busiest = max(monthly, key=lambda item: item[1])
        print(f'\nDiscussion spans {monthly[0][0]} to {monthly[-1][0]}; '
              f'busiest month was {busiest[0]} with {busiest[1]} comments.')

    def _plot_timeline(self, monthly: List[Tuple[str, int]]):
        """Plot comments per month as a time series."""
        if not monthly:
            return
        months = [month for month, _ in monthly]
        values = [count for _, count in monthly]

        fig, ax = plt.subplots(figsize=(13, 6))
        ax.plot(months, values, marker='o', color='#4C72B0')
        ax.fill_between(range(len(months)), values, alpha=0.1, color='#4C72B0')
        ax.set_title('Issue discussion volume over time')
        ax.set_xlabel('Month')
        ax.set_ylabel('Number of comments')
        # Show a readable subset of month labels when there are many.
        step = max(1, len(months) // 15)
        ax.set_xticks(range(0, len(months), step))
        ax.set_xticklabels(months[::step], rotation=45, ha='right')
        self._finish_chart(fig, 'feature3_discussion_timeline.png')

    def _finish_chart(self, fig, filename: str) -> Optional[str]:
        """
        Show the chart interactively (default) or save it to the directory
        named by ENPM611_CHART_OUTPUT_DIR for headless and tested runs.
        """
        output_dir = config.get_parameter('ENPM611_CHART_OUTPUT_DIR')
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            path = os.path.join(output_dir, filename)
            fig.savefig(path, bbox_inches='tight')
            plt.close(fig)
            print(f'Chart saved to {path}')
            return path
        plt.show()
        return None


if __name__ == '__main__':
    DiscussionTrendsAnalysis().run()
