import multiprocessing
import Fog
import end_user
import miner
import blockchain
import random
import output
from math import ceil
import time
import modification
from consensus_algorithm_base import ConsensusAlgorithmBase
import consensus_algorithms
from Sim_data import simdata


def user_input():
    modification.initiate_files(simdata)
    choose_functionality()
    choose_placement()


def choose_functionality():
    while True:
        output.choose_functionality()
        simdata.blockchainFunction = input()
        if simdata.blockchainFunction in simdata.blockchainFunction:
            simdata.blockchainFunction = int(simdata.blockchainFunction)
            break
        else:
            print("Input is incorrect, try again..!")


def choose_placement():
    while True:
        output.choose_placement()
        simdata.blockchainPlacement = input()
        if simdata.blockchainPlacement in simdata.blockchain_placement_options:
            simdata.blockchainPlacement = int(simdata.blockchainPlacement)
            break
        else:
            print("Input is incorrect, try again..!")


def initiate_network():
    for count in range(simdata.params.NumOfFogNodes):
        simdata.fogNodes.append(Fog.Fog(count + 1))
        for p in range(simdata.params.num_of_users_per_fog_node):
            simdata.list_of_end_users.append(end_user.User(p + 1, count + 1))
    output.users_and_fogs_are_up()
    if simdata.blockchainFunction == 4:
        output.GDPR_warning()
        while True:
            print("If you don't want other attributes to be added to end_users, input: done\n")
            new_attribute = input("If you want other attributes to be added to end_users, input them next:\n")
            if new_attribute == 'done':
                break
            else:
                for user in simdata.list_of_end_users:
                    user.identity_added_attributes[new_attribute] = ''
                output.user_identity_addition_reminder(len(simdata.list_of_end_users))
    for user in simdata.list_of_end_users:
        user.create_tasks(simdata.params.NumOfTaskPerUser, simdata.blockchainFunction, simdata.list_of_end_users)
        user.send_tasks(simdata.fogNodes)
        print("End_user " + str(user.addressParent) + "." + str(user.addressSelf) + " had sent its tasks to the fog layer")


def initiate_miners():
    the_miners_list = []

    if simdata.blockchainPlacement == 1:
        for i in range(simdata.params.NumOfFogNodes):
            the_miners_list.append(miner.Miner(i + 1, simdata.trans_delay, simdata.params.gossip_activated))
    if simdata.blockchainPlacement == 2:
        for i in range(simdata.params.NumOfMiners):
            the_miners_list.append(miner.Miner(i + 1, simdata.trans_delay, simdata.params.gossip_activated))
    for entity in the_miners_list:
        simdata.locks[f"{entity.address}_local_chain"] = multiprocessing.Lock()
        modification.write_file("temporary/" + entity.address + "_local_chain.json", {},simdata.locks[f"{entity.address}_local_chain"])
        miner_wallets_log_py = modification.read_file("temporary/miner_wallets_log.json",simdata.locks["miner_wallets_log"])
        miner_wallets_log_py[str(entity.address)] = simdata.params.initial_wallet_value
        modification.rewrite_file("temporary/miner_wallets_log.json", miner_wallets_log_py,simdata.locks["miner_wallets_log"])
    print('Miners have been initiated..')
    connect_miners(the_miners_list)
    output.miners_are_up()
    return the_miners_list


def define_trans_delay(layer):
    transmission_delay = 0
    if layer == 1:
        transmission_delay = simdata.params.delay_between_fog_nodes
    if layer == 2:
        transmission_delay = simdata.params.delay_between_end_users
    return transmission_delay


def connect_miners(miners_list):
    print("Miners will be connected in a P2P fashion now. Hold on...")
    bridges = set()
    all_components = create_components(miners_list)
    for comp in all_components:
        bridge = random.choice(tuple(comp))
        bridges.add(bridge)
    bridging(bridges, miners_list)


def bridging(bridges, miners_list):
    while len(bridges) != 1:
        bridge = random.choice(tuple(bridges))
        other_bridge = random.choice(tuple(bridges))
        same_bridge = True
        while same_bridge:
            other_bridge = random.choice(tuple(bridges))
            if other_bridge != bridge:
                same_bridge = False
        for entity in miners_list:
            if entity.address == bridge:
                entity.neighbours.add(other_bridge)
            if entity.address == other_bridge:
                entity.neighbours.add(bridge)
        bridges.remove(bridge)


