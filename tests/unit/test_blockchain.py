import sys
import os
import pytest
from unittest.mock import patch, Mock, MagicMock
import copy

from pywin.mfc.object import Object

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))
import blockchain

fake_confirmation_log={
        "test_hash": {
        "winning_miner": "Miner_1",
        "votes": 1
        },"test_hash_2": {
        "winning_miner": "Miner_2",
        "votes": 2
        }
    }
fake_simdata=Object()
fake_simdata.locks=({
    "confirmation_log": "fake_lock",
    "miner_wallets_log": "fake_lock",
    "miners_stake_amounts": "fake_lock"
})



@patch("blockchain.modification.rewrite_file")
@patch("blockchain.modification.read_file")
def test_report_a_successful_block_addition(mock_read_file, mock_rewrite_file):
    mock_read_file.return_value = copy.deepcopy(fake_confirmation_log)
    blockchain.report_a_successful_block_addition("Miner_1","test_hash",fake_simdata)
    assert mock_rewrite_file.call_args[0][1]["test_hash"]["votes"] == 2 and mock_rewrite_file.call_args[0][1]["test_hash"]["winning_miner"] == "Miner_1"

@patch("blockchain.modification.rewrite_file")
@patch("blockchain.modification.read_file")
def test_report_a_unsuccessful_block_addition_new_addition(mock_read_file, mock_rewrite_file):
    mock_read_file.return_value = copy.deepcopy(fake_confirmation_log)
    blockchain.report_a_successful_block_addition("Miner_3","test_hash_3",fake_simdata)
    assert mock_rewrite_file.call_args[0][1]["test_hash_3"]["votes"] == 1 and mock_rewrite_file.call_args[0][1]["test_hash_3"]["winning_miner"] == "Miner_3"


@patch("blockchain.modification.rewrite_file")
@patch("blockchain.modification.read_file")
def test_report_a_unsuccessful_block_addition_empty_confirmation_log(mock_read_file, mock_rewrite_file):
    mock_read_file.return_value = {}
    blockchain.report_a_successful_block_addition("Miner_1","test_hash",fake_simdata)
    assert mock_rewrite_file.call_args[0][1]["test_hash"]["votes"] == 1 and mock_rewrite_file.call_args[0][1]["test_hash"]["winning_miner"] == "Miner_1"


@patch("blockchain.mining_award",100)
@patch("blockchain.generator_is_adversary")
@patch("blockchain.modification.rewrite_file")
@patch("blockchain.modification.read_file")
def test_award_winning_miners(mock_read_file, mock_rewrite_file, mock_generator_is_adversary, capsys):
    fake_confirmation_log_copy = copy.deepcopy(fake_confirmation_log)
    fake_confirmation_log_copy["test_hash_3"] = {
        "winning_miner": "Miner_3",
        "votes": 3
    }
    mock_read_file.side_effect = [fake_confirmation_log_copy,{"Miner_1": 0,"Miner_2": 0,"Miner_3": 0}]
    mock_generator_is_adversary.return_value = False
    fake_simdata.miner_list = MagicMock()
    fake_simdata.miner_list.__len__.return_value = 3
    blockchain.award_winning_miners(fake_simdata)
    output = capsys.readouterr()
    assert 'Success Score for Adversary Portion (if any)= ' + '0.0 %' in output.out
    assert mock_rewrite_file.call_args[0][1]["Miner_1"] == 0 and mock_rewrite_file.call_args[0][1]["Miner_2"] == 100 and mock_rewrite_file.call_args[0][1]["Miner_3"] == 100

@patch("blockchain.mining_award",100)
@patch("blockchain.generator_is_adversary")
@patch("blockchain.modification.rewrite_file")
@patch("blockchain.modification.read_file")
def test_award_winning_miners_adversary(mock_read_file, mock_rewrite_file, mock_generator_is_adversary, capsys):
    fake_confirmation_log_copy = copy.deepcopy(fake_confirmation_log)
    fake_confirmation_log_copy["test_hash_3"] = {
        "winning_miner": "Miner_3",
        "votes": 3
    }
    mock_read_file.side_effect = [fake_confirmation_log_copy,{"Miner_1": 0,"Miner_2": 0,"Miner_3": 0}]
    mock_generator_is_adversary.side_effect = [True,True]
    fake_simdata.miner_list = MagicMock()
    fake_simdata.miner_list.__len__.return_value = 3
    blockchain.award_winning_miners(fake_simdata)
    output = capsys.readouterr()
    assert '= 66.6' in output.out
    assert mock_rewrite_file.call_args[0][1]["Miner_1"] == 0 and mock_rewrite_file.call_args[0][1]["Miner_2"] == 100 and mock_rewrite_file.call_args[0][1]["Miner_3"] == 100


def test_generator_is_adversary():
    fake_simdata.miner_list = [
        Mock(address="Miner_1", adversary=True),
        Mock(address="Miner_2", adversary=False),
        Mock(address="Miner_3", adversary=False)
    ]
    assert blockchain.generator_is_adversary("Miner_1",fake_simdata.miner_list) == True


@patch("blockchain.modification.rewrite_file")
@patch("blockchain.modification.read_file")
def test_stake(mock_read_file, mock_rewrite_file):
    fake_simdata.type_of_consensus = 2
    fake_simdata.miner_list = [
        Mock(address="Miner_1"),
        Mock(address="Miner_2"),
        Mock(address="Miner_3"),
        Mock(address="Miner_4")
    ]
    blockchain.stake(fake_simdata)
    assert mock_read_file.call_count == len(fake_simdata.miner_list) * 2
    assert mock_rewrite_file.call_count == len(fake_simdata.miner_list) * 2

@patch("blockchain.hashlib")
@patch("blockchain.modification.read_file")
@patch("blockchain.output.fork_analysis")
@patch("blockchain.modification.write_file")
def test_fork_analysis(mock_write_file,mock_fork_analysis,mock_read_file,mock_sha256):
    fake_simdata.miner_list = [
        Mock(address="Miner_1"),
        Mock(address="Miner_2"),
        Mock(address="Miner_3")
    ]
    fake_simdata.locks = MagicMock()
    blockchain.fork_analysis(fake_simdata)
    assert mock_read_file.call_count == len(fake_simdata.miner_list)
    mock_fork_analysis.assert_called_once()
    mock_write_file.assert_called_once()

