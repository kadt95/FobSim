from multiprocessing import Process
import random
import time

import PoET_server
import blockchain
import encryption_module
import modification
import output
from consensus_algorithm_base import ConsensusAlgorithmBase

# NON-MODIFIABLE PART:

class PoW(ConsensusAlgorithmBase):
    name = 'Proof of Work (PoW)'
    orderNo = "1"

    def prepare_necessary_files(self):
        pass

    def generate_new_block(self, transactions, generator_id, previous_hash, type_of_consensus, AI_assisted_mining_wanted, is_adversary, new_block):
        if AI_assisted_mining_wanted:
            new_block['Header']['is_adversary'] = is_adversary
        new_block = self.pow_mining(new_block, AI_assisted_mining_wanted, is_adversary)
        return new_block

    def miners_trigger(self, simdata):
        mining_processes = []
        for counter in range(simdata.expected_chain_length):
            obj = random.choice(simdata.miner_list)
            if simdata.params.Parallel_PoW_mining:
                # parallel approach
                process = Process(target=obj.build_block, args=(
                    simdata,))
                process.start()
                mining_processes.append(process)
            else:
                # non-parallel approach
                obj.build_block(simdata)
            output.simulation_progress(counter, simdata.expected_chain_length)
        for process in mining_processes:
            process.join()

    def block_is_valid(self, type_of_consensus, new_block, top_block, next_pos_block_from, miner_list, delegates):
        if int(new_block['Header']['hash'], 16) <= blockchain.target:
            if new_block['Body']['previous_hash'] == top_block['Header']['hash']:
                if new_block['Header']['hash'] == encryption_module.hashing_function(new_block['Body']):
                    return True
        return False

    def pow_classical_mining(self, block):
        if block['Body']['nonce'] > 4000000000 / 2:
            up = False
        else:
            up = True
        for i in range(1, 4000000000):
            block['Header']['hash'] = encryption_module.hashing_function(block['Body'])
            if int(block['Header']['hash'], 16) <= blockchain.target:
                return block
            else:
                if up:
                    block['Body']['nonce'] += 1
                else:
                    block['Body']['nonce'] -= 1
                continue

    def pow_mining(self, block, AI_assisted_mining_wanted, is_adversary):
        while True:
            if AI_assisted_mining_wanted and is_adversary:
                print('AI-assisted mining is currently under construction. Classical mining will be used for now')
                new_block = self.pow_classical_mining(block)
                break
            else:
                new_block = self.pow_classical_mining(block)
                break
        return new_block

class PoS(ConsensusAlgorithmBase):
    name = 'Proof of Stake (PoS)'
    orderNo = "2"

    def prepare_necessary_files(self):
        modification.write_file('temporary/miners_stake_amounts.json', {})

    def generate_new_block(self, transactions, generator_id, previous_hash, type_of_consensus,
                           AI_assisted_mining_wanted, is_adversary, new_block):
        new_block['Header']['hash'] = encryption_module.hashing_function(new_block['Body'])
        return new_block

    def miners_trigger(self, simdata):
        for counter in range(simdata.expected_chain_length):
            randomly_chosen_miners = []
            x = int(round((len(simdata.miner_list) / 2), 0))
            j = 0
            miners_with_empty_mempools = []
            while j < x:
                if len(miners_with_empty_mempools) == len(simdata.miner_list):
                    break
                randomly_chosen_miner = random.choice(simdata.miner_list)
                if randomly_chosen_miner.local_mempool:
                    randomly_chosen_miners.append(randomly_chosen_miner)
                    j += 1
                elif randomly_chosen_miner not in miners_with_empty_mempools:
                    miners_with_empty_mempools.append(randomly_chosen_miner)
            if len(miners_with_empty_mempools) == len(simdata.miner_list):
                break
            biggest_stake = 0
            final_chosen_miner = simdata.miner_list[0]
            temp_file_py = modification.read_file('temporary/miners_stake_amounts.json')
            for chosen_miner in randomly_chosen_miners:
                stake = temp_file_py[chosen_miner.address]
                if stake > biggest_stake:
                    biggest_stake = stake
                    final_chosen_miner = chosen_miner
            for entity in simdata.miner_list:
                entity.next_pos_block_from = final_chosen_miner.address
            final_chosen_miner.build_block(simdata)
            output.simulation_progress(counter, simdata.expected_chain_length)

    def block_is_valid(self, type_of_consensus, new_block, top_block, next_pos_block_from, miner_list, delegates):
        condition_1 = new_block['Header']['hash'] == encryption_module.hashing_function(new_block['Body'])
        condition_2 = new_block['Body']['previous_hash'] == top_block['Header']['hash']
        condition_3 = new_block['Header']['generator_id'] == next_pos_block_from
        if condition_1 and condition_2 and condition_3:
            return True
        return False

