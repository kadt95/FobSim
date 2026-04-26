import blockchain
import time
import output
import encryption_module
import modification


class Miner:
    def __init__(self, address, trans_delay, gossiping):
        self.address = "Miner_" + str(address)
        self.top_block = {}
        self.isAuthorized = False
        self.next_pos_block_from = self.address
        self.neighbours = set()
        self.trans_delay = trans_delay/1000
        self.gossiping = gossiping
        self.waiting_times = {}
        self.dpos_vote_for = None
        self.amount_to_be_staked = None
        self.delegates = None
        self.adversary = False
        self.local_mempool = []
        self.successful_gossip=False

    def build_block(self, simdata):
        if simdata.type_of_consensus == 3 and not self.isAuthorized:
            output.unauthorized_miner_msg(self.address)
        elif simdata.type_of_consensus == 4:
            waiting_time = (self.top_block['Body']['timestamp'] + self.waiting_times[self.top_block['Header']['blockNo'] + 1]) - time.time()
            if waiting_time <= 0:
                self.continue_building_block(simdata)
        else:
            self.continue_building_block(simdata)

    def continue_building_block(self, simdata):
        accumulated_transactions = simdata.chosen_consensus.accumulate_transactions(simdata.params.numOfTXperBlock, self.local_mempool, simdata.blockchainFunction,
                                                                                self.address)
        if accumulated_transactions:
            transactions = accumulated_transactions
            new_block = self.abstract_block_building(transactions, simdata)
            output.block_info(new_block, simdata.type_of_consensus)
            if simdata.blockchainFunction == 2:
                tx = new_block["Body"]["transactions"][1].split()[-1]
                for transaction in self.local_mempool:
                    if transaction[2] == tx:
                        try:
                            self.local_mempool.remove(transaction)
                            break
                        except Exception as e:
                            pass
            else:
                for tx in transactions:
                    try:
                        self.local_mempool.remove(tx)
                    except Exception as e:
                        pass
            time.sleep(self.trans_delay)
            for elem in simdata.miner_list:
                if elem.address in self.neighbours:
                    elem.receive_new_block(new_block, simdata)

    def abstract_block_building(self, transactions, simdata):
        if simdata.blockchainFunction == 3:
            transactions = self.validate_transactions(transactions, "generator")
        if self.gossiping:
            self.gossip(simdata.blockchainFunction, simdata.miner_list)
        new_block = simdata.chosen_consensus.generate_new_block_start(transactions, self.address,
                                                            self.top_block['Header']['hash'], simdata.type_of_consensus,
                                                            simdata.AI_assisted_mining_wanted, self.adversary)
        if simdata.type_of_consensus == 4:
            new_block['Header']['PoET'] = encryption_module.retrieve_signature_from_saved_key(
                new_block['Body']['previous_hash'], self.address)
        return new_block

    def receive_new_block(self, new_block, simdata):
        block_already_received = False
        self.successful_gossip=False
        local_chain_temporary_file = modification.read_file(str("temporary/" + self.address + "_local_chain.json"))
        # print("a new block is received from " + str(new_block['generator_id']))
        condition_1 = (len(local_chain_temporary_file) == 0) and (new_block['Header']['generator_id'] == 'The Network')
        if condition_1:
            self.add(new_block, simdata.blockchainFunction, simdata.expected_chain_length, simdata.miner_list)
        else:
            if self.gossiping:
                self.gossip(simdata.blockchainFunction, simdata.miner_list)
            list_of_hashes_in_local_chain = []
            for key in local_chain_temporary_file:
                read_hash = local_chain_temporary_file[key]['Header']['hash']
                list_of_hashes_in_local_chain.append(read_hash)
                if new_block['Header']['hash'] == read_hash:
                    block_already_received = True
                    break
            if not block_already_received:
                if simdata.chosen_consensus.block_is_valid(simdata.type_of_consensus, new_block, self.top_block, self.next_pos_block_from, simdata.miner_list, self.delegates) or (self.successful_gossip and self.top_block==new_block):
                    self.add(new_block, simdata.blockchainFunction, simdata.expected_chain_length, simdata.miner_list)
                    time.sleep(self.trans_delay)
                    if simdata.blockchainFunction == 2:
                        tx = new_block["Body"]["transactions"][1].split()[-1]
                        for transaction in self.local_mempool:
                            if transaction[2] == tx:
                                self.local_mempool.remove(transaction)
                                break
                    else:
                        for tx in new_block["Body"]["transactions"]:
                            try:
                                self.local_mempool.remove(tx)
                            except Exception as e:
                                pass
                    for elem in simdata.miner_list:
                        if elem.address in self.neighbours:
                            elem.receive_new_block(new_block, simdata)

    def validate_transactions(self, list_of_new_transactions, miner_role):
        user_wallets_temporary_file = modification.read_file(str("temporary/" + self.address + "_users_wallets.json"))
        if list_of_new_transactions:
            for key in user_wallets_temporary_file:
                for transaction in list_of_new_transactions:
                    if miner_role == "receiver":
                        if key == (str(transaction[1]) + "." + str(transaction[2])):
                            if user_wallets_temporary_file[key]['wallet_value'] >= transaction[0]:
                                user_wallets_temporary_file[key]['wallet_value'] -= transaction[0]
                            else:
                                return False
                        if key == (str(transaction[3]) + "." + str(transaction[4])):
                            user_wallets_temporary_file[key]['wallet_value'] += transaction[0]
                    if miner_role == "generator" and key == (str(transaction[1]) + "." + str(transaction[2])):
                        if user_wallets_temporary_file[key]['wallet_value'] < transaction[0]:
                            output.illegal_tx(transaction, user_wallets_temporary_file[key]['wallet_value'])
                            del transaction
        if miner_role == "generator":
            return list_of_new_transactions
        if miner_role == "receiver":
            modification.rewrite_file(str("temporary/" + self.address + "_users_wallets.json"), user_wallets_temporary_file)
            return True

    def add(self, block, blockchain_function, expected_chain_length, list_of_miners):
        ready = False
        local_chain_temporary_file = modification.read_file("temporary/" + self.address + "_local_chain.json")
        if len(local_chain_temporary_file) == 0:
            ready = True
        else:
            condition = blockchain_function == 3 and self.validate_transactions(block['Body']['transactions'], "receiver")
            if blockchain_function != 3 or condition:
                if block['Body']['previous_hash'] == self.top_block['Header']['hash']:
                    blockchain.report_a_successful_block_addition(block['Header']['generator_id'], block['Header']['hash'])
                    # output.block_success_addition(self.address, block['generator_id'])
                    ready = True
        if ready:
            block['Header']['blockNo'] = len(local_chain_temporary_file)
            self.top_block = block
            local_chain_temporary_file[str(len(local_chain_temporary_file))] = block
            modification.rewrite_file(str("temporary/" + self.address + "_local_chain.json"), local_chain_temporary_file)
            self.remove_confirmed_txs_from_local_mempool(block,blockchain_function)
            if self.gossiping:
                self.update_global_longest_chain(local_chain_temporary_file, blockchain_function, list_of_miners)

    def remove_confirmed_txs_from_local_mempool(self, confirmed_bock,blockchain_function):
        if confirmed_bock["Header"]["generator_id"] != "The Network":
            try:
                if blockchain_function == 2:
                    tx = confirmed_bock["Body"]["transactions"][1].split()[-1]
                    for transaction in self.local_mempool:
                        if transaction[2] == tx:
                            self.local_mempool.remove(transaction)
                            break
                else:
                    for tx in confirmed_bock["Body"]["transactions"]:
                        self.local_mempool.remove(tx)
            except Exception as e:
                pass

    def gossip(self, blockchain_function, list_of_miners):
        local_chain_temporary_file = modification.read_file(str("temporary/" + self.address + "_local_chain.json"))
        temporary_global_longest_chain = modification.read_file('temporary/longest_chain.json')
        condition_1 = len(temporary_global_longest_chain['chain']) > len(local_chain_temporary_file)
        condition_2 = self.global_chain_is_confirmed_by_majority(temporary_global_longest_chain['chain'], len(list_of_miners))
        if condition_1 and condition_2:
            confirmed_chain = temporary_global_longest_chain['chain']
            confirmed_chain_from = temporary_global_longest_chain['from']
            modification.rewrite_file(str("temporary/" + self.address + "_local_chain.json"), confirmed_chain)
            self.top_block = confirmed_chain[str(len(confirmed_chain) - 1)]
            self.successful_gossip=True
            output.local_chain_is_updated(self.address, len(confirmed_chain))
            if blockchain_function == 3:
                user_wallets_temp_file = modification.read_file(str("temporary/" + confirmed_chain_from + "_users_wallets.json"))
                modification.rewrite_file(str("temporary/" + self.address + "_users_wallets.json"), user_wallets_temp_file)

    def global_chain_is_confirmed_by_majority(self, global_chain, no_of_miners):
        chain_is_confirmed = True
        temporary_confirmations_log = modification.read_file('temporary/confirmation_log.json')
        for block in global_chain:
            condition_0 = block != '0'
            if condition_0:
                condition_1 = not (global_chain[block]['Header']['hash'] in temporary_confirmations_log)
                if condition_1:
                    chain_is_confirmed = False
                    break
                else:
                    condition_2 = temporary_confirmations_log[global_chain[block]['Header']['hash']]['votes'] <= (no_of_miners / 2)
                    if condition_2:
                        chain_is_confirmed = False
                        break
        return chain_is_confirmed

    def update_global_longest_chain(self, local_chain_temporary_file, blockchain_function, list_of_miners):
        temporary_global_longest_chain = modification.read_file('temporary/longest_chain.json')
        if len(temporary_global_longest_chain['chain']) < len(local_chain_temporary_file):
            temporary_global_longest_chain['chain'] = local_chain_temporary_file
            temporary_global_longest_chain['from'] = self.address
            modification.rewrite_file('temporary/longest_chain.json', temporary_global_longest_chain)
        else:
            if len(temporary_global_longest_chain['chain']) > len(local_chain_temporary_file) and self.gossiping:
                self.gossip(blockchain_function, list_of_miners)
