"""
Feature 2: Contributor Activity Analysis.

Question answered:
    Who are the most active contributors on the project, and what does the
    activity of a specific contributor look like?

Method:
    Every event in the dataset carries an author. The analysis aggregates
    events per author and breaks them down by event type (commenting,
    labeling, closing, and so on). When a specific contributor is supplied
    (--user), the analysis reports that person's activity profile. When no
    contributor is supplied, it ranks the most active contributors and shows
    how their activity is composed, which is a project-level insight.

Input (optional):
    --user <name>    Focus the analysis on a single contributor.
"""

import os
from collections import Counter
from typing import List, Optional, Dict, Tuple

import matplotlib.pyplot as plt

import config
from data_loader import DataLoader
from model import Issue


# Number of contributors to show in the project-level ranking.
TOP_CONTRIBUTORS: int = 15
# Event types highlighted as their own series in the stacked chart; everything
# else is grouped under 'other'.
HIGHLIGHT_EVENT_TYPES: Tuple[str, ...] = ('commented', 'labeled', 'closed')


def total_events_by_author(issues: List[Issue]) -> Counter:
    """Count the total number of events authored by each contributor."""
    counts: Counter = Counter()
    for issue in issues:
        for event in issue.events:
            if event.author:
                counts[event.author] += 1
    return counts


def event_breakdown_by_author(issues: List[Issue]) -> Dict[str, Counter]:
    """
    For each contributor, count how many events of each type they authored.
    Returns a mapping author -> Counter(event_type -> count).
    """
    breakdown: Dict[str, Counter] = {}
    for issue in issues:
        for event in issue.events:
            if event.author:
                breakdown.setdefault(event.author, Counter())[
                    event.event_type or 'unknown'
                ] += 1
    return breakdown


def user_activity(issues: List[Issue], user: str) -> Dict[str, object]:
    """
    Summarize a single contributor's activity: total events, a per-type
    breakdown, how many issues they opened, and how many distinct issues they
    participated in.
    """
    per_type: Counter = Counter()
    issues_created = 0
    issues_touched = set()
    for issue in issues:
        if issue.creator == user:
            issues_created += 1
        for event in issue.events:
            if event.author == user:
                per_type[event.event_type or 'unknown'] += 1
                issues_touched.add(issue.number)
    return {
        'total_events': sum(per_type.values()),
        'per_type': per_type,
        'issues_created': issues_created,
        'issues_participated': len(issues_touched),
    }


def _categorize(counter: Counter) -> Dict[str, int]:
    """Collapse an event-type counter into the highlighted series + 'other'."""
    categorized = {etype: counter.get(etype, 0) for etype in HIGHLIGHT_EVENT_TYPES}
    categorized['other'] = sum(
        count for etype, count in counter.items()
        if etype not in HIGHLIGHT_EVENT_TYPES
    )
    return categorized


class ContributorActivityAnalysis:
    """
    Analyzes contributor activity, overall and for a specific contributor.
    """

    def __init__(self):
        """Constructor: read the optional --user parameter from config."""
        self.USER: Optional[str] = config.get_parameter('user')

    def run(self):
        """Starting point for this analysis."""
        issues: List[Issue] = DataLoader().get_issues()

        print('\n=== Feature 2: Contributor Activity Analysis ===')
        print('Question: Who are the most active contributors, and what does '
              'their activity consist of?')

        if self.USER:
            self._analyze_single_user(issues, self.USER)
        else:
            self._analyze_all_contributors(issues)

    def _analyze_single_user(self, issues: List[Issue], user: str):
        """Report one contributor's activity profile plus a chart."""
        print(f'Method: Aggregating every event authored by "{user}" and '
              f'grouping it by event type.')
        activity = user_activity(issues, user)

        if activity['total_events'] == 0 and activity['issues_created'] == 0:
            print(f'Finding: No activity was found for contributor "{user}".')
            return

        per_type: Counter = activity['per_type']
        print(f'\nActivity profile for "{user}":')
        print(f'  Issues opened:        {activity["issues_created"]}')
        print(f'  Issues participated:  {activity["issues_participated"]}')
        print(f'  Total events:         {activity["total_events"]}')
        print('  Events by type:')
        for etype, count in per_type.most_common():
            print(f'    {etype:<18}{count:>6}')

        top_type = per_type.most_common(1)[0] if per_type else ('none', 0)
        print(f'Finding: "{user}" is most active through "{top_type[0]}" '
              f'events ({top_type[1]} of {activity["total_events"]}).')

        if not per_type:
            return
        types = [etype for etype, _ in per_type.most_common()]
        counts = [count for _, count in per_type.most_common()]
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(types, counts, color='#55A868')
        ax.set_title(f'Activity breakdown for contributor "{user}"')
        ax.set_xlabel('Event type')
        ax.set_ylabel('Number of events')
        plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
        self._finish_chart(fig, 'feature2_user_activity.png')

    def _analyze_all_contributors(self, issues: List[Issue]):
        """Rank the most active contributors with a stacked activity chart."""
        print('Method: Ranking contributors by total events and showing how '
              'each one\'s activity is composed.')
        totals = total_events_by_author(issues)

        if not totals:
            print('Finding: No contributor activity was found in the dataset.')
            return

        top = totals.most_common(TOP_CONTRIBUTORS)
        breakdown = event_breakdown_by_author(issues)

        print(f'\nTop {len(top)} contributors by total events:')
        print(f'  {"Contributor":<22}{"Events":>8}')
        for author, count in top:
            print(f'  {author:<22}{count:>8}')

        leader = top[0]
        print(f'Finding: "{leader[0]}" is the most active contributor with '
              f'{leader[1]} events across the project.')

        authors = [author for author, _ in top]
        categories = list(HIGHLIGHT_EVENT_TYPES) + ['other']
        colors = ['#4C72B0', '#DD8452', '#C44E52', '#8C8C8C']
        series = {
            cat: [_categorize(breakdown[author])[cat] for author in authors]
            for cat in categories
        }

        fig, ax = plt.subplots(figsize=(12, 7))
        bottom = [0] * len(authors)
        for cat, color in zip(categories, colors):
            ax.bar(authors, series[cat], bottom=bottom, label=cat, color=color)
            bottom = [b + v for b, v in zip(bottom, series[cat])]
        ax.set_title(f'Activity composition of the top {len(authors)} '
                     f'contributors')
        ax.set_xlabel('Contributor')
        ax.set_ylabel('Number of events')
        ax.legend(title='Event type')
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        self._finish_chart(fig, 'feature2_top_contributors.png')

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
    ContributorActivityAnalysis().run()
