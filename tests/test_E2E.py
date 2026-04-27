import sys
import pytest
import os
from unittest.mock import patch
import deepreload


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import main


def run_main():
    main.user_input()
    main.initiate_network()
    main.simdata.consensus_setup()
    main.simdata.trans_delay = main.define_trans_delay(main.simdata.blockchainPlacement)
    main.simdata.miner_list = main.initiate_miners()
    main.simdata.AI_assisted_mining_wanted = main.give_miners_authorization(main.simdata.miner_list)
    main.inform_miners_of_users_wallets()
    main.blockchain.stake(main.simdata.miner_list, main.simdata.type_of_consensus)
    main.initiate_genesis_block(main.simdata.AI_assisted_mining_wanted)
    main.send_tasks_to_BC()
    main.time_start = main.time.time()
    if main.simdata.blockchainFunction == 2:
        main.simdata.expected_chain_length = main.ceil((main.simdata.params.num_of_users_per_fog_node * main.simdata.params.NumOfTaskPerUser * main.simdata.params.NumOfFogNodes))
    main.simdata.chosen_consensus.miners_trigger_start(main.simdata)
    main.blockchain.award_winning_miners(len(main.simdata.miner_list), main.simdata.miner_list)
    main.blockchain.fork_analysis(main.simdata.miner_list)
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
        deepreload.reload("main")
        main.Fog.mempool.MemPool.clear()
    run_main()