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
