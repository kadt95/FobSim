import sys
import os
from unittest.mock import patch, MagicMock
import pytest


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))
import consensus_algorithms
import miner
import PoET_server


#shared
def helper_generate_new_block(hashing,ca):
    new_block = {
        "Header": {"hash": "test"},
        "Body": {"previous_hash": "test"}
    }
    ca.generate_new_block("", "", "", "", False, "", new_block)
    hashing.assert_called_once()

def valid_block_shared(hashvalue):
    new_block = {
        "Header": {"hash": hashvalue},
        "Body": {"previous_hash": "test"}
    }
    top_block = {
        "Header": {"hash": "test"},
    }
    return new_block, top_block

#PoW tests
@pytest.fixture
def powtest():
    return consensus_algorithms.PoW()

@patch("consensus_algorithms.PoW.pow_mining")
def test_pow_generate_new_block(mock_pow_mining,powtest):
    powtest.generate_new_block("","","","",False,"","")
    mock_pow_mining.assert_called_once()


@patch("miner.Miner.build_block")
@patch("output.simulation_progress")
@patch("consensus_algorithms.Process")
@patch("consensus_algorithms.simdata")
@pytest.mark.parametrize("parallel_mining", [True, False])
def test_pow_miners_trigger(mock_simdata,mock_Process,mock_simprog,mock_build_block,parallel_mining,powtest):
    mock_simdata.params.Parallel_PoW_mining = parallel_mining
    mock_simdata.miner_list = [MagicMock(spec = miner.Miner) for _ in range(5)]
    mock_simdata.expected_chain_length = 3
    powtest.miners_trigger()
    if parallel_mining:
        assert mock_Process.call_count == mock_simdata.expected_chain_length
        calls = 0
        for call in mock_Process.call_args_list:
            if "build_block" in str(call):
                calls += 1
        assert calls == mock_simdata.expected_chain_length
    else:
        called = 0
        for m in mock_simdata.miner_list:
            if m.build_block.call_count != 0:
                called += m.build_block.call_count
        assert called == mock_simdata.expected_chain_length


@patch("consensus_algorithms.encryption_module.hashing_function")
@pytest.mark.parametrize("hashvalue",["0","f"])
def test_pow_block_is_valid(mock_hashing_function,hashvalue,powtest):
    new_block, top_block = valid_block_shared(hashvalue)
    mock_hashing_function.return_value = hashvalue
    with patch("consensus_algorithms.blockchain.target", 14):
        result = powtest.block_is_valid("type_of_consensus", new_block, top_block, "next_pos_block_from", "miner_list","delegates")
    if hashvalue == "0":
        assert result is True
    else:
        assert result is False


@patch("consensus_algorithms.encryption_module.hashing_function")
def test_pow_classical_mining(mock_hashing,powtest):
    mock_hashing.return_value = "0"
    block = {
        "Header": {"hash": "-"},
        "Body": {"nonce": 0}
    }
    with patch("consensus_algorithms.blockchain.target", 14):
        result = powtest.pow_classical_mining(block)
    assert result["Header"]["hash"] == "0"


# PoS tests
@pytest.fixture
def postest():
    return consensus_algorithms.PoS()

@patch("consensus_algorithms.encryption_module.hashing_function")
def test_pos_generate_new_block(mock_hashing,postest):
    helper_generate_new_block(mock_hashing,postest)


@patch("consensus_algorithms.output.simulation_progress")
@patch("miner.Miner.build_block")
@patch("consensus_algorithms.modification.read_file")
@patch("consensus_algorithms.simdata")
def test_pos_miners_trigger(mock_simdata,mock_read_file,mock_build_block,mock_sim_prog,postest):
    mock_simdata.expected_chain_length = 3
    mock_simdata.miner_list = [MagicMock(spec = miner.Miner) for _ in range(5)]
    mock_read_rv = {}
    for i in range(len(mock_simdata.miner_list)):
        mock_simdata.miner_list[i].local_mempool = "test"
        mock_simdata.miner_list[i].address = i
        mock_read_rv[i] = i
    mock_read_file.return_value = mock_read_rv
    postest.miners_trigger()
    build_block_count = 0
    for m in mock_simdata.miner_list:
        build_block_count += m.build_block.call_count
    assert build_block_count == mock_simdata.expected_chain_length


@patch("consensus_algorithms.encryption_module.hashing_function")
@pytest.mark.parametrize("posblockfrom",["valid","invalid"])
def test_pos_block_is_valid(mock_hashing_function,posblockfrom,postest):
    new_block,top_block = valid_block_shared("0")
    new_block['Header']['generator_id'] = posblockfrom
    mock_hashing_function.return_value = "0"
    with patch("consensus_algorithms.blockchain.target", 14):
        result = postest.block_is_valid("type_of_consensus", new_block, top_block, "valid", "miner_list",
                                        "delegates")
    if posblockfrom == "valid":
        assert result is True
    else:
        assert result is False


