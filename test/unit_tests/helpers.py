class ContextMock:
    bot_data = {}


class JobContextMock:
    bot_data = {}


node_mock = {'node_address': 'thor92', 'status': 'standby', 'pub_key_set': {
    'secp256k1': 'tthorpub1addwnpepqtzh5uyjwv2l0c7vecyslr0a54hz5k5j65f8q0486jhehu6epr69slwq0w6',
    'ed25519': 'tthorpub1addwnpepqtzh5uyjwv2l0c7vecyslr0a54hz5k5j65f8q0486jhehu6epr69slwq0w6'},
             'validator_cons_pub_key': 'tthorcpub1zcjduepqayw85fwtgsarpvf22q4lhc9wqheaxdjfcak4vfkrm2v3asc4davsnk0r6v',
             'bond': '3000128905072', 'active_block_height': '0',
             'bond_address': 'tbnb157drnscq264zu7m2hqnw7s2c6h9zwleaszvnd7', 'status_since': '120248',
             'signer_membership': ['tthorpub1addwnpepq030w3cdynxpxcsc9t74xp5ktakpkmgt8rww3hdd8h8lt770p0nu6xyk990',
                                   'tthorpub1addwnpepqwk0rlvu9x42nr06g8zsetp8r92l48rj9cwwef2386p9wf2r07vuszsauqs',
                                   'tthorpub1addwnpepq2sj8k5u7d9trzk2epax2489anfgqgvxya8h93hmsylmut24fgrvwwtfrf4',
                                   'tthorpub1addwnpepq20n4meytypxsuj5drdq42fyyftrqgyhxxdsj6r78vd702a9gjvfj7ukh5e',
                                   'tthorpub1addwnpepqvj6qdnnwd5lh5njwmhfa2hyjrakk48wschp3p7lswrp8tr6xywkxqtn9sx',
                                   'tthorpub1addwnpepq2dn8pgs2qgd5qh8qwclpsdg5lhzefjy9dyvte94vnne0vzc9ra45p2pgvq',
                                   'tthorpub1addwnpepq0lklck528mw9krmmrhhfdff5lu5hsl7wa5pw4d2c796q4m7znknqganm02',
                                   'tthorpub1addwnpepqvt52kj8tz9mhjdu9hns57cwahnc3zk63vlrpgvrjpa569np0nsnupu3cc9',
                                   'tthorpub1addwnpepqg29knr2hfz56332xp44j27dyqsahvd6vf0tkysstd5la3l25wcq56u0pg8',
                                   'tthorpub1addwnpepqfsgcsc06gp4auudysdnhqdcs47s3gesjdm2djg4769fsld3ach2js8rej7',
                                   'tthorpub1addwnpepq2r4qsrtqkrn4a7d09g8samlw0vssacftew0cqkjxnv2l57a7fzcjwctumf',
                                   'tthorpub1addwnpepqgr4rheqtu2dxeejepj0qt8ulv39yw47w4s0sg9g4y3evfsvtcv2cjh6dza',
                                   'tthorpub1addwnpepq07guannevz9v97gwf47mcgjzsdxp3g4vslhme6yqq07d65duwlr5v6ptpn',
                                   'tthorpub1addwnpepqgwqdsfnvtrwwx7z4z9rp2x9237ygdpgzlk3cmtu3cjygx3vees2v3040tc',
                                   'tthorpub1addwnpepqwj7mhvydfh0akkrqxvdgvpd2e7lyldkwua5m2cfn3p4csgwnccywp0hnuf',
                                   'tthorpub1addwnpepqvk5nmdt7xsthjm239f5h87vjc05gjrr3ej0m2u2hj8ury367zwvjrx9vyd',
                                   'tthorpub1addwnpepqvf7g09xw9nlp4kfynlrdugu06z7h3vzevcxdykmnywnww5e3mkw7j7r4ne',
                                   'tthorpub1addwnpepqf3fvqa6x0zkt9hg9xs0y6sukljcnm4rt9wwjuc7cgh8zar8lqss70k7fws',
                                   'tthorpub1addwnpepqvfnua65rslcdhm5y6v0teswzt2hpmqwd2hcg7u6texsme3dg348uwup277',
                                   'tthorpub1addwnpepqgv73cx6xuyvj274sfgs38ztxkc9svn0mrj926y4a00qhq6e0zelkzme954',
                                   'tthorpub1addwnpepqg5pxj8z9ykhljlaqdyyalm808qpk6d8xgqjzkhv4x9lrqkhj7832qu68ph',
                                   'tthorpub1addwnpepqg8euyz34jg86u2acylv4tyzdpu9dgf98rvxzql534sjx72zcdy76v7g7uc',
                                   'tthorpub1addwnpepqtdpz9x4qs2wm5qc4nx5u0qf5zlc5rcrvt4es3l5k8usq3m8zpjjkak47s4',
                                   'tthorpub1addwnpepq0n3a99pwv76krk7ulpx3dztxhakhfj0xe072hv0s3gyul7yjqyjvywqkfe',
                                   'tthorpub1addwnpepq0k0rqfykz7guk4hj4rt69da03q56qrgu9p869hs7fs07jd3gefnsfts7cq',
                                   'tthorpub1addwnpepqtyrv8acpfavppuvqqa4yntz7236xd28p654j6ac3kkalp502f5rx587k72',
                                   'tthorpub1addwnpepqvvh9399nfkks4qgepm2t3lfal0nppjr3pqp237nu50kawvghmjgy0y7t66',
                                   'tthorpub1addwnpepq2get95uscltsgnua7hd3t25hkuhl5l6qq6ryt0kzd0s3x0aarruzja4m3k',
                                   'tthorpub1addwnpepqvty09p9j8ufg7ze8ewrvzptxxel0mndveql9cmzvw7ltjktchfn7uax6jy',
                                   'tthorpub1addwnpepqv63mq6e0h9yqdk43vq4freyzh3la5el3wvsr4uy0n7duz22hwulznnd95c',
                                   'tthorpub1addwnpepqw9vnnvkmjmdcm3fxr3kfm4md32lkjst96tmyz8aa7rqxprwrzcdsywgcnk',
                                   'tthorpub1addwnpepqwqsdpvfxqudg2cw27ygran4axqgswka2azawrnw920azx5l9e9d76a6728',
                                   'tthorpub1addwnpepqtdaquhuzezysjl2suauw35rrcshlpuf5rayzpfnky48l5wazt0ewhv9qcq'],
             'requested_to_leave': False, 'forced_to_leave': False, 'leave_height': '118800', 'ip_address': 'localhost',
             'version': '0.7.2', 'slash_points': '329',
             'jail': {'node_address': 'tthor14pncj84nsda4x39y4h8acwexagff23dzgupzel', 'release_height': '120188',
                      'reason': 'failed to perform keysign'}, 'current_award': '44187532', 'alias': 'Thor-1',
             'last_notification_timestamp': 1607008058.286409, 'notification_timeout_in_seconds': 15}

