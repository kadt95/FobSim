import sys
import os
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))
import modification


@patch("Sim_data.simdata")
@patch("modification.write_file")
@patch("modification.shutil.rmtree")
@patch("modification.os.listdir")
@patch("modification.os.path.islink")
@patch("modification.os.path.isfile")
@patch("modification.os.path.join")
@pytest.mark.parametrize("gossip",[True,False])
def test_initiate_files(mock_join,mock_isfile,mock_islink,mock_listdir,mock_rmtree,mock_write_file,mock_simdata,gossip):
    mock_simdata.params.gossip_activated = gossip
    mock_listdir("temporary").return_value = ["test","test2"]
    modification.initiate_files(mock_simdata)
    if gossip:
        assert mock_write_file.call_count == 3
    if not gossip:
        assert mock_write_file.call_count == 2
