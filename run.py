"""
Starting point of the application. This module is invoked from
the command line to run the analyses.

Usage:
    python run.py --feature 0 [--user <name>]     Example analysis (template)
    python run.py --feature 1 [--label <name>]    Issue Resolution Analysis
    python run.py --feature 2 [--user <name>]     Contributor Activity Analysis
    python run.py --feature 3                      Discussion Trends Analysis
"""

import argparse

import config
from example_analysis import ExampleAnalysis
from issue_resolution_analysis import IssueResolutionAnalysis
from contributor_activity_analysis import ContributorActivityAnalysis
from discussion_trends_analysis import DiscussionTrendsAnalysis


def parse_args():
    """
    Parses the command line arguments that were provided along
    with the python command. The --feature flag must be provided as
    that determines what analysis to run. Optionally, you can pass in
    a user and/or a label to run analysis focusing on specific issues.

    You can also add more command line arguments following the pattern
    below.
    """
    ap = argparse.ArgumentParser("run.py")

    # Required parameter specifying what analysis to run
    ap.add_argument('--feature', '-f', type=int, required=True,
                    help='Which of the features to run: 0 (example), '
                         '1 (issue resolution), 2 (contributor activity), '
                         '3 (discussion trends)')

    # Optional parameter for analyses focusing on a specific user (i.e., contributor)
    ap.add_argument('--user', '-u', type=str, required=False,
                    help='Optional parameter for analyses focusing on a specific user')

    # Optional parameter for analyses focusing on a specific label
    ap.add_argument('--label', '-l', type=str, required=False,
                    help='Optional parameter for analyses focusing on a specific label')

    return ap.parse_args()


# Maps the --feature value to the analysis class that implements it.
FEATURES = {
    0: ExampleAnalysis,
    1: IssueResolutionAnalysis,
    2: ContributorActivityAnalysis,
    3: DiscussionTrendsAnalysis,
}


def main():
    """Parse arguments, store them in config, and run the chosen feature."""
    args = parse_args()
    # Add arguments to config so that they can be accessed in other parts
    # of the application.
    config.overwrite_from_args(args)

    analysis_class = FEATURES.get(args.feature)
    if analysis_class is None:
        valid = ', '.join(str(key) for key in sorted(FEATURES))
        print(f'Unknown feature {args.feature}. '
              f'Specify one of: {valid} with the --feature flag.')
        return

    analysis_class().run()


if __name__ == '__main__':
    main()
