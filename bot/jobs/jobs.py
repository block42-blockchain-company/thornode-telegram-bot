from jobs.other_nodes_jobs import *
from jobs.thorchain_network_jobs import check_network_security_job, check_thorchain_constants_job
from jobs.thorchain_node_jobs import *


def setup_bot_jobs(dispatcher):
    dispatcher.job_queue.run_repeating(general_bot_checks,
                                       interval=JOB_INTERVAL_IN_SECONDS)
    dispatcher.job_queue.run_repeating(check_bitcoin_height_increase_job,
                                       interval=BitcoinNode.max_time_for_block_height_increase_in_seconds)
    dispatcher.job_queue.run_repeating(check_ethereum_height_increase_job,
                                       interval=EthereumNode.max_time_for_block_height_increase_in_seconds)

    dispatcher.job_queue.run_repeating(check_other_nodes_syncing_job,
                                       interval=120)

    dispatcher.job_queue.run_repeating(network_checks,
                                       interval=3600)

    dispatcher.job_queue.run_repeating(network_checks,
                                       interval=3600)


def start_user_job(context, chat_id):
    context.job_queue.run_repeating(user_specific_checks,
                                    interval=JOB_INTERVAL_IN_SECONDS,
                                    context={
                                        'chat_id': chat_id,
                                        'chat_data': context.chat_data
                                    })

    context.chat_data['job_started'] = True


def user_specific_checks(context):
    """
    Periodic checks of nodes that the user monitors
    """

    check_versions_status(context)
    check_thornodes(context)


def general_bot_checks(context):
    """
    Periodic checks that are interesting for all users
    """

    check_churning(context)
    check_solvency(context)
    check_other_nodes_health(context)


def network_checks(context):
    """
    Periodic checks that are interesting for all users but are rarely changing -> lower frequency
    """
    check_thorchain_constants_job(context)
    check_network_security_job(context)
