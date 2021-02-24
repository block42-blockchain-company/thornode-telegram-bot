import os
import subprocess

from pymongo import MongoClient

from constants.globals import MONGO_URL, MONGO_SNAPSHOT_HEIGHT, NATIVE_DEPLOYMENT, MONGO_CONTAINER_NAME, logger

client = MongoClient(f"mongodb://{MONGO_URL}:27017/")


def init_mongo_db():
    spin_up_mongo_db()

    # check if db exists
    dbs = client.list_database_names()
    if "thorchain" in dbs:
        docs = client["thorchain"]["config"].find_one()
        block_height = docs["block_height_end"]

        # check if db is more advanced than snapshot
        if block_height > MONGO_SNAPSHOT_HEIGHT:
            logger.info(f"Continue parsing thorchain from {block_height}")
            return

    # load snapshot in db
    logger.info("Loading snapshot to container")
    os.system(f"docker cp ../snapshot {MONGO_CONTAINER_NAME}:/snapshot")

    logger.info("Restoring db from snapshot")
    os.system(f"docker exec {MONGO_CONTAINER_NAME} mongorestore ./snapshot")


def spin_up_mongo_db():
    # check if bot runs not in container
    if NATIVE_DEPLOYMENT:
        logger.info("Running in debug... Setting up environment")
        os.environ.setdefault("TM_CLIENT_DEV", "true")
        get_container_names = "docker ps --format '{{.Names}}'"
        result = subprocess.check_output(get_container_names, shell=True)
        if b"mongodb" not in result:
            logger.info("Spinning up new MongoDB container")
            os.system("docker run --name mongodb -p 27017:27017 mongo:latest &")
        else:
            logger.info("Using existing MongoDB container")

    else:
        logger.info("Assuming bot runs dockerized. Using default config.")


def get_current_churn_cycle():
    config = client["thorchain"]["config"]
    docs = config.find()
    for document in docs:
        return document


def get_churn_cycles(block_height_start: int, block_height_end: int):
    churn_cycles = []
    churns = client["thorchain"]["churns"]
    docs = churns.find({"block_height_end": {"$gte": block_height_start},
                        "block_height_start": {"$lte": block_height_end}})

    for document in docs:
        churn_cycles.append(document)

    # The current churn cycle is not stored along with the completed ones
    config = client["thorchain"]["config"]
    docs = config.find({"block_height_end": {"$gte": block_height_start},
                        "block_height_start": {"$lte": block_height_end}})
    for document in docs:
        churn_cycles.append(document)

    return churn_cycles


def get_churn_cycles_with_node(block_height_start: int, block_height_end: int, node_address: str):
    effective_churn_circles = []
    churns = client["thorchain"]["churns"]
    docs = churns.find({"block_height_end": {"$gte": block_height_start},
                        "block_height_start": {"$lte": block_height_end},
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
