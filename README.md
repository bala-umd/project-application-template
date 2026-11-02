# ENPM611 Project: Poetry GitHub Issue Analysis (Team 8)

This application analyzes GitHub issue activity from the
[Poetry](https://github.com/python-poetry/poetry/issues) open-source project
and produces insights about how issues are resolved, who contributes, and how
discussion evolves over time. It extends the ENPM611 application template with
three analyses that are selected from the command line with the `--feature`
flag.

Repository: https://github.com/bala-umd/project-application-template

## Team 8 Members

- Bala Sreerangam
- Asa Constantian
- Jaden James

## Features

The application exposes four analyses. Feature 0 is the original template
example; features 1-3 are the team's analyses.

### Feature 1: Issue Resolution Analysis (`issue_resolution_analysis.py`)

- **Question:** How long do issues take to resolve, and does the resolution
  time differ by label?
- **Input (optional):** `--label <name>` to focus on one label.
- **Method:** For each closed issue the resolution time is computed as the gap
  between the creation date and the `closed` event date (falling back to the
  last update date when no dated close event exists). Durations are aggregated
  into summary statistics. With no label, it compares the median resolution
  time across the most common labels (a project-level insight); with a label,
  it shows that label's resolution-time distribution.
- **Output:** A console summary (count, median, mean, fastest, slowest) and a
  Matplotlib chart (a per-label bar chart, or a distribution histogram).

### Feature 2: Contributor Activity Analysis (`contributor_activity_analysis.py`)

- **Question:** Who are the most active contributors, and what does a specific
  contributor's activity look like?
- **Input (optional):** `--user <name>` to focus on one contributor.
- **Method:** Events are aggregated per author and broken down by event type
  (commenting, labeling, closing, and so on). With no user, it ranks the top
  contributors and shows the composition of their activity (a project-level
  insight); with a user, it reports that person's activity profile.
- **Output:** A console ranking or profile and a Matplotlib chart (a stacked
  bar chart of the top contributors, or a per-type bar chart for one user).

### Feature 3: Discussion Trends Analysis (`discussion_trends_analysis.py`)

- **Question:** How has discussion volume changed over time, and which labels
  attract the most discussion?
- **Input:** None. This is a project-level analysis.
- **Method:** Comment events are bucketed by calendar month to build a time
  series, and discussion intensity (comments per issue) is measured overall
  and per label.
- **Output:** A console summary (totals, average comments per issue, most
  discussed issue and label) and a Matplotlib line chart of comments per month.

Collectively the three analyses satisfy the assignment requirements: at least
one accepts user input (features 1 and 2), at least one gives a project-level
insight (feature 3, and the default modes of 1 and 2), all three produce
charts, and each states the question it answers, the method, and the finding.

## Prerequisites

- **Python 3.9 or newer** (developed and tested on Python 3.13).
- The dependencies listed in `requirements.txt`: `python-dateutil`, `pandas`,
  and `matplotlib`.

## Environment Setup

From the root of the project, create and activate a virtual environment:

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

To also install the testing tools (`pytest`, `pytest-cov`):

```bash
pip install -r requirements-dev.txt
```

## Dataset Configuration

Download the prepared `poetry_issues.json` dataset from the project assignment
in Canvas. The dataset is **not** committed to the repository. Configure its
location in one of two ways:

1. **Relative path (default):** place the file at `data/poetry_issues.json`.
   `config.json` already points there:

   ```json
   { "ENPM611_PROJECT_DATA_PATH": "data/poetry_issues.json" }
   ```

2. **Environment variable (recommended, avoids committing a personal path):**

   ```bash
   # macOS / Linux
   export ENPM611_PROJECT_DATA_PATH=/full/path/to/poetry_issues.json

   # Windows (PowerShell)
   $env:ENPM611_PROJECT_DATA_PATH = "C:\full\path\to\poetry_issues.json"
   ```

   The environment variable takes precedence over `config.json`.

## Running the Analyses

Each feature is run through the `--feature` flag:

```bash
python run.py --feature 1     # Issue Resolution Analysis
python run.py --feature 2     # Contributor Activity Analysis
python run.py --feature 3     # Discussion Trends Analysis
python run.py --feature 0     # Original template example analysis
```

### Example commands with optional arguments

```bash
# Resolution time for a specific label
python run.py --feature 1 --label "kind/bug"

# Activity profile for a specific contributor
python run.py --feature 2 --user "dimbleby"

# Project-level discussion trends (no arguments)
python run.py --feature 3
```

### Expected output

Each feature prints its question, method, and finding to the console and then
opens a Matplotlib chart window. For example, `--feature 1` (no label) prints a
table of median resolution time per label and displays a bar chart; a typical
finding is that `status/triage` issues resolve fastest while
`status/needs-reproduction` issues take the longest.

**Headless or saved charts.** By default charts are shown in a window
(`plt.show()`). To run without a display or to save charts to disk instead,
set `ENPM611_CHART_OUTPUT_DIR`; each chart is then written there as a PNG:

```bash
export ENPM611_CHART_OUTPUT_DIR=charts
python run.py --feature 3
# -> charts/feature3_discussion_timeline.png
```

## Running the Tests

Install the dev dependencies, then run the suite from the project root:

```bash
pip install -r requirements-dev.txt
pytest
```

Run with a statement-coverage report:

```bash
pytest --cov=. --cov-report=term-missing
```

The unit tests use small controlled fixtures and do not require the dataset.
Two integration tests exercise the real dataset; they run automatically when
`poetry_issues.json` is available (via `ENPM611_PROJECT_DATA_PATH` or at
`data/poetry_issues.json`) and are skipped with an explanatory message
otherwise.

## Project Structure

```
project-root/
├── run.py                              # Entry point; dispatches on --feature
├── config.py                           # Loads config.json / env variables
├── config.json                         # Dataset path configuration
├── model.py                            # Issue and Event data model
├── data_loader.py                      # Loads issues from the JSON dataset
├── example_analysis.py                 # Template example (feature 0)
├── issue_resolution_analysis.py        # Feature 1
├── contributor_activity_analysis.py    # Feature 2
├── discussion_trends_analysis.py       # Feature 3
├── requirements.txt                    # Application dependencies
├── requirements-dev.txt                # Testing dependencies
├── pytest.ini                          # Test configuration
├── .coveragerc                         # Coverage configuration
├── README.md
├── data/                               # Dataset location (git-ignored)
└── tests/                              # Automated test suite
    ├── conftest.py                     # Fixtures and shared helpers
    ├── test_model.py
    ├── test_config.py
    ├── test_data_loader.py
    ├── test_issue_resolution_analysis.py
    ├── test_contributor_activity_analysis.py
    ├── test_discussion_trends_analysis.py
    ├── test_run.py
    └── test_integration_dataset.py
```

## Known Limitations and Assumptions

- **Resolution time** relies on the latest dated `closed` event; when a closed
  issue has no dated close event, the last `updated_date` is used as an
  approximation. Issues whose close date precedes their creation date are
  treated as having no computable resolution time.
- Analyses operate on the provided snapshot of issues. Findings describe that
  snapshot and are not predictions.
- A contributor is identified by the exact author string in the dataset,
  including bot accounts such as `github-actions[bot]`; these are not filtered
  out.
- Feature 3 ranks a label by average discussion only when it appears on at
  least three issues, so a single very active issue does not dominate.
- Charts are shown interactively by default; set `ENPM611_CHART_OUTPUT_DIR` to
  run in a headless environment.

## Team Contributions

Each member contributed to at least two project phases. Areas of contribution:

| Member | Primary areas |
| --- | --- |
| Bala Sreerangam | Repository setup, Feature 1 (Issue Resolution Analysis), README |
| Asa Constantian | Feature 2 (Contributor Activity Analysis), component and sequence diagrams |
| Jaden James | Feature 3 (Discussion Trends Analysis), test suite and coverage |

> Note: update this table to match the team's final division of work before
> submission.
