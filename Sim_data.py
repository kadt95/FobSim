from contextlib import nullcontext
from math import ceil
import modification




class SimData:
    class Parameters:
        def __init__(self, data):
            self.number_of_miner_neighbours = data["number_of_each_miner_neighbours"]
            self.NumOfFogNodes = data["NumOfFogNodes"]
            self.NumOfTaskPerUser = data["NumOfTaskPerUser"]
            self.NumOfMiners = data["NumOfMiners"]
            self.numOfTXperBlock = data["numOfTXperBlock"]
            self.num_of_users_per_fog_node = data["num_of_users_per_fog_node"]
            self.gossip_activated = data["Gossip_Activated"]
            self.Automatic_PoA_miners_authorization = data["Automatic_PoA_miners_authorization?"]
            self.Parallel_PoW_mining = data["Parallel_PoW_mining?"]
            self.delay_between_fog_nodes = data["delay_between_fog_nodes"]
            self.delay_between_end_users = data["delay_between_end_users"]
            self.poet_block_time = data['poet_block_time']
            self.Asymmetric_key_length = data['Asymmetric_key_length']
            self.number_of_DPoS_delegates = data['Num_of_DPoS_delegates']
            self.initial_wallet_value = data['miners_initial_wallet_value']
    def __init__(self, rawparameters):
        self.params  = SimData.Parameters(rawparameters)
        self.list_of_end_users = []
        self.fogNodes = []
        self.transactions_list = []
        self.list_of_authorized_miners = []
        self.blockchainFunction = 0
        self.blockchainPlacement = 0
        self.blockchain_functions = ['1', '2', '3', '4']
        self.blockchain_placement_options = ['1', '2']
        self.expected_chain_length = ceil((self.params.num_of_users_per_fog_node * self.params.NumOfTaskPerUser * self.params.NumOfFogNodes) / self.params.numOfTXperBlock)
        self.trans_delay = 0
        self.user_informed = False
        self.cons_algorithms = None
        self.type_of_consensus = None
        self.chosen_consensus = None
        self.miner_list = None
        self.AI_assisted_mining_wanted = None
        self.locks = {}

    def consensus_setup(self,cabase):
        self.cons_algorithms = sorted(cabase.__subclasses__(), key=lambda ca: int(ca.orderNo))
        self.type_of_consensus = cabase.choose_consensus(self.cons_algorithms)
        self.chosen_consensus = self.cons_algorithms[self.type_of_consensus - 1]()
        self.chosen_consensus.prepare_necessary_files()

data = modification.read_file("Sim_parameters.json",nullcontext())
simdata = SimData(data)