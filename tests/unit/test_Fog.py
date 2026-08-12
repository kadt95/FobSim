import sys
import os
from unittest.mock import patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))
import Fog

test_fog = Fog.Fog("test")


def test_receive_tasks():
    test_fog.receive_tasks(["TASK1","TASK2"],"test_user")
    assert test_fog.tasks == ["TASK1","TASK2"]
    assert "test_user" in test_fog.list_of_connected_users


@patch("Fog.output.inform_of_fog_procedure")
@patch("Fog.simdata")
@pytest.mark.parametrize("store_place",[0,1])
def test_send_tasks_to_BC(mock_simdata,mock_inform,store_place):
    mock_simdata.mempool = []
    test_fog.tasks = [["TASK1",1],["TASK2",1],["TASK3",1]]
    test_fog.STOR_PLC = store_place
    test_fog.send_tasks_to_BC(False)
    if store_place == 0:
        assert len(test_fog.local_storage) == len(test_fog.tasks)
    if store_place == 1:
        assert len(mock_simdata.mempool) == len(test_fog.tasks)
    test_fog.local_storage = []
    mock_simdata.mempool = []

@patch("Fog.output.inform_of_fog_procedure")
@patch("Fog.simdata")
def test_send_tasks_to_BC_computational(mock_simdata,mock_inform):
    mock_simdata.mempool = []
    test_fog.tasks = [["TASK1", "5+5",2], ["TASK2","8-9",2], ["TASK3", "5*5",2]]
    test_fog.STOR_PLC = 0
    test_fog.send_tasks_to_BC(False)
    assert len(mock_simdata.mempool) == 1
    assert len(test_fog.local_storage) == 2