class PoA(ConsensusAlgorithmBase):
    name = 'Proof of Authority (PoA)'
    orderNo = "3"

    def prepare_necessary_files(self):
        pass

    def generate_new_block(self, transactions, generator_id, previous_hash, type_of_consensus,
                           AI_assisted_mining_wanted, is_adversary, new_block):
        new_block['Header']['hash'] = encryption_module.hashing_function(new_block['Body'])
        return new_block

    def miners_trigger(self, simdata):
        for counter in range(simdata.expected_chain_length):
            obj = random.choice(simdata.miner_list)
            if obj.local_mempool:
                obj.build_block(simdata)
            output.simulation_progress(counter, simdata.expected_chain_length)

    def block_is_valid(self, type_of_consensus, new_block, top_block, next_pos_block_from, miner_list, delegates):
        condition_1 = new_block['Body']['previous_hash'] == top_block['Header']['hash']
        condition_2 = new_block['Header']['hash'] == encryption_module.hashing_function(new_block['Body'])
        if condition_1 and condition_2:
            for obj in miner_list:
                if obj.address == new_block['Header']['generator_id']:
                    return obj.isAuthorized
        return False

class PoET(ConsensusAlgorithmBase):
    name = 'Proof of Elapsed Time (PoET)'
    orderNo = "4"

    def prepare_necessary_files(self):
        pass

    def generate_new_block(self, transactions, generator_id, previous_hash, type_of_consensus,
                           AI_assisted_mining_wanted, is_adversary, new_block):
        new_block['Header']['hash'] = encryption_module.hashing_function(new_block['Body'])
        new_block['Header']['PoET'] = ''
        return new_block

    def miners_trigger(self, simdata):
        start_time = time.time()
        for obj in simdata.miner_list:
            obj.waiting_times = PoET_server.generate_random_waiting_times(simdata.expected_chain_length, simdata.params.poet_block_time,
                                                                          obj.address)
            private_key, public_key = encryption_module.generate_PKI_keys(simdata.params.Asymmetric_key_length, obj.address + '_key')
        mining_processes = []
        for counter in range(simdata.expected_chain_length):
            least_waiting_time = simdata.params.poet_block_time
            least_waiting_time_for = []
            for obj in simdata.miner_list:
                if PoET_server.network_waiting_times[obj.address][counter + 1] < least_waiting_time:
                    least_waiting_time = PoET_server.network_waiting_times[obj.address][counter + 1]
            for obj in simdata.miner_list:
                if PoET_server.network_waiting_times[obj.address][counter + 1] == least_waiting_time:
                    least_waiting_time_for.append(obj.address)
            time.sleep(least_waiting_time)
            if simdata.params.Parallel_PoW_mining:
                # parallel approach
                for obj in simdata.miner_list:
                    if obj.address in least_waiting_time_for:
                        process = Process(target=obj.build_block, args=(
                            simdata,))
                        process.start()
                        mining_processes.append(process)
                for process in mining_processes:
                    process.join()
            else:
                for obj in simdata.miner_list:
                    if obj.address in least_waiting_time_for:
                        obj.build_block(simdata)
            for obj in simdata.miner_list:
                if obj.local_mempool:
                    now_time_must_be = start_time + ((counter + 1) * simdata.params.poet_block_time)
                    difference = now_time_must_be - time.time()
                    if difference > 0:
                        time.sleep(difference)

    def block_is_valid(self, type_of_consensus, new_block, top_block, next_pos_block_from, miner_list, delegates):
        try:
            expected_block_poet = encryption_module.retrieve_signature_from_saved_key(top_block['Header']['hash'],
                                                                                      new_block['Header'][
                                                                                          'generator_id'])
            condition1 = new_block['Header']['PoET'] == expected_block_poet
            condition2 = new_block['Header']['hash'] == encryption_module.hashing_function(new_block['Body'])
            condition3 = time.time() >= (top_block['Body']['timestamp'] +
                                         PoET_server.network_waiting_times[new_block['Header']['generator_id']][
                                             top_block['Header']['blockNo'] + 1])
            if condition1 and condition2 and condition3:
                return True
        except Exception as e:
            pass
        return False

