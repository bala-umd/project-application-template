"""Tests for the data_loader module."""

import json
import os

import pytest

import data_loader
from data_loader import DataLoader
from model import Issue


def test_loads_all_issues(data_file):
    issues = DataLoader().get_issues()
    assert len(issues) == 4
    assert all(isinstance(i, Issue) for i in issues)


def test_issues_are_cached_as_singleton(data_file):
    first = DataLoader().get_issues()
    second = DataLoader().get_issues()
    # The loader caches issues, so repeated calls return the same object.
    assert first is second


def test_loader_reads_configured_path(data_file):
    loader = DataLoader()
    assert loader.data_path == data_file


def test_missing_data_file_raises(tmp_path):
    os.environ['ENPM611_PROJECT_DATA_PATH'] = str(tmp_path / 'nope.json')
    with pytest.raises(FileNotFoundError):
        DataLoader().get_issues()


def test_empty_dataset_loads_to_empty_list(tmp_path):
    path = tmp_path / 'empty.json'
    path.write_text(json.dumps([]))
    os.environ['ENPM611_PROJECT_DATA_PATH'] = str(path)
    assert DataLoader().get_issues() == []
