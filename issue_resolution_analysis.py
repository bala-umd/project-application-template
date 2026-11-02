"""
Feature 1: Issue Resolution Analysis.

Question answered:
    How long do issues take to get resolved, and does the resolution time
    differ depending on the label attached to the issue?

Method:
    For every closed issue, the resolution time is computed as the difference
    between the issue's creation date and the date of its 'closed' event
    (falling back to the last update when no dated close event exists). The
    durations are then aggregated into summary statistics. When a specific
    label is supplied (--label), the analysis focuses on that label and shows
    the distribution of resolution times. When no label is supplied, it
    compares the median resolution time across the most common labels, which
    is a project-level insight.

Input (optional):
    --label <name>   Restrict the analysis to issues carrying this label.
"""

import os
import statistics
from typing import List, Optional, Tuple, Dict

import matplotlib.pyplot as plt

import config
from data_loader import DataLoader
from model import Issue, State


# Number of labels to compare in the project-level (no-label) view.
TOP_LABELS: int = 12
# Seconds in a day, used to convert timedeltas to a human-friendly unit.
_SECONDS_PER_DAY: float = 86400.0


def resolution_days(issue: Issue) -> Optional[float]:
    """
    Return the number of days it took to resolve an issue, or None when the
    resolution time cannot be determined (issue is not closed, or the dates
    required for the calculation are missing).
    """
    if issue.state != State.closed or issue.created_date is None:
        return None

    # Prefer the date of the (latest) 'closed' event.
    closed_dates = [
        event.event_date
        for event in issue.events
        if event.event_type == 'closed' and event.event_date is not None
    ]
    end_date = max(closed_dates) if closed_dates else issue.updated_date
    if end_date is None:
        return None

    delta = (end_date - issue.created_date).total_seconds() / _SECONDS_PER_DAY
    # Guard against inconsistent data where the close predates creation.
    return delta if delta >= 0 else None


def collect_resolution_times(
    issues: List[Issue], label: Optional[str] = None
) -> List[Tuple[Issue, float]]:
    """
    Return (issue, resolution_days) pairs for every closed issue whose
    resolution time can be computed. When a label is given, only issues
    carrying that label are included.
    """
    results: List[Tuple[Issue, float]] = []
    for issue in issues:
        if label is not None and label not in issue.labels:
            continue
        days = resolution_days(issue)
        if days is not None:
            results.append((issue, days))
    return results


def summary_stats(durations: List[float]) -> Dict[str, float]:
    """
    Compute summary statistics for a list of resolution-time durations.
    Returns an empty dict when there is no data.
    """
    if not durations:
        return {}
    return {
        'count': len(durations),
        'median': statistics.median(durations),
        'mean': statistics.mean(durations),
        'min': min(durations),
        'max': max(durations),
    }


def median_resolution_by_label(
    issues: List[Issue], top_n: int = TOP_LABELS
) -> List[Tuple[str, float, int]]:
    """
    For the most frequently used labels, compute the median resolution time.
    Returns a list of (label, median_days, issue_count) sorted by median
    resolution time ascending. This is the project-level insight.
    """
    per_label: Dict[str, List[float]] = {}
    for issue in issues:
        days = resolution_days(issue)
        if days is None:
            continue
        for label in issue.labels:
            per_label.setdefault(label, []).append(days)

    # Keep the labels that appear on the most resolved issues.
    ranked_by_volume = sorted(
        per_label.items(), key=lambda item: (-len(item[1]), item[0])
    )[:top_n]

    summary = [
        (label, statistics.median(values), len(values))
        for label, values in ranked_by_volume
    ]
    # Present shortest-to-longest median resolution time.
    summary.sort(key=lambda item: (item[1], item[0]))
    return summary


class IssueResolutionAnalysis:
    """
    Analyzes how long issues take to resolve, overall and per label.
    """

    def __init__(self):
        """Constructor: read the optional --label parameter from config."""
        self.LABEL: Optional[str] = config.get_parameter('label')

    def run(self):
        """Starting point for this analysis."""
        issues: List[Issue] = DataLoader().get_issues()

        print('\n=== Feature 1: Issue Resolution Analysis ===')
        print('Question: How long do issues take to resolve, and does it '
              'vary by label?')

        if self.LABEL:
            self._analyze_single_label(issues, self.LABEL)
        else:
            self._analyze_all_labels(issues)

    def _analyze_single_label(self, issues: List[Issue], label: str):
        """Focus on a single label: stats plus a distribution chart."""
        print(f'Method: Measuring resolution time for closed issues labeled '
              f'"{label}".')
        pairs = collect_resolution_times(issues, label)
        durations = [days for _, days in pairs]
        stats = summary_stats(durations)

        if not stats:
            print(f'Finding: No closed issues labeled "{label}" have a '
                  f'computable resolution time.')
            return

        print(f'\nResolved issues labeled "{label}": {stats["count"]}')
        print(f'  Median resolution: {stats["median"]:.1f} days')
        print(f'  Mean resolution:   {stats["mean"]:.1f} days')
        print(f'  Fastest:           {stats["min"]:.1f} days')
        print(f'  Slowest:           {stats["max"]:.1f} days')
        print(f'Finding: Half of "{label}" issues are resolved within '
              f'{stats["median"]:.1f} days.')

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(durations, bins=20, color='#4C72B0', edgecolor='white')
        ax.axvline(stats['median'], color='#C44E52', linestyle='--',
                   label=f'Median = {stats["median"]:.1f} days')
        ax.set_title(f'Resolution-time distribution for "{label}" issues')
        ax.set_xlabel('Resolution time (days)')
        ax.set_ylabel('Number of issues')
        ax.legend()
        self._finish_chart(fig, 'feature1_resolution_distribution.png')

    def _analyze_all_labels(self, issues: List[Issue]):
        """Project-level view: compare median resolution across labels."""
        print('Method: Comparing the median resolution time across the most '
              'common labels.')
        summary = median_resolution_by_label(issues)

        if not summary:
            print('Finding: No closed issues have a computable resolution '
                  'time.')
            return

        print('\nMedian resolution time by label (shortest first):')
        print(f'  {"Label":<28}{"Median days":>12}{"Issues":>9}')
        for label, median_days, count in summary:
            print(f'  {label:<28}{median_days:>12.1f}{count:>9}')

        fastest = summary[0]
        slowest = summary[-1]
        print(f'Finding: "{fastest[0]}" issues are resolved fastest '
              f'(median {fastest[1]:.1f} days), while "{slowest[0]}" issues '
              f'take longest (median {slowest[1]:.1f} days).')

        labels = [row[0] for row in summary]
        medians = [row[1] for row in summary]
        fig, ax = plt.subplots(figsize=(12, 7))
        ax.barh(labels, medians, color='#4C72B0')
        ax.invert_yaxis()  # shortest median at the top
        ax.set_title('Median issue resolution time by label')
        ax.set_xlabel('Median resolution time (days)')
        ax.set_ylabel('Label')
        self._finish_chart(fig, 'feature1_median_by_label.png')

    def _finish_chart(self, fig, filename: str) -> Optional[str]:
        """
        Either show the chart interactively (default) or save it to the
        directory named by ENPM611_CHART_OUTPUT_DIR. Saving keeps the feature
        runnable in headless environments and makes chart generation testable.
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
    IssueResolutionAnalysis().run()
