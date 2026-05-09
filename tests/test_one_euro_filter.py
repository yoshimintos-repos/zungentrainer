"""Tests fuer den One-Euro-Filter (adaptive Signalglaettung)."""
import pytest
from detection.one_euro_filter import OneEuroFilter

def test_initial_value_passthrough():
    f = OneEuroFilter(min_cutoff=1.0, beta=0.0, d_cutoff=1.0)
    result = f.filter(5.0, timestamp=0.0)
    assert result == 5.0

def test_smoothing_reduces_noise():
    f = OneEuroFilter(min_cutoff=1.0, beta=0.0, d_cutoff=1.0)
    f.filter(0.0, timestamp=0.0)
    result = f.filter(10.0, timestamp=0.033)
    assert 0.0 < result < 10.0

def test_high_beta_tracks_fast_changes():
    slow = OneEuroFilter(min_cutoff=1.0, beta=0.0, d_cutoff=1.0)
    fast = OneEuroFilter(min_cutoff=1.0, beta=10.0, d_cutoff=1.0)
    slow.filter(0.0, timestamp=0.0)
    fast.filter(0.0, timestamp=0.0)
    slow_result = slow.filter(10.0, timestamp=0.033)
    fast_result = fast.filter(10.0, timestamp=0.033)
    assert fast_result > slow_result

def test_reset_clears_state():
    f = OneEuroFilter(min_cutoff=1.0, beta=0.0, d_cutoff=1.0)
    f.filter(100.0, timestamp=0.0)
    f.filter(100.0, timestamp=0.033)
    f.reset()
    result = f.filter(5.0, timestamp=1.0)
    assert result == 5.0
