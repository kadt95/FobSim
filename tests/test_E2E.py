import sys
import pytest
import os
from unittest.mock import patch
from IPython.lib.deepreload import reload



sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import main


def run_main():
    main.user_input()
    main.initiate_network()
    main.type_of_consensus = main.new_consensus_module.choose_consensus()
    main.trans_delay = main.define_trans_delay(main.blockchainPlacement)
    main.miner_list = main.initiate_miners()
    main.AI_assisted_mining_wanted = main.give_miners_authorization(main.miner_list, main.type_of_consensus)
    main.inform_miners_of_users_wallets()
    main.blockchain.stake(main.miner_list, main.type_of_consensus)
    main.initiate_genesis_block(main.AI_assisted_mining_wanted)
    main.send_tasks_to_BC()
    main.time_start = main.time.time()
    if main.blockchainFunction == 2:
        main.expected_chain_length = main.ceil((main.num_of_users_per_fog_node * main.NumOfTaskPerUser * main.NumOfFogNodes))
    main.new_consensus_module.miners_trigger(main.miner_list, main.type_of_consensus, main.expected_chain_length,
                                             main.Parallel_PoW_mining,
                                             main.numOfTXperBlock, main.blockchainFunction, main.poet_block_time,
                                             main.Asymmetric_key_length,
                                             main.number_of_DPoS_delegates, main.AI_assisted_mining_wanted)
    main.blockchain.award_winning_miners(len(main.miner_list), main.miner_list)
    main.blockchain.fork_analysis(main.miner_list)
    main.output.finish()
    main.store_fog_data()
    main.elapsed_time = main.time.time() - main.time_start
    print("elapsed time = " + str(main.elapsed_time) + " seconds")


confirmed_bugged=[]

@pytest.mark.parametrize("consensus_algorithm",["1","2","3","4","5"])
@pytest.mark.parametrize("network_placement",["1","2"])
@pytest.mark.parametrize("blockchain_network",["1","2","3","4"])
@patch("builtins.input")
def test_main(mock_input,blockchain_network,network_placement,consensus_algorithm):
    for bug in confirmed_bugged:
        if blockchain_network == bug[0] and network_placement == bug[1] and consensus_algorithm == bug[2]:
            pytest.skip()
    user_input = [blockchain_network, network_placement]
    if blockchain_network=="4":
        user_input.append("done")
    user_input.append(consensus_algorithm)
    if consensus_algorithm == "1":
        user_input.append("N")
    user_input.append("")
    mock_input.side_effect = user_input
    #TODO
    #testing with different sim parameters

    if not (blockchain_network=="1" and network_placement=="1" and consensus_algorithm=="1"):
        reload("main")
        main.Fog.mempool.MemPool.clear()
    run_main()