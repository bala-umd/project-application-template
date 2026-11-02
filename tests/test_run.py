"""Tests for run.py: argument parsing and feature dispatch."""

import pytest

import run


def test_parse_args_reads_feature(monkeypatch):
    monkeypatch.setattr('sys.argv', ['run.py', '--feature', '2'])
    args = run.parse_args()
    assert args.feature == 2
    assert args.user is None


def test_parse_args_reads_optional_params(monkeypatch):
    monkeypatch.setattr(
        'sys.argv', ['run.py', '--feature', '1', '--label', 'kind/bug'])
    args = run.parse_args()
    assert args.feature == 1
    assert args.label == 'kind/bug'


def test_features_mapping_complete():
    # Every documented feature id is wired to an analysis class.
    assert set(run.FEATURES) == {0, 1, 2, 3}


@pytest.mark.parametrize('feature_id', [0, 1, 2, 3])
def test_main_dispatches_selected_feature(monkeypatch, feature_id):
    called = {}

    class DummyAnalysis:
        def run(self):
            called['ran'] = True

    monkeypatch.setitem(run.FEATURES, feature_id, DummyAnalysis)
    monkeypatch.setattr('sys.argv', ['run.py', '--feature', str(feature_id)])
    run.main()
    assert called.get('ran') is True


def test_main_unknown_feature_prints_message(monkeypatch, capsys):
    monkeypatch.setattr('sys.argv', ['run.py', '--feature', '9'])
    run.main()
    out = capsys.readouterr().out
    assert 'Unknown feature 9' in out


def test_missing_feature_flag_exits(monkeypatch):
    # --feature is required; argparse exits with a non-zero status.
    monkeypatch.setattr('sys.argv', ['run.py'])
    with pytest.raises(SystemExit):
        run.parse_args()


def test_non_integer_feature_exits(monkeypatch):
    monkeypatch.setattr('sys.argv', ['run.py', '--feature', 'abc'])
    with pytest.raises(SystemExit):
        run.parse_args()