#PoA tests
@pytest.fixture
def poatest():
    return consensus_algorithms.PoA()

@patch("consensus_algorithms.encryption_module.hashing_function")
def test_poa_generate_new_block(mock_hashing,poatest):
    helper_generate_new_block(mock_hashing,poatest)

@patch("miner.Miner.build_block")
@patch("consensus_algorithms.output.simulation_progress")
@patch("consensus_algorithms.random.choice")
@patch("consensus_algorithms.simdata")
def test_poa_miners_trigger(mock_simdata,mock_rchoice,mock_simprog,mock_build_block,poatest):
    mock_simdata.expected_chain_length = 5
    mock_simdata.miner_list = [MagicMock(spec = miner.Miner) for _ in range(5)]
    mock_rchoice.side_effect = [mock_simdata.miner_list[0],mock_simdata.miner_list[1],mock_simdata.miner_list[2],mock_simdata.miner_list[3],mock_simdata.miner_list[4]]
    for m in mock_simdata.miner_list:
        if m == mock_simdata.miner_list[0]:
            m.local_mempool = ""
        else:
            m.local_mempool = "notempty"
    poatest.miners_trigger()
    build_block_count = 0
    for m in mock_simdata.miner_list:
        build_block_count += m.build_block.call_count
    assert build_block_count == mock_simdata.expected_chain_length-1

@patch("consensus_algorithms.encryption_module.hashing_function")
@pytest.mark.parametrize("generator",[("valid",True),("valid",False),("invalid",True)])
def test_poa_block_is_valid(mock_hashing,generator,poatest):
    new_block,top_block = valid_block_shared("0")
    new_block['Header']['generator_id'] = "valid"
    miner_list = [MagicMock(spec = miner.Miner) for _ in range(5)]
    mock_hashing.return_value = "0"
    for m in miner_list:
        if m == miner_list[3]:
            m.address = generator[0]
            m.isAuthorized = generator[1]
        else:
            m.address  = "test"
            m.isAuthorized = "test"
    result = poatest.block_is_valid("type_of_consensus", new_block, top_block, "next_pos_block_from", miner_list,"delegates")
    if generator == ("valid",True):
        assert result is True
    else:
        assert result is False

#PoET tests
@pytest.fixture
def poettest():
    return consensus_algorithms.PoET()

@patch("consensus_algorithms.encryption_module.hashing_function")
def test_poet_generate_new_block(mock_hashing,poettest):
    helper_generate_new_block(mock_hashing,poettest)

@patch("miner.Miner.build_block")
@patch("consensus_algorithms.Process")
@patch("consensus_algorithms.time.sleep")
@patch("consensus_algorithms.simdata")
@patch("consensus_algorithms.encryption_module.generate_PKI_keys")
@patch("consensus_algorithms.PoET_server.generate_random_waiting_times")
@pytest.mark.parametrize("parallel",[True,False])
def test_poet_miners_trigger(mock_generate_waiting_times,mock_gen_pki,mock_simdata,mock_sleep,mock_process,mock_build_block,parallel,poettest):
    mock_simdata.expected_chain_length = 5
    mock_gen_pki.return_value=["test","test"]
    mock_simdata.miner_list = [MagicMock(spec = miner.Miner) for _ in range(5)]
    for i in range(5):
        mock_simdata.miner_list[i].address = str(i)
    for m in mock_simdata.miner_list:
        m.local_mempool = "test"
        PoET_server.network_waiting_times[m.address] = {0: 0}
        for i in range(5):
            if m.address == str(i) :
                PoET_server.network_waiting_times[m.address][i+1] = 0.12345
            else:
                PoET_server.network_waiting_times[m.address][i+1] = 0.5
    mock_simdata.params.poet_block_time = 1
    mock_simdata.params.Parallel_PoW_mining = parallel
    poettest.miners_trigger()
    if not parallel:
        for m in mock_simdata.miner_list:
            m.build_block.assert_called_once()
        assert len(mock_sleep.call_args_list) == len(mock_simdata.miner_list)*mock_simdata.expected_chain_length+mock_simdata.expected_chain_length
        leastcount = 0
        for arg in mock_sleep.call_args_list:
            if arg[0][0] == 0.12345:
                leastcount += 1
        assert leastcount == mock_simdata.expected_chain_length
    if parallel:
        assert mock_process.call_count == mock_simdata.expected_chain_length
    PoET_server.network_waiting_times.clear()