def create_components(miners_list):
    all_components = set()
    for entity in miners_list:
        component = set()
        while len(entity.neighbours) < simdata.params.number_of_miner_neighbours:
            neighbour = random.choice(miners_list).address
            if neighbour != entity.address:
                entity.neighbours.add(neighbour)
                component.add(neighbour)
                for entity_2 in miners_list:
                    if entity_2.address == neighbour:
                        entity_2.neighbours.add(entity.address)
                        component.add(entity.address)
                        break
        if component:
            all_components.add(tuple(component))
    return all_components


def give_miners_authorization(the_miners_list):
    if simdata.type_of_consensus == 1:
        wanted, float_portion = output.AI_assisted_mining_wanted()
        if wanted:
            num_of_miners_requested_to_use_AI = ceil(float_portion * len(the_miners_list))
            num_of_miners_instructed_to_use_AI = 0
            while num_of_miners_instructed_to_use_AI < num_of_miners_requested_to_use_AI:
                random_miner = random.choice(the_miners_list)
                if not random_miner.adversary:
                    random_miner.adversary = True
                    num_of_miners_instructed_to_use_AI += 1
            print(str(num_of_miners_instructed_to_use_AI) + ' miners were successfully instructed to use AI.')
        return wanted
    if simdata.type_of_consensus == 3:
        # automated approach:
        if simdata.params.Automatic_PoA_miners_authorization:
            for i in range(len(the_miners_list)):
                the_miners_list[i].isAuthorized = True
                simdata.list_of_authorized_miners.append(the_miners_list[i])
        else:
            # user input approach:
            output.authorization_trigger(simdata.blockchainPlacement, simdata.params.NumOfFogNodes, simdata.params.NumOfMiners)
            while True:
                authorized_miner = input()
                if authorized_miner == "done":
                    break
                else:
                    for node in the_miners_list:
                        if node.address == "Miner_" + authorized_miner:
                            node.isAuthorized = True
                            simdata.list_of_authorized_miners.append(node)
    return None


def initiate_genesis_block(AI_wanted):
    genesis_transactions = ["genesis_block"]
    for i in range(len(simdata.miner_list)):
        genesis_transactions.append(simdata.miner_list[i].address)
    genesis_block = simdata.chosen_consensus.generate_new_block_start(genesis_transactions, 'The Network', 0, simdata.type_of_consensus, AI_wanted, False)
    output.block_info(genesis_block, simdata.type_of_consensus)
    for elem in simdata.miner_list:
        elem.receive_new_block(genesis_block, simdata)
    output.genesis_block_generation()


def send_tasks_to_BC():
    for node in simdata.fogNodes:
        node.send_tasks_to_BC(simdata.user_informed)
        if not simdata.user_informed:
            simdata.user_informed = True


def store_fog_data():
    for node in simdata.fogNodes:
        log = open('temporary/Fog_node_'+str(node.address)+'.txt', 'w')
        log.write(str(node.local_storage))


def inform_miners_of_users_wallets():
    if simdata.blockchainFunction == 3:
        user_wallets = {}
        for user in simdata.list_of_end_users:
            wallet_info = {'parent': user.addressParent,
                           'self': user.addressSelf,
                           'wallet_value': user.wallet}
            user_wallets[str(user.addressParent) + '.' + str(user.addressSelf)] = wallet_info
        for i in range(len(simdata.miner_list)):
            modification.rewrite_file(str("temporary/" + simdata.miner_list[i].address + "_users_wallets.json"), user_wallets,simdata.locks[f"{simdata.miner_list[i].address}_users_wallets"])


if __name__ == '__main__':
    user_input()
    initiate_network()
    simdata.consensus_setup(ConsensusAlgorithmBase)
    simdata.trans_delay = define_trans_delay(simdata.blockchainPlacement)
    simdata.miner_list = initiate_miners()
    simdata.AI_assisted_mining_wanted = give_miners_authorization(simdata.miner_list)
    inform_miners_of_users_wallets()
    blockchain.stake(simdata.miner_list, simdata.type_of_consensus, simdata)
    initiate_genesis_block(simdata.AI_assisted_mining_wanted)
    send_tasks_to_BC()
    time_start = time.time()
    if simdata.blockchainFunction == 2:
        simdata.expected_chain_length = ceil((simdata.params.num_of_users_per_fog_node * simdata.params.NumOfTaskPerUser * simdata.params.NumOfFogNodes))

    simdata.chosen_consensus.miners_trigger_start()

    blockchain.award_winning_miners(len(simdata.miner_list), simdata.miner_list, simdata)
    blockchain.fork_analysis(simdata.miner_list, simdata)
    output.finish()
    store_fog_data()
    elapsed_time = time.time() - time_start
    print("elapsed time = " + str(elapsed_time) + " seconds")