churn_cycles_mock_daily = [
    {
            "_churn_number": 17,
            "block_height_start": 484292,
            "block_height_end": 487791,
            "total_added_rewards": 600000000,
            "validator_set": [
                {
                    "address": "thor18md2p592zdkn440rfd3y5c26jencsryql75kep",
                    "slashpoints": 0
                },
                {
                    "address": "thor13a45mdaac40v0yty3ndm7f04nkmrcx4pf8an0v",
                    "slashpoints": 0
                },
                {
                    "address": "thor1kg57w3z7c5jh06vnxwzmugfh6urc4zezl3kvch",
                    "slashpoints": 0
                }
            ]
        },
    {
            "_churn_number": 20,
            "block_height_start": 496500,
            "block_height_end": 500000,
            "total_added_rewards": 600000000,
            "validator_set": [
                {
                    "address": "thor18md2p592zdkn440rfd3y5c26jencsryql75kep",
                    "slashpoints": 0
                },
                {
                    "address": "thor13a45mdaac40v0yty3ndm7f04nkmrcx4pf8an0v",
                    "slashpoints": 0
                },
                {
                    "address": "thor1kg57w3z7c5jh06vnxwzmugfh6urc4zezl3kvch",
                    "slashpoints": 0
                }
            ]
        }]


