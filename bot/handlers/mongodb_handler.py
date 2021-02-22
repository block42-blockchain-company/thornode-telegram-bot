from pymongo import MongoClient

from constants.globals import MONGO_URL

client = MongoClient(f"mongodb://{MONGO_URL}:27017/")


def get_current_churn_cycle():
    config = client["thorchain"]["config"]
    docs = config.find()
    for document in docs:
        return document


def get_churn_cycles_with_node(block_height_start: int, block_height_end: int, node_address: str):
    effective_churn_circles = []
    churns = client["thorchain"]["churns"]
    docs = churns.find({"block_height_end": {"$gte": block_height_start},
                        "block_height_start": {"$lt": block_height_end},
                        "validator_set.address": {"$eq": node_address}})

    for document in docs:
        effective_churn_circles.append(document)

    # The current churn cycle is not stored along with the completed ones
    config = client["thorchain"]["config"]
    docs = config.find({"block_height_end": {"$gte": block_height_start},
                        "block_height_start": {"$lt": block_height_end},
                        "validator_set.address": {"$eq": node_address}})
    for document in docs:
        effective_churn_circles.append(document)

    return effective_churn_circles