@patch("consensus_algorithms.time.time")
@patch("consensus_algorithms.PoET_server.network_waiting_times")
@patch("consensus_algorithms.encryption_module.hashing_function")
@patch("consensus_algorithms.encryption_module.retrieve_signature_from_saved_key")
def test_poet_block_is_valid(mock_ret_key,mock_hashing,mock_network_time,mock_time,poettest):
    new_block,top_block = valid_block_shared("0")
    new_block['Header']['PoET'] = "valid"
    new_block['Header']['generator_id'] = "test"
    mock_ret_key.return_value = "valid"
    mock_hashing.return_value = "0"
    top_block["Body"] = {"timestamp": 1}
    top_block["Header"]["blockNo"] = 1
    mock_network_time.__getitem__.return_value.__getitem__.return_value = 1
    mock_time.return_value = 3
    result = poettest.block_is_valid("type_of_consensus",new_block,top_block,"next_pos_block_from","miner_list","delegates")
    assert result is True


#DPoS tests
@pytest.fixture
def dpostest():
    return consensus_algorithms.DPoS()

@patch("consensus_algorithms.modification.write_file")
@patch("consensus_algorithms.simdata")
def test_dpos_prepare_necessary_files(mock_simdata,mock_write_file,dpostest):
    dpostest.prepare_necessary_files()
    mock_write_file.assert_called_once()

@patch("consensus_algorithms.ConsensusAlgorithmBase.dummy_proof_generator_function")
@patch("consensus_algorithms.encryption_module.hashing_function")
def test_dpos_generate_new_block(mock_hashing,mock_dummy_proof,dpostest):
    helper_generate_new_block(mock_hashing,dpostest)
    mock_dummy_proof.assert_called_once()

@patch("consensus_algorithms.output.simulation_progress")
@patch("miner.Miner.build_block")
@patch("consensus_algorithms.Process")
@patch("consensus_algorithms.DPoS.dpos_delegates_selection")
@patch("consensus_algorithms.DPoS.dpos_voting")
@patch("consensus_algorithms.simdata")
@pytest.mark.parametrize("parallel",[True,False])
def test_dpos_miners_trigger(mock_simdata,mock_dpos_voting,mock_delegates_selection,mock_process,mock_build_block,mock_simprog,parallel,dpostest):
    mock_simdata.params.number_of_DPoS_delegates = 3
    mock_delegates_selection.return_value = [1,2,3]
    mock_simdata.miner_list = [MagicMock(spec = miner.Miner) for _ in range(5)]
    for i in range(5):
        mock_simdata.miner_list[i].address = i
        mock_simdata.miner_list[i].delegates = []
    mock_simdata.params.Parallel_PoW_mining = parallel
    dpostest.miners_trigger()
    if parallel:
        calls = 0
        for call in mock_process.call_args_list:
            if "build_block" in str(call):
                calls += 1
        assert calls == len(mock_delegates_selection.return_value)
    else:
        called = 0
        for m in mock_simdata.miner_list:
            if m.build_block.call_count != 0:
                called += m.build_block.call_count
        assert called == len(mock_delegates_selection.return_value)


@patch("consensus_algorithms.encryption_module.hashing_function")
@patch("consensus_algorithms.simdata")
def test_dpos_block_is_valid(mock_simdata,mock_hashing,dpostest):
    new_block,top_block = valid_block_shared("0")
    new_block['Header']['generator_id'] = 'delegate'
    mock_hashing.return_value = "0"
    result = dpostest.block_is_valid("type_of_consensus",new_block,top_block,"next_pos_block_from","miner_list",[1,2,3,"delegate"])
    assert result is True

@patch("consensus_algorithms.simdata")
@patch("consensus_algorithms.modification.read_file")
def test_dpos_voting(mock_read,mock_simdata,dpostest):
    mock_read.return_value = {
        0: 0,
        1: 10,
        2: 20,
        3: 50,
        4: 100
    }
    miner_list = [MagicMock(spec = miner.Miner) for _ in range(5)]
    for i in range(5):
        miner_list[i].address = i
    result = dpostest.dpos_voting(miner_list)
    assert len(result) == len(miner_list)
    for m in miner_list:
        assert m.address in result


@patch("consensus_algorithms.simdata")
def test_dpos_delegates_selection(mock_simdata,dpostest):
    votes_and_stakes = {0: {1: 1}, 1: {0: 0, 2: 2}, 2: {3: 3, 4: 4}, 3: {}, 4: {}}
    result = dpostest.dpos_delegates_selection(votes_and_stakes,2)
    assert 1 and 2 in result