churn_cycles_mock_weekly = [
    {
        "_churn_number": 16,
        "block_height_start": 480792,
        "block_height_end": 484291,
        "total_added_rewards": 600000000,
        "validator_set": [
            {
                "address": "thor18md2p592zdkn440rfd3y5c26jencsryql75kep",
                "slashpoints": 0
            },
            {
                "address": "thor13a45mdaac40v0yty3ndm7f04nkmrcx4pf8an0v",
                "slashpoints": 0
            },
            {
                "address": "thor1kg57w3z7c5jh06vnxwzmugfh6urc4zezl3kvch",
                "slashpoints": 0
            }
        ]
    },
    {
        "_churn_number": 17,
        "block_height_start": 484292,
        "block_height_end": 487791,
        "total_added_rewards": 600000000,
        "validator_set": [
            {
                "address": "thor18md2p592zdkn440rfd3y5c26jencsryql75kep",
                "slashpoints": 0
            },
            {
                "address": "thor13a45mdaac40v0yty3ndm7f04nkmrcx4pf8an0v",
                "slashpoints": 0
            },
            {
                "address": "thor1kg57w3z7c5jh06vnxwzmugfh6urc4zezl3kvch",
                "slashpoints": 0
            }
        ]
    },
    {
            "_churn_number": 20,
            "block_height_start": 496500,
            "block_height_end": 500000,
            "total_added_rewards": 600000000,
            "validator_set": [
                {
                    "address": "thor18md2p592zdkn440rfd3y5c26jencsryql75kep",
                    "slashpoints": 0
                },
                {
                    "address": "thor13a45mdaac40v0yty3ndm7f04nkmrcx4pf8an0v",
                    "slashpoints": 0
                },
                {
                    "address": "thor1kg57w3z7c5jh06vnxwzmugfh6urc4zezl3kvch",
                    "slashpoints": 0
                }
            ]
        }]

churn_cycles_mock_monthly = [
    {
        "_churn_number": 5,
        "block_height_start": 29000,
        "block_height_end": 32000,
        "total_added_rewards": 600000000,
        "validator_set": [
            {
                "address": "thor18md2p592zdkn440rfd3y5c26jencsryql75kep",
                "slashpoints": 0
            },
            {
                "address": "thor13a45mdaac40v0yty3ndm7f04nkmrcx4pf8an0v",
                "slashpoints": 0
            },
            {
                "address": "thor1kg57w3z7c5jh06vnxwzmugfh6urc4zezl3kvch",
                "slashpoints": 0
            }
        ]
    },
    {
        "_churn_number": 16,
        "block_height_start": 480792,
        "block_height_end": 484291,
        "total_added_rewards": 600000000,
        "validator_set": [
            {
                "address": "thor18md2p592zdkn440rfd3y5c26jencsryql75kep",
                "slashpoints": 0
            },
            {
                "address": "thor13a45mdaac40v0yty3ndm7f04nkmrcx4pf8an0v",
                "slashpoints": 0
            },
            {
                "address": "thor1kg57w3z7c5jh06vnxwzmugfh6urc4zezl3kvch",
                "slashpoints": 0
            }
        ]
    },
    {
        "_churn_number": 17,
        "block_height_start": 484292,
        "block_height_end": 487791,
        "total_added_rewards": 600000000,
        "validator_set": [
            {
                "address": "thor18md2p592zdkn440rfd3y5c26jencsryql75kep",
                "slashpoints": 0
            },
            {
                "address": "thor13a45mdaac40v0yty3ndm7f04nkmrcx4pf8an0v",
                "slashpoints": 0
            },
            {
                "address": "thor1kg57w3z7c5jh06vnxwzmugfh6urc4zezl3kvch",
                "slashpoints": 0
            }
        ]
    },
    {
            "_churn_number": 20,
            "block_height_start": 496500,
            "block_height_end": 500000,
            "total_added_rewards": 600000000,
            "validator_set": [
                {
                    "address": "thor18md2p592zdkn440rfd3y5c26jencsryql75kep",
                    "slashpoints": 0
                },
                {
                    "address": "thor13a45mdaac40v0yty3ndm7f04nkmrcx4pf8an0v",
                    "slashpoints": 0
                },
                {
                    "address": "thor1kg57w3z7c5jh06vnxwzmugfh6urc4zezl3kvch",
                    "slashpoints": 0
                }
            ]
        }]