class DPoS(ConsensusAlgorithmBase):
    name = 'Delegated Proof of Stake (DPoS)'
    orderNo = "5"

    def prepare_necessary_files(self):
        modification.write_file('temporary/miners_stake_amounts.json', {})

    def generate_new_block(self, transactions, generator_id, previous_hash, type_of_consensus,
                           AI_assisted_mining_wanted, is_adversary, new_block):
        new_block['Header']['hash'] = encryption_module.hashing_function(new_block['Body'])
        new_block['Header']['dummy_new_proof'] = super().dummy_proof_generator_function(new_block)
        return new_block

    def miners_trigger(self, simdata):
        for counter in range(simdata.expected_chain_length):
            votes_and_stakes = self.dpos_voting(simdata.miner_list)
            selected_delegates = self.dpos_delegates_selection(votes_and_stakes, simdata.params.number_of_DPoS_delegates)
            for entity in simdata.miner_list:
                entity.delegates = selected_delegates
            processes = []
            for entity in simdata.miner_list:
                if entity.address in entity.delegates:
                    if simdata.params.Parallel_PoW_mining:
                        process = Process(target=entity.build_block, args=(
                            simdata,))
                        process.start()
                        processes.append(process)
                    else:
                        entity.build_block(simdata)
            for process in processes:
                process.join()
            output.simulation_progress(counter, simdata.expected_chain_length)

    def block_is_valid(self, type_of_consensus, new_block, top_block, next_pos_block_from, miner_list, delegates):
        try:
            condition1 = new_block['Header']['generator_id'] in delegates
            condition2 = new_block['Header']['hash'] == encryption_module.hashing_function(new_block['Body'])
            condition3 = new_block['Body']['previous_hash'] == top_block['Header']['hash']
            if condition1 and condition2 and condition3:
                return True
        except:
            pass
        return False

    def dpos_voting(self, the_miners_list):
        temp_file_py = modification.read_file('temporary/miner_wallets_log.json')
        votes_and_stakes = {}
        for miner in the_miners_list:
            votes_and_stakes[miner.address] = {}
        for miner in the_miners_list:
            chosen_miner = miner
            while chosen_miner == miner:
                chosen_miner = random.choice(the_miners_list)
            miner.dpos_vote_for = chosen_miner.address
            max_amount_to_be_staked = temp_file_py[miner.address]
            miner.amount_to_be_staked = random.randint(0, max_amount_to_be_staked)
            votes_and_stakes[chosen_miner.address][miner.address] = miner.amount_to_be_staked
        return votes_and_stakes

    def dpos_delegates_selection(self, votes_and_stakes, number_of_delegates):
        top_delegates = []
        while len(top_delegates) < number_of_delegates:
            top_delegate = None
            highest_num_votes = 0
            for entry in votes_and_stakes:
                if len(votes_and_stakes[entry]) > highest_num_votes:
                    highest_num_votes = len(votes_and_stakes[entry])
                    top_delegate = entry
            top_delegates.append(top_delegate)
            votes_and_stakes.pop(top_delegate)
        return top_delegates


# MODIFIABLE PART:

class Dummy(ConsensusAlgorithmBase):
    # 1- add a number and a name of the new consensus algorithm (all strings)
    # as "name" and "orderNo":
    name = 'Example New CA'
    orderNo = "6"

    # 2-if your consensus algorithm requires other files to refer to while miners are
    # processing TXs and Blocks, add them to the
    # "prepare_necessary_files" function. Check the 'modification.py' file in this
    # project to utilize already implemented functions
    def prepare_necessary_files(self):
        super().prepare_necessary_files()

    # 3- the 'generate_new_block' generates a standard-like block. You can add more attributes
    # to your new consensus blocks by adding your own logic for generation,
    # see implemented CAs implementation for reference above --^
    def generate_new_block(self, transactions, generator_id, previous_hash, type_of_consensus,
                           AI_assisted_mining_wanted, is_adversary, new_block):
        pass

    # 4- the 'miners_trigger' function triggers the miners to start mining/minting new blocks.
    # add your own logic to this function for triggering miners,
    # see implemented CAs implementation for reference above --^
    def miners_trigger(self, simdata):
        super().trigger_dummy_miners(simdata)

    # 5- Add miner validation strategy in a 'block_is_valid' function.
    # The function MUST return either True or False.
    # The parameters passed to this function differ depending on a) the application of the consensus, and b) the validation criteria.
    # to see some examples, refer to the 'block_is_valid' functions in the area above^^^^^^.
    # Preferred approach to implement this function is to define the conditions to check. If all conditions were met,
    # the function would return true. Otherwise it shall return False. Note that this is a Proof-based consensus approach.
    # If other approach is to be implemented (e.g. PBFT), other functions and related variables need to be added/modified
    # in the 'miner.py' file in this project.
    def block_is_valid(self, type_of_consensus, new_block, top_block, next_pos_block_from, miner_list, delegates):
        super().dummy_block_is_valid(new_block)

    # 6- (OPTIONAL) Add other type of proof that could be validated by the 'block_is_valid' function.
    # To do that, you can implement a function that generates the proof as in the
    # 'pow_mining' function in the NON-MODIFIABLE area above^^^^^^. Once implemented, the
    # 'block_is_valid' function must be modified accordingly so that valid blocks only are added.
    def dummy_proof_generator_function(self, block):
        return encryption_module.hashing_function(block['Body'])