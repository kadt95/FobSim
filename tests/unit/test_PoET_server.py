import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))
import PoET_server




@pytest.mark.parametrize("objects",["test1","test2","test3"])
def test_generate_random_waiting_times(objects):
    result = PoET_server.generate_random_waiting_times(5,2,objects)
    assert len(result) == 11
    assert PoET_server.network_waiting_times[objects] == result
    if objects=="test3":
        assert len(PoET_server.network_waiting_times) == 3
