import mempool
import output
import encryption_module
import time
import copy
import random

from abc import abstractmethod, ABC



class ConsensusAlgorithmBase(ABC):
    name : str
    orderNo : str

    @staticmethod
    def choose_consensus(consensus_algorithms):
        while True:
            cas = {ca.orderNo: ca.name for ca in consensus_algorithms}
            output.choose_consensus(cas)
            num_of_consensus = input()
            if num_of_consensus in cas:
                num_of_consensus = int(num_of_consensus)
                break
            else:
                print("Input is incorrect, try again..!")
        return num_of_consensus

    @abstractmethod
    def prepare_necessary_files(self):
        pass

    def generate_new_block_start(self, transactions, generator_id, previous_hash, type_of_consensus, AI_assisted_mining_wanted,
                           is_adversary):
        new_block = {'Header': {'generator_id': generator_id,
                                'hash': '',
                                'blockNo': 0},
                     'Body': {'transactions': transactions,
                              'nonce': 0,
                              'previous_hash': previous_hash,
                              'timestamp': time.time()}}

        return self.generate_new_block(transactions, generator_id, previous_hash, type_of_consensus, AI_assisted_mining_wanted,
                           is_adversary, new_block)

    @abstractmethod
    def generate_new_block(self, transactions, generator_id, previous_hash, type_of_consensus, AI_assisted_mining_wanted,
                           is_adversary, new_block):
        pass

    def miners_trigger_start(self, simdata):

        output.mempool_info(mempool.MemPool)
        for obj in simdata.miner_list:
            obj.local_mempool = copy.deepcopy(mempool.MemPool)

        self.miners_trigger(simdata)

    @abstractmethod
    def miners_trigger(self, simdata):
        pass


    @staticmethod
    def trigger_dummy_miners(simdata):
        counter = -1
        for obj in simdata.miner_list:
            if obj.local_mempool:
                obj.build_block(simdata)
                counter += 1
        output.simulation_progress(counter, simdata.expected_chain_length)

    @abstractmethod
    def block_is_valid(self, type_of_consensus, new_block, top_block, next_pos_block_from, miner_list, delegates):
        pass

    def accumulate_transactions(self, num_of_tx_per_block, this_mem_pool, blockchain_function, miner_address):
        lst_of_transactions = []
        if blockchain_function == 2:
            if this_mem_pool:
                try:
                    lst_of_transactions = random.choice(this_mem_pool)
                    lst_of_transactions.append(eval(lst_of_transactions[2]))
                    produced_transaction = [
                        'End-user address: ' + str(lst_of_transactions[0]) + '.' + str(lst_of_transactions[1]),
                        'Requested computational task: ' + str(lst_of_transactions[2]), 'Result: '
                        + str(lst_of_transactions[4]), "miner: " + str(miner_address)]
                    return produced_transaction
                except:
                    print("error in accumulating new TXs:")
        else:
            i = 0
            while i < num_of_tx_per_block:
                if this_mem_pool:
                    try:
                        selected_tx = random.choice(this_mem_pool)
                        if selected_tx not in lst_of_transactions:
                            lst_of_transactions.append(selected_tx)
                        this_mem_pool.remove(selected_tx)
                        i += 1
                    except:
                        print("error in accumulating full new list of TXs")
                        break
                else:
                    output.mempool_is_empty()
                    break
        return lst_of_transactions

    @staticmethod
    def dummy_block_is_valid(block):
        return block['Header']['dummy_new_proof'] == encryption_module.hashing_function(block['Body'])

    @staticmethod
    def dummy_proof_generator_function(block):
        return encryption_module.hashing_function(block['Body'])
