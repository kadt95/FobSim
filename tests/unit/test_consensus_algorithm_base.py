import sys
import os
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))
import consensus_algorithms
import miner

@pytest.fixture
def test_ca():
    return consensus_algorithms.PoW()


@patch("builtins.input")
@pytest.mark.parametrize("inputs",["3","8","test",""])
def test_choose_consensus(mock_input,inputs,test_ca,capsys):
    mock_input.side_effect = [inputs,"1"]
    result = test_ca.choose_consensus([consensus_algorithms.PoW,consensus_algorithms.PoS,consensus_algorithms.PoA,
                                   consensus_algorithms.PoET,consensus_algorithms.DPoS,consensus_algorithms.Dummy])
    printed = capsys.readouterr().out
    if inputs == "3":
        assert result == 3
    else:
        assert "Input is incorrect, try again..!" in printed



@patch("consensus_algorithm_base.time.time")
@patch("consensus_algorithms.PoW.generate_new_block")
def test_generate_new_block_start(mock_generate_block,mock_time,test_ca):
    mock_time.return_value = 1
    test_ca.generate_new_block_start( "transactions", "generator_id", "previous_hash", "type_of_consensus", "AI_assisted_mining_wanted",
                           "is_adversary")
    assert {'Header': {'generator_id': "generator_id",
                                'hash': '',
                                'blockNo': 0},
                     'Body': {'transactions': "transactions",
                              'nonce': 0,
                              'previous_hash': "previous_hash",
                              'timestamp': 1}} == mock_generate_block.call_args_list[0].args[6]


@patch("consensus_algorithms.PoW.miners_trigger")
@patch("consensus_algorithm_base.copy.deepcopy")
@patch("consensus_algorithm_base.output.mempool_info")
@patch("consensus_algorithm_base.simdata")
def test_miners_trigger_start(mock_simdata,mock_mempool_info,mock_deepcopy,mock_miners_trigger,test_ca):
    mock_simdata.miner_list = [MagicMock(spec = miner.Miner) for _ in range(5)]
    mock_deepcopy.return_value = "test_simdata_mempool"
    test_ca.miners_trigger_start()
    mock_miners_trigger.assert_called_once()
    for minerr in mock_simdata.miner_list:
        assert minerr.local_mempool == "test_simdata_mempool"



@patch("consensus_algorithm_base.random.choice")
@pytest.mark.parametrize("bcfunction",[1,2])
def test_accumulate_transactions(mock_random_choice,bcfunction,test_ca):
    mempool = None
    if bcfunction == 2:
        mempool = [[1, 1, '2*2', 2], [1, 1, '8/9', 2], [1, 2, '9*5', 2],
                   [1, 2, '6*3', 2], [1, 2, '8*2', 2], [1, 3, '9*7', 2],
                   [1, 3, '3*8', 2], [1, 3, '2*5', 2], [1, 4, '1*6', 2]]
    else:
        mempool = [[1, 1], [2, 1], [3, 1],
                   [4, 1], [5, 1], [6, 1]]
    mock_random_choice.side_effect = mempool.copy()
    result = test_ca.accumulate_transactions(4, mempool, bcfunction, "miner_address")
    if bcfunction == 2:
        assert ['End-user address: ' + str(1) + '.' + str(1),
                'Requested computational task: ' + str("2*2"), 'Result: '
                + str(4), "miner: " + "miner_address"] == result
    else:
        assert len(mempool) == 2
        assert len(result) == 4
