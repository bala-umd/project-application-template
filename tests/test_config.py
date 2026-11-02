"""Tests for the config module."""

import argparse
import os

import config


def test_set_and_get_string_parameter():
    config.set_parameter('label', 'kind/bug')
    assert config.get_parameter('label') == 'kind/bug'


def test_env_variable_takes_precedence():
    os.environ['ENPM611_PROJECT_DATA_PATH'] = 'data/custom.json'
    assert config.get_parameter('ENPM611_PROJECT_DATA_PATH') == 'data/custom.json'


def test_get_missing_parameter_returns_default():
    assert config.get_parameter('does_not_exist') is None
    assert config.get_parameter('does_not_exist', default='fallback') == 'fallback'


def test_overwrite_from_args_stores_non_none_values():
    args = argparse.Namespace(feature=1, user=None, label='kind/bug')
    config.overwrite_from_args(args)
    assert config.get_parameter('label') == 'kind/bug'
    assert config.get_parameter('feature') == 1
    # A None argument must not be written into the config.
    assert config.get_parameter('user') is None


def test_set_typed_parameter_roundtrips_int():
    config.set_parameter('feature', 3)
    assert config.get_parameter('feature') == 3
