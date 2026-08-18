import sys
import os
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))
import miner


@pytest.fixture
def test_miner():
    return miner.Miner("test",0,True)


@patch("Sim_data.simdata")
@patch("output.unauthorized_miner_msg")
@patch("miner.Miner.continue_building_block")
@patch("miner.time.time")
@pytest.mark.parametrize("consensus,time_value,authorization",[(3,None,True),(3,None,False),(4,2,None),(4,4,None)])
def test_build_block(mock_time,mock_continue_block,mock_unath_msg,mock_simdata,consensus,time_value,authorization,test_miner):
    mock_simdata.type_of_consensus = consensus
    test_miner.isAuthorized = authorization
    if consensus == 4:
        test_miner.top_block = {"Body":{"timestamp": 1},"Header":{"blockNo": 1}}
        test_miner.waiting_times = {2: 2}
        mock_time.return_value = time_value
    test_miner.build_block(mock_simdata)
    if consensus == 3:
        if not authorization:
            mock_unath_msg.assert_called_once()
        if authorization:
            mock_continue_block.assert_called_once_with(mock_simdata)
    if consensus == 4:
        if time_value == 4:
            mock_continue_block.assert_called_once_with(mock_simdata)
        if time_value == 2:
            mock_continue_block.assert_not_called()


@patch("Sim_data.simdata.chosen_consensus.accumulate_transactions")
@patch("miner.Miner.abstract_block_building")
@patch("Sim_data.simdata")
@patch("miner.output.block_info")
@pytest.mark.parametrize("blockchainfunction",[2,1])
def test_continue_building_block(mock_block_info,mock_simdata,mock_abstract_bb,mock_accumulate_txs,blockchainfunction,test_miner):
    mock_simdata.blockchainFunction = blockchainfunction
    if blockchainfunction == 2:
        mock_abstract_bb.return_value = {'Body': {'transactions': ['End-user address: TEST', 'Requested computational task: 1*1', 'Result: 1', 'miner: TEST']}}
        test_miner.local_mempool = [["TEST1","TEST", "1*1"],["TEST2","TEST", "2/2"],["TEST3","TEST", "3-3"],["TEST4","TEST", "4+4"]]
        test_miner.build_block(mock_simdata)
        assert test_miner.local_mempool == [["TEST2","TEST", "2/2"],["TEST3","TEST", "3-3"],["TEST4","TEST", "4+4"]]
    if blockchainfunction != 2:
        mock_accumulate_txs.return_value = [[1, 1], [2, 1], [3, 1]]
        test_miner.local_mempool = [[1, 1], [2, 1], [3, 1], [4, 1], [5, 1]]
        test_miner.build_block(mock_simdata)
        assert test_miner.local_mempool == [[4, 1], [5, 1]]


@patch("miner.encryption_module.retrieve_signature_from_saved_key")
@patch("miner.Miner.gossip")
@patch("miner.Miner.validate_transactions")
def test_abstract_block_building(mock_validate_txs,mock_gossiping,mock_retrieve_key,test_miner):
    mock_simdata = MagicMock()
    mock_simdata.type_of_consensus = 4
    mock_simdata.blockchainFunction = 3
    mock_simdata.gossiping = True
    mock_validate_txs.return_value = []
    test_miner.top_block = MagicMock()
    test_miner.abstract_block_building([],mock_simdata)
    mock_validate_txs.assert_called_once()
    mock_retrieve_key.assert_called_once()
    mock_gossiping.assert_called_once()
    mock_simdata.chosen_consensus.generate_new_block_start.assert_called_once_with([], test_miner.address,
                                        test_miner.top_block['Header']['hash'], mock_simdata.type_of_consensus,
                                        mock_simdata.AI_assisted_mining_wanted, test_miner.adversary)

@patch("miner.Miner.add")
@patch("miner.modification.read_file")
@patch("Sim_data.simdata")
def test_receive_new_block_genesis(mock_simdata,mock_read,mock_add,test_miner):
    genesis_block = {'Body': {'nonce': 0, 'previous_hash': 0, 'timestamp': 1,
                              'transactions': ['genesis_block', 'Test_1', 'Test_2', 'Test_3']},
                            'Header': {'blockNo': 0, 'generator_id': 'The Network', 'hash': 'test'}}
    mock_read.return_value = []
    test_miner.receive_new_block(genesis_block,mock_simdata)
    mock_add.assert_called_once_with(genesis_block,mock_simdata)


