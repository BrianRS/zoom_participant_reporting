from processor import fetch_data
import pytest


def test_run():
    result = fetch_data.fetch_data(1)
    assert 2 == result
