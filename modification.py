import random
import json
import os
import shutil
import time
import multiprocessing


def initiate_files(simdata):
    for filename in os.listdir('temporary'):
        if filename == ".gitignore":
            continue
        file_path = os.path.join('temporary', filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
    simdata.locks["confirmation_log"] = multiprocessing.Lock()
    write_file('temporary/confirmation_log.json', {},simdata.locks["confirmation_log"])
    simdata.locks["miner_wallets_log"] = multiprocessing.Lock()
    write_file('temporary/miner_wallets_log.json', {},simdata.locks["miner_wallets_log"])
    if simdata.params.gossip_activated:
        simdata.locks["longest_chain"] = multiprocessing.Lock()
        write_file('temporary/longest_chain.json', {'chain': {}, 'from': 'Miner_1'},simdata.locks["longest_chain"])


def read_file(file_path,lock):
    with lock:
            with open(file_path, 'r') as f:
                file = json.load(f)
            return file


def write_file(file_path, contents, lock):
    with lock:
            with open(file_path, 'w') as f:
                json.dump(contents, f, indent=4)

def rewrite_file(file_path, new_version, lock):
    with lock:
        with open(file_path, "w") as f:
            json.dump(new_version, f, indent=4)
            f.flush()
            os.fsync(f.fileno())