@patch("miner.Miner.gossip")
@patch("miner.Miner.add")
@patch("miner.modification.read_file")
@patch("Sim_data.simdata")
def test_receive_new_block_miner_has_block(mock_simdata,mock_read,mock_add,mock_gossip,test_miner):
    new_block = {'Header': {'generator_id': 'The Test', 'hash': 'test'}}
    mock_read.return_value = {'0': {'Body': {'transactions': ['TEST0']},
                                    'Header': {'generator_id': 'The Test',
                                    'hash': 'test0'}},
                                '1': {'Header': {'generator_id': 'The Test',
                                                 'hash': 'test'}}
                                }
    test_miner.receive_new_block(new_block,mock_simdata)
    mock_add.assert_not_called()



@patch("miner.Miner.gossip")
@patch("Sim_data.simdata.chosen_consensus.block_is_valid")
@patch("miner.Miner.add")
@patch("miner.modification.read_file")
@patch("Sim_data.simdata")
@pytest.mark.parametrize("valid",[True,False])
def test_receive_new_block(mock_simdata,mock_read,mock_add,mock_block_valid,mock_gossip,valid,test_miner):
    new_block = {'Body': {'nonce': 0, 'previous_hash': 0, 'timestamp': 1,
                              'transactions': ['TEST0', 'TEST1', 'TEST2']},
                     'Header': {'blockNo': 0, 'generator_id': 'The Test', 'hash': 'test'}}
    mock_read.return_value = {'0': {'Header': {'generator_id': 'The Test',
                                    'hash': 'test0'}},
                              '1': {'Header': {'generator_id': 'The Test',
                                               'hash': 'test1'}},
                              '2': {'Header': {'generator_id': 'The Test',
                                               'hash': 'test2'}}
                              }
    test_miner.local_mempool = ["TEST0","TEST1","TEST2","TEST3"]
    mock_block_valid.return_value = valid
    mock_simdata.blockchainFunction = 1
    test_miner.neighbours = [MagicMock (spec = miner.Miner) for _ in range(5)]
    test_miner.receive_new_block(new_block, mock_simdata)
    if not valid:
        mock_add.assert_not_called()
        assert test_miner.local_mempool == ["TEST0","TEST1","TEST2","TEST3"]
    if valid:
        assert test_miner.local_mempool == ["TEST3"]
        for neighbour in test_miner.neighbours:
            neighbour.receive_new_block.asser_called_once()




@patch("Sim_data.simdata")
@patch("miner.modification.rewrite_file")
@patch("miner.modification.read_file")
@pytest.mark.parametrize("miner_role",["generator","receiver"])
def test_validate_transactions(mock_read_file,mock_rewrite,mock_simdata,miner_role,test_miner):
    mock_simdata.locks = MagicMock()
    mock_read_file.return_value = {'1.1': {'parent': 1, 'self': 1, 'wallet_value': 500},
                                   '1.2': {'parent': 1, 'self': 2, 'wallet_value': 500},
                                   '2.1': {'parent': 2, 'self': 1, 'wallet_value': 500},
                                   '3.3': {'parent': 3, 'self': 3, 'wallet_value': 500},
                                   '5.1': {'parent': 5, 'self': 1, 'wallet_value': 500}}
    new_txs = [[100, 1, 1, 1, 2, 3], [200, 1, 2, 2, 1, 3], [300, 2, 1, 3, 3, 3], [400, 3, 3, 1, 1, 3], [50, 5, 5, 1, 4, 3]]
    result = test_miner.validate_transactions(new_txs,miner_role,mock_simdata)
    expected_txs = {'1.1': {'parent': 1, 'self': 1, 'wallet_value': 800},
                    '1.2': {'parent': 1, 'self': 2, 'wallet_value': 400},
                    '2.1': {'parent': 2, 'self': 1, 'wallet_value': 400},
                    '3.3': {'parent': 3, 'self': 3, 'wallet_value': 400},
                    '5.1': {'parent': 5, 'self': 1, 'wallet_value': 500}}
    if miner_role == "receiver":
        mock_rewrite.assert_called_once_with(str("temporary/" + test_miner.address + "_users_wallets.json"),
                                             expected_txs,
                                             mock_simdata.locks[f"{test_miner.address}_users_wallets"]
                                             )
    if miner_role == "generator":
        assert result == new_txs


@patch("miner.output.illegal_tx")
@patch("Sim_data.simdata")
@patch("miner.modification.rewrite_file")
@patch("miner.modification.read_file")
@pytest.mark.parametrize("miner_role",["generator","receiver"])
def test_validate_transactions_illegal_txs(mock_read_file,mock_rewrite,mock_simdata,mock_illegal_tx,miner_role,test_miner):
    mock_simdata.locks = MagicMock()
    mock_read_file.return_value = {'1.1': {'parent': 1, 'self': 1, 'wallet_value': 100},
                                   '1.2': {'parent': 1, 'self': 2, 'wallet_value': 100}}
    new_txs = [[10, 1, 1, 1, 2, 3], [150, 1, 2, 1, 1, 3]]
    result = test_miner.validate_transactions(new_txs,miner_role,mock_simdata)
    if miner_role == "receiver":
        assert result == False
    if miner_role == "generator":
        mock_illegal_tx.assert_called_once_with([150, 1, 2, 1, 1, 3],100)
        assert result == [[10, 1, 1, 1, 2, 3]]


@patch("miner.Miner.update_global_longest_chain")
@patch("miner.Miner.remove_confirmed_txs_from_local_mempool")
@patch("miner.modification.rewrite_file")
@patch("miner.blockchain.report_a_successful_block_addition")
@patch("Sim_data.simdata")
@patch("miner.modification.read_file")
def test_add(mock_read_file,mock_simdata,mock_report_block,mock_rewrite,mock_remove_txs,mock_update_global,test_miner):
    mock_simdata.locks = MagicMock()
    local_chain = MagicMock()
    local_chain.__len__.return_value = 2
    test_miner.top_block = {"Header": {"hash": "test"}}
    block = {"Header": {"generator_id": "test_id", "hash":"test_hash","blockNo": 2},"Body":{"transactions": "Test","previous_hash": "test"}}
    mock_read_file.return_value = local_chain
    mock_simdata.blockchainFunction = 1
    test_miner.add(block,mock_simdata)
    mock_report_block.assert_called_once_with("test_id", "test_hash", mock_simdata)
    mock_rewrite.assert_called_once_with(str("temporary/" + test_miner.address + "_local_chain.json"),local_chain ,mock_simdata.locks[f"{test_miner.address}_local_chain"])
    mock_remove_txs.assert_called_once_with(block,mock_simdata.blockchainFunction)
    mock_update_global.assert_called_once_with(local_chain, mock_simdata.blockchainFunction, mock_simdata.miner_list,mock_simdata)



@pytest.mark.parametrize("blockchainfunction",[2,1])
def test_remove_confirmed_txs_from_local_mempool(blockchainfunction,test_miner):
    if blockchainfunction == 2:
        confirmed_block = {'Header':{'generator_id': 'test'},'Body': {'transactions': ['End-user address: TEST', 'Requested computational task: 1*1', 'Result: 1', 'miner: TEST']}}
        test_miner.local_mempool = [["TEST1","TEST", "1*1"],["TEST2","TEST", "2/2"],["TEST3","TEST", "3-3"],["TEST4","TEST", "4+4"]]
        test_miner.remove_confirmed_txs_from_local_mempool(confirmed_block,blockchainfunction)
        assert test_miner.local_mempool == [["TEST2","TEST", "2/2"],["TEST3","TEST", "3-3"],["TEST4","TEST", "4+4"]]
    if blockchainfunction != 2:
        confirmed_block = {'Header':{'generator_id': 'test'},'Body':{'transactions': [[1, 1], [2, 1], [3, 1]]}}
        test_miner.local_mempool = [[1, 1], [2, 1], [3, 1], [4, 1], [5, 1]]
        test_miner.remove_confirmed_txs_from_local_mempool(confirmed_block,blockchainfunction)
        assert test_miner.local_mempool == [[4, 1], [5, 1]]

