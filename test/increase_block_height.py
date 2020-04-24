import json
import time


def increase_block_height():
    """
        Only executed in Debug mode
        To artificially increase the block height status.json is modified
    """
    print("Increasing local Block Height ...")
    while True:
        with open('status.json') as json_read_file:
            node_data = json.load(json_read_file)

        block_height = node_data['result']['sync_info']['latest_block_height']
        new_block_height = int(block_height) + 1
        node_data['result']['sync_info']['latest_block_height'] = str(new_block_height)

        with open('status.json', 'w') as json_write_file:
            json.dump(node_data, json_write_file)
        time.sleep(5)


if __name__ == '__main__':
    increase_block_height()