churn_cycles_mock_overall = [
    {
            "_churn_number": 0,
            "block_height_start": 1,
            "block_height_end": 3500,
            "total_added_rewards": 600000000,
            "validator_set": [
                {
                    "address": "thor18md2p592zdkn440rfd3y5c26jencsryql75kep",
                    "slashpoints": 0
                },
                {
                    "address": "thor13a45mdaac40v0yty3ndm7f04nkmrcx4pf8an0v",
                    "slashpoints": 0
                },
                {
                    "address": "thor1kg57w3z7c5jh06vnxwzmugfh6urc4zezl3kvch",
                    "slashpoints": 0
                }
            ]
        },
    {
        "_churn_number": 5,
        "block_height_start": 12000,
        "block_height_end": 15000,
        "total_added_rewards": 600000000,
        "validator_set": [
            {
                "address": "thor18md2p592zdkn440rfd3y5c26jencsryql75kep",
                "slashpoints": 0
            },
            {
                "address": "thor13a45mdaac40v0yty3ndm7f04nkmrcx4pf8an0v",
                "slashpoints": 0
            },
            {
                "address": "thor1kg57w3z7c5jh06vnxwzmugfh6urc4zezl3kvch",
                "slashpoints": 0
            }
        ]
    },
    {
        "_churn_number": 16,
        "block_height_start": 480792,
        "block_height_end": 484291,
        "total_added_rewards": 600000000,
        "validator_set": [
            {
                "address": "thor18md2p592zdkn440rfd3y5c26jencsryql75kep",
                "slashpoints": 0
            },
            {
                "address": "thor13a45mdaac40v0yty3ndm7f04nkmrcx4pf8an0v",
                "slashpoints": 0
            },
            {
                "address": "thor1kg57w3z7c5jh06vnxwzmugfh6urc4zezl3kvch",
                "slashpoints": 0
            }
        ]
    },
    {
        "_churn_number": 17,
        "block_height_start": 484292,
        "block_height_end": 487791,
        "total_added_rewards": 600000000,
        "validator_set": [
            {
                "address": "thor18md2p592zdkn440rfd3y5c26jencsryql75kep",
                "slashpoints": 0
            },
            {
                "address": "thor13a45mdaac40v0yty3ndm7f04nkmrcx4pf8an0v",
                "slashpoints": 0
            },
            {
                "address": "thor1kg57w3z7c5jh06vnxwzmugfh6urc4zezl3kvch",
                "slashpoints": 0
            }
        ]
    },
    {
            "_churn_number": 20,
            "block_height_start": 496500,
            "block_height_end": 500000,
            "total_added_rewards": 600000000,
            "validator_set": [
                {
                    "address": "thor18md2p592zdkn440rfd3y5c26jencsryql75kep",
                    "slashpoints": 0
                },
                {
                    "address": "thor13a45mdaac40v0yty3ndm7f04nkmrcx4pf8an0v",
                    "slashpoints": 0
                },
                {
                    "address": "thor1kg57w3z7c5jh06vnxwzmugfh6urc4zezl3kvch",
                    "slashpoints": 0
                }
            ]
        }]

network_data = {"activeBonds":["3251838867462","1224445361097","1007196760386","5412660469344","3925694112419","4347585521357","4150573702493","1360727022258"],"activeNodeCount":8,"blockRewards":{"blockReward":"257888","bondReward":"237772","stakeReward":"20115"},"bondMetrics":{"averageActiveBond":"3085090227102","averageStandbyBond":"2893032932586.222","maximumActiveBond":"5412660469344","maximumStandbyBond":"6000868993322","medianActiveBond":"3925694112419","medianStandbyBond":"100000000000","minimumActiveBond":"1007196760386","minimumStandbyBond":"100000000000","totalActiveBond":"24680721816816","totalStandbyBond":"26037296393276"},"bondingAPY":"0.06252683225574751","liquidityAPY":"0.0045319632375318","nextChurnHeight":"3165604","poolActivationCountdown":170,"poolShareFactor":"0.07800247677137709","standbyBonds":["6000868993322","2320192318072","2966156802987","3200447789835","100000000000","3827347974206","1000100000000","3339283699744","3282898815110"],"standbyNodeCount":9,"totalReserve":"9765819282152","totalStaked":"21109009373292"}