@pytest.fixture()
def global_chain():
    return {'chain': {'1': {'Body': {'nonce': 1, 'previous_hash': 'test_hash1', 'timestamp': 1, 'transactions': [[11, 1], [12, 1], [13, 1], [14, 1], [15, 1]]}, 'Header': {'blockNo': 1, 'generator_id': 'Test1', 'hash': 'test_hash2'}},
                      '2': {'Body': {'nonce': 2, 'previous_hash': 'test_hash2', 'timestamp': 2, 'transactions': [[21, 1], [22, 1], [23, 1], [24, 1], [25, 1]]}, 'Header': {'blockNo': 2, 'generator_id': 'Test2', 'hash': 'test_hash3'}},
                      '3': {'Body': {'nonce': 3, 'previous_hash': 'test_hash3', 'timestamp': 3, 'transactions': [[31, 1], [32, 1], [33, 1], [34, 1], [35, 1]]}, 'Header': {'blockNo': 3, 'generator_id': 'Test3', 'hash': 'test_hash4'}}},
                      'from':'Test1'}


@patch("miner.Miner.global_chain_is_confirmed_by_majority")
@patch("miner.modification.rewrite_file")
@patch("miner.modification.read_file")
@patch("Sim_data.simdata")
@pytest.mark.parametrize("blockchainfunction,local_length",[(3,1),(1,4)])
def test_gossip(mock_simdata,mock_read_file,mock_rewrite_file,mock_global_ch_confirmed,blockchainfunction,local_length,test_miner,global_chain):
    mock_local_chain = MagicMock()
    mock_local_chain.__len__.return_value = local_length
    mock_simdata.blockchainFunction = blockchainfunction
    side_effects = [mock_local_chain,global_chain]
    if mock_simdata.blockchainFunction == 3:
        side_effects.append("test_wallet_file")
    mock_read_file.side_effect = side_effects
    mock_global_ch_confirmed.return_value = True
    test_miner.gossip(mock_simdata.blockchainFunction, mock_simdata.miner_list, mock_simdata)
    if local_length == 1:
        if blockchainfunction == 3:
            assert mock_rewrite_file.call_count == 2
            mock_rewrite_file.assert_any_call(str("temporary/" + test_miner.address + "_users_wallets.json"), "test_wallet_file", mock_simdata.locks[f"{test_miner.address}_users_wallets"])
        else:
            mock_rewrite_file.assert_called_once_with(str("temporary/" + test_miner.address + "_local_chain.json"), global_chain["from"], mock_simdata.locks[f"{test_miner.address}_local_chain"])
            assert test_miner.top_block == global_chain["chain"][str(len(global_chain["chain"]) - 1)]



@patch("miner.modification.read_file")
@patch("Sim_data.simdata")
@pytest.mark.parametrize("confirmed",[True,False])
def test_global_chain_is_confirmed_by_majority(mock_simdata,mock_read_file,confirmed,test_miner,global_chain):
    return_values = {
    "test_hash2": {
        "winning_miner": "Test_1",
        "votes": 5
    },
    "test_hash3": {
        "winning_miner": "Test_2",
        "votes": 4
    },
    "test_hash4": {
        "winning_miner": "Test_3",
        "votes": 5
    }
    }
    if not confirmed :
        return_values.update({
            "test_hash5": {
                "winning_miner": "Test_4",
                "votes": 1
            }
        })
        global_chain["chain"].update({
            "4": {
                "Header": {
                    "hash": "test_hash5"
                }
            }
        })
        assert "4" in global_chain["chain"]
        assert global_chain["chain"]["4"]["Header"]["hash"] == "test_hash5"
    mock_read_file.return_value = return_values
    result = test_miner.global_chain_is_confirmed_by_majority(global_chain["chain"], 5, mock_simdata)
    if confirmed:
        assert result == True
    if not confirmed :
        assert result == False


@patch("miner.Miner.gossip")
@patch("miner.modification.rewrite_file")
@patch("Sim_data.simdata")
@patch("miner.modification.read_file")
@pytest.mark.parametrize("local_length",[4,2])
def test_update_global_longest_chain(mock_read_file,mock_simdata,mock_rewrite_file,mock_gossip,local_length,test_miner,global_chain):
    mock_local_chain = MagicMock()
    mock_local_chain.__len__.return_value = local_length
    mock_read_file.return_value = global_chain
    mock_simdata.locks = MagicMock()
    test_miner.update_global_longest_chain(mock_local_chain, 2, "test_miner_list", mock_simdata)
    if local_length == 4:
        assert global_chain["chain"] == mock_local_chain
        mock_rewrite_file.assert_called_once_with('temporary/longest_chain.json', global_chain,mock_simdata.locks["longest_chain"])
    if local_length == 2:
        mock_gossip.assert_called_once_with(2, "test_miner_list", mock_simdata)