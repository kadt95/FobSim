import sys
import os
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))
import end_user


test_user = end_user.User("test","test_parent")
test_user.STOR_PLC = 1
test_user.wallet = 100

@patch("end_user.User._User__apply_first_functionality")
@patch("end_user.User._User__apply_second_functionality")
@patch("end_user.User._User__apply_third_functionality")
@patch("end_user.User._User__apply_forth_functionality")
@pytest.mark.parametrize("functionality",[1,2,3,4])
def test_create_tasks(mock_4, mock_3, mock_2, mock_1,functionality):
    test_user.create_tasks("test_tasks_per_user",functionality,"test_list")
    if functionality == 1:
        mock_1.assert_called_once_with("test_tasks_per_user",functionality)
    if functionality == 2:
        mock_2.assert_called_once_with("test_tasks_per_user",functionality)
    if functionality == 3:
        mock_3.assert_called_once_with("test_tasks_per_user","test_list",functionality)
    if functionality == 4:
        mock_4.assert_called_once_with(functionality)


def test_send_tasks():
    import Fog
    mock_fogs = [MagicMock (spec = Fog.Fog) for _ in range(5)]
    for fog in mock_fogs:
        fog.address = "test"
    mock_fogs[3].address = "test_parent"
    test_user.send_tasks(mock_fogs)
    for fog in mock_fogs:
        if fog.address != "test_parent":
            fog.receive_tasks.assert_not_called()
        else:
            fog.receive_tasks.assert_called_once()

@patch("end_user.output")
@pytest.mark.parametrize("txperuser",[0,10,1000,-10,-1000])
def test_apply_first_functionality(mock_output,txperuser):
    test_user._User__apply_first_functionality(txperuser,"test")
    assert len(test_user.tasks) == max(0,txperuser)
    test_user.tasks = []


@pytest.mark.parametrize("txperuser",[0,10,1000,-10,-1000])
def test_apply_second_functionality(txperuser):
    test_user._User__apply_second_functionality(txperuser,"test")
    assert len(test_user.tasks) == max(0,txperuser)
    test_user.tasks = []

@pytest.mark.parametrize("txperuser",[0,10,1000,-10,-1000])
def test_apply_third_functionality(txperuser):
    mock_end_users = [MagicMock(spec = end_user.User) for _ in range(5)]
    for user in mock_end_users:
        user.addressParent = MagicMock()
        user.addressSelf = MagicMock()
    test_user._User__apply_third_functionality(txperuser, mock_end_users,"test")
    assert len(test_user.tasks) == max(0, txperuser)
    test_user.tasks = []

@pytest.mark.parametrize("txperuser",[0,10,1000,-10,-1000])
def test_apply_forth_functionality(txperuser):
    test_user._User__apply_forth_functionality("test")
    assert len(test_user.tasks) == 1
    test_user.tasks = []


@patch("builtins.input")
def test_add_new_attributes(mock_input):
    attributes = ["TEST1","TEST2","TEST3","TEST4","TEST5"]
    mock_input.side_effect = attributes
    test_user.identity_added_attributes = {"KEY1": None, "KEY2": None, "KEY3": None, "KEY4": None, "KEY5": None}
    end_user.add_new_attributes(test_user)
    for attribute in attributes:
        assert attribute in test_user.identity_added_attributes.values()
    test_user.identity_added_attributes = {}