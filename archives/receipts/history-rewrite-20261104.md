<!-- redact: public copy; source sha256 3daf52736d76f508122bcf8db61ca2334b4d946b2306a5ca8d43d28a08d6f871; rules 8; mode record; words 0; sessions 0 whole, 0 truncated; host paths 0; decisions 1 -->
# The history rewrite and route B: the public gate's repository rebuilt under the same name (2026-11-04)

Written 2026-11-04 22:27:44 EST by the Session Continuity Manager (Claude Shannon), registry key session-doctor, under RoR-15 (the public gate, route B under the name nooksee/sessions; each step after the Independent Reviewer's PASS on its exact hashes; the visibility switch last) and the plan "The public gate, part 3", revisions 2 to 12 in `storage/handoff/shannon.md`, passed by the Independent Reviewer (Claudio Freeman) in his sections 166 to 205. One choice was the operator's alone and was asked once, by the Independent Reviewer in his section 204: the 145 author and committer slots that carried his full name with a personal email address are rewritten to his GitHub noreply address (his answer, section 205). This record explains what the rewrite did, why, and where to look; it holds no operator words. Event-time next steps are labelled below and point to the current handoff.

## Why

PoT 1.2.10 and 1.4.15: the operator's words are published only as digests, and anything committed to a repository is published. The pre-rewrite history held his words in clear in old records and in two commit messages, 46 real session identifiers in old code and old records, and his personal email addresses in the commit identities. The tip had been cleaned (pull requests #21 to #23 and #38 of the old repository); the history had not. A rewrite of every reachable blob and message, with the tip tree kept identical, gives a public history that leaks nothing and still bisects.

## What was done, in order (times EST, 2026-11-04)

1. **Step 5, the list.** Measured over the history as it stood at 22:11 (commit e008d875 at the head of main): 227 blobs absent from the tip (161 prose, 66 code); 46 identifier shapes outside the synthetic namespace, in 17 blobs; the redact tool's history-mode check over every absent blob: 225 classified, 2 refused as already public copies and left as they are. The rule by class: a blob present at the tip is never changed; a Markdown blob is rendered by the tool in history mode when its check would change anything, then swept for identifiers; a code blob (Python, shell, YAML, templates, executables without an extension) is swept, every whole and truncated identifier replaced by a hash-derived synthetic form in the namespace the tip already uses, then every span the tool attributes as the operator's words is digested by position, a zero-length span never, and each only when the blob still compiles or parses afterwards; a data blob (the old `.gitignore` files) is swept only. The reader pass covered every unclassified quote in old code whose exact text the tip does not already publish, and every comment and single-quoted literal beyond the tool's reach: decisions 1 words (one literal from a real body in an old test, digested by exact text) and 5 keep (fragments of f-strings the tool's quote pairing cut). Two commit messages quoted the operator; one survives in the carried history and carries its digest. The list: sha256 d37273157ce9c8df610e2580de834a1b0e92b3bb2e97f3e9ed13ff3870480128, mode 0600, in custody, never in Git, since it holds the words it digests. The tool: git-filter-repo 2.47.0, wheel sha256 2cd04929b9024e83e65db571cbe36aec65ead0cb5f9ec5abe42158654af5ad83, in a virtual environment under `var/tmp/`.
2. **Step 6, custody.** Two batches on the three custody roots (tier 1; the failing second tier, verified by direct reads; the interim boot-drive tier), each with SHA256SUMS checked on every root: `sessions-history-20261104` at 20:57, a bundle of every ref and every worktree head before any ref was settled (bundle sha256 d8a40d581056d0ac54cbbc7eecc806136117b146be3fd3a8b6b670ab3506c215); `sessions-prerewrite-20261104` at 22:11, the bundle of the settled refs (bundle sha256 67f03332e22876a0b7ef447aab62c13bda3febe60dbf3d9d9bb6389cc0752806, 9 heads), beside the export of every pull request of the old repository (38: titles, bodies, 46 comments, 6 reviews, 12 review comments), the list, the decisions and the scripts.
3. **The refs settled.** `agent/port-scripts-2026-11-01` (closed as PR #2) deleted by its owner, the Session Continuity Manager, at 20:57; `agent/filing-alignment-2026-11-03`, `agent/sessions-w2a-20261103` and `agent/root-filing-guidance-2026-11-04` (merged as PR #25, #26 and #36) and the finished worktree of the last deleted by the Session Continuity Manager at 22:09 under the operator's direction that nothing be relayed through him, with a comment on each pull request for their owner's record; `agent/redact-20261101` (closed as PR #9) deleted by its owner, the Assistant Session Continuity Manager, at 22:10. `agent/block-7-mind-b1-20261102` (PR #24, open) carried through the rewrite. Every deleted tip is in the first batch.
4. **The rewrite.** A fresh mirror clone under `var/tmp/`, the tag `bootstrap-with-ci-20261031` deleted there (it survives in both bundles), git-filter-repo with blob and message callbacks, replace refs neither added nor kept, empty commits never pruned, and the mailmap of the operator's choice. Result: 89 commits mapped, 0 pruned; main at commit 2752fd3a4ef3013e946c887c1a927865d332b7d9 with tree 30e90264d15d9094b20beeff107bea278a965d73, identical to the tree of commit e008d875; the carried branch at commit 00a0270f87cc3fcbc18c486c89d56d8c8e9e5136; 200 tip blobs untouched, 123 prose blobs rendered, 65 code, 16 data and 19 other blobs swept; 65 identifier replacements; 88 words spans digested; 17 spans kept by the reader's decision; 1 message changed; identities after: the operator's noreply address on 145 slots, GitHub's on 31, the Copilot resident's noreply on 2, personal addresses 0. Checks: 59 Python and shell blobs compile or parse before and after, 0 new failures. The Independent Reviewer's pre-push audit (section 205): 0 identifiers whole or by head in blobs and messages; 0 attributed words outside tip text; every commit's tree equal to the audited unmapped rewrite's, in order, with identical dates; 0 old commits reachable.
5. **Route B.** 22:24:14 the old repository renamed `nooksee/sessions-prerewrite-20261104`, private, kept until the post-push audit. 22:24:15 `nooksee/sessions` created private, issues and wiki off as before. 22:24:21 main and the carried branch pushed once from the audited clone. 22:24:24 main protected as the old repository was: strict `sessions-gates`, admins enforced, pull requests required with 0 approvals, no force push, no deletion. 22:24:25 secret scanning and push protection asked and refused by GitHub (HTTP 422, not available on this private repository): their named moment is the switch to public. 22:24:49 the live room moved in place: the old local branch of PR #24 renamed under `old/` with its upstream removed and its worktree following it, main reset to the new head with no tracked file written, the carried branch tracking the new repository, the tag deleted, stray HEAD files removed, reflogs expired, old objects kept until the post-push audit and the Copilot resident's settlement of his worktrees.

## Counts

Protected acts under this receipt: 1 (the push of two heads, once). Irreversible acts at this writing: 0 (the rename is reversible; the old repository's deletion and the visibility switch are pending). Workers: 0. Deviations: 2 (a deadline written in a message before the clock was read, corrected at once, counted in the handoff of 22:10; and this receipt's own first render, which failed closed on one unclassified span while a pipe masked the exit code, so that the pull request carrying it stood 90 seconds without the receipt before the rendered copy was pushed as the branch's second commit).

## Pending at this writing (event-time next steps; the current handoff is `storage/handoff/shannon.md`)

The Independent Reviewer's post-push audit on the exact heads; the old repository's deletion after it; the Copilot resident's settlement of his three worktrees and his re-opening of PR #24 on this repository; the Independent Reviewer's final audit that 0 old commits are reachable from any ref of this repository; the switch to public, with secret scanning and push protection switched on at that moment; the attributed corrections for pull-request citations in the records that cite them. Each is recorded beneath this section as an attributed addition when it happens.

## Amendments

- **2026-11-04 22:34:18 EST, by the writer:** the Independent Reviewer's section 207 found two faults in this receipt's first rendering: the commit map's new side came from the unmapped rewrite (the clone before the mailmap), none of whose ids exist in the repository, and the deviation count read 1 where the render fault above made it 2. The map below is rebuilt from the pushed rewrite's own commit map and the count is corrected; nothing else in the record changed.

## Maps

Pull-request numbers in this repository's records refer to the old repository. The export in the custody batch holds each one's text; the second table maps every number to its files.

## Commit map, old to new (filter-repo commit-map of the pushed rewrite, the 6vpAyq clone; 89 rows)

| old | new |
| --- | --- |
| 03ffd4947a52b4f85146776c62503c4910d3664b | da06f23cb35b0676848cdacb0562b189657d9c43 |
| 04dc0485bcad7d68f81e29cbdbed7640374dacde | 4ba59f56925968e86a7b2951cf00ec3ad1f05fda |
| 0658842739088dc16048111df70f4c389220a4fa | 1f9053fce116b354e8105766a3c34b7e1b729f23 |
| 065c6ae52f2f76b99335bd8b6f32be1ab2dc8c41 | fc9ee01cdec7b72954250666066f03593b425f9a |
| 07cba3b144a19c8f263233f98584e5c127c584bc | f4b192dea03ef895f182c05198dc941fdef0b0bf |
| 089d4122c09b80c028686fb7fb9a3f7dfc2ba6d4 | 00a0270f87cc3fcbc18c486c89d56d8c8e9e5136 |
| 09bbe63ec8f5e7d3dd26287d2fef10f0dedc6fab | f89125b6df335d5c4542d580c8409287ac96fc57 |
| 0a9e5dc928f16c0afaf1caca4f5a98ecbbe4af16 | b31bff8fa995392b1e8fd7864d78c30014e5f7bf |
| 0b3c193478467d4822c2506f5b4fb447e211856f | 6794c1ee0a3d8136e3c199436c2d765f3d42a02c |
| 11d65f99edeccfe5d27b79c1335ebdece9b5670f | 9b42e18f58bbb5fd96bd4d947ddffa0dba3111fa |
| 139f4ec89e6a56e9c6aa57dcdefaa9abde482e9a | c0245ec24828bf4c1d210a731e6903dfda713051 |
| 17abdcf833786f3fdde5ea3cea28992ba4a1644c | fbc5e849f2f92d19dcc51fcbb4cdc6f493098ff8 |
| 18dad2e8f1cc4360ca9f8dc1e87b69a3d1b09413 | bd0b58f59bea6964ce637814dcb1446e531b84f5 |
| 191df5ab4eedda7a5ad657a96ee878a1446a8e98 | d519dc7c25d82bac1a6053959acfd0c367a625ed |
| 1a1b1f51e005f4012d3ff428260a2efd93f46d09 | 6ae03d14ffc612cdb33e54db1705c4aa55d41528 |
| 1b1bbc8af02bacfef50278d20bee8aad0fa45da4 | 85629b26adc3fdd02d31685ac6f4f3c896538759 |
| 1c4675545e8379f7b2986380f2443e081dca70ae | 6cedd60506a8982ec0159268c09bb1f552335056 |
| 2158f08c0d220a172c563a5d963fa9d273721a9a | 1584b564d86e10f862786dc56046d04221a88b9e |
| 23aa0010c47a33e155204229781d3ba3e3d2b071 | 19e6afafa621200f3a1669a0d08aca91603ed156 |
| 32f26f3326ec2f71e1d9431069f3e212c601876d | 4f887de3977dfd799de389c253f85ac774b33a3d |
| 3ca8640a234d098d837cbf20aa6e3a80b2b88754 | e48c204b9459776cf819b2f633c2f297167135bc |
| 408f9ea98bc5eedceb9ce32ef6f697c95ee9f485 | 75676ede9c554a9517a72d80025b65bf05c0e8db |
| 438280b5174a6447b503f0a30ca786ccb2cafe3e | e996828b983dcf88f9e8346b97ea83b858a6320f |
| 4581d24e2a73b4fa22eaa689eb160189e5f37815 | 10848cb319e68b1e80f2f3eab1a1c32f3888674b |
| 49fa0c66f5b245bdfaeed0c136a8c45c8e194f23 | a3b3ebece4f82a5f66c03385bc9ae276dd05212a |
| 4ae9207fabc3d32fd66574a3e8cd611188ce8fd1 | e6ba829f56343f5b65761ddc44b7c2b4343187bd |
| 4c02ca9c8b3c2780d961e6d6f24290f2e5840e30 | e74c80a7233103635dece04ef2073ca684731dca |
| 4d89e537e4149bd7812dd4e9f0365d377c70f5cc | 710b4023c4933dd147f80d8bb7905c66f6c579b5 |
| 4edcd18ade81682caafc46dbf19cb5a474d849b7 | bbb67bd410647e1b9005946bf80e69ef19239cdd |
| 4f67ec0d3ff353e87375ebeb2d37173db3b38005 | 6c3ef53c045ff3cb366921a9e8153bd9f8a32a9e |
| 54c2d1fc75873b51263a10dc6958b3a3e98f0259 | 1f518bb3a69f3f9d64d3cbe9b79f4831b8055845 |
| 571db3e2ed1c0bf60298c6fafd3f97b968d9e131 | ec9da459f2336db7904e9a1107278aa96e24ea2c |
| 5736f8c15b9a7727b825987513e1753a1785b53e | ffb28e880932572917e52784d3095b79c3506475 |
| 57b8021efa11ebbdb0670f1681677c5758c318ff | e8dcaa009d6eae454174d11f7ca0c2b4368dda5c |
| 5828a2c2878d240ff6af3337002102b8423d5177 | f4a7a2a17ad335940b62fa11daf283f4f32a7c59 |
| 589c72a23af89741261fb024108402030e9758d4 | b13f10b5c5223edeaee7ef95073129ffbd536b3d |
| 5c73ba312ffbbe6fc8a56d31ef4d8316e5600536 | d959c1de9070dfc2cc9ccfac200cbd0227b1c7b6 |
| 5cbcd266d73bbf4dd58b39895a95656d1519c23d | 778168e4ab7edac243997c26bcb8e4031955fb19 |
| 648e834262f9de875aec0240aad1415da2fc6ce4 | 30e00a21778810698e53499e62e517428e050207 |
| 685ab5162294218e6385a346b9278c77700ca72b | a171aa43432736dfca1883190218edf7ee7fe0e4 |
| 6d208999f59e2cb09399ab47c24a4e2978bb8ad7 | 28535de5b7947a303f697b17bd19e78f25c85d8b |
| 6d3130d03cb8573e682f9f4dba23a13b37b140f5 | 5952061c2e0afe8a6e41d3ff588d596d22845670 |
| 6db8781bdb4f80191ebe8656b7b58a690ba6215e | e07956d509ec320eeec15def19f668c1b7007b61 |
| 6fe6a1a96118101e065c9e4362f772b42284dff6 | 83edae818a57d2b7a6ce05ba936ed76d6d2e4b7d |
| 714c588aa137c39a26bf4c431e9eb386a29e498f | 7102739b307167403cab374c58e2bfc8203c00d6 |
| 71a8f1a5d40aa70b50fefc3fcb649e42ef7faf33 | 341c5d1cf36e858423627ab101c107ebbed82055 |
| 77384318812befe02657ee701e0a23f506684e86 | 9938e9c19334cbf84f2a24d25e7a7870877262a2 |
| 8c95e8f34c5ed3bc1ad2081237b2b93ada39cf2e | b166d4c3ee61579250fc3ca04b9989ef383575ac |
| 8f4f17127fa37ba1b702ff21bba31cdfc86077f3 | 3d73e74ffcbc9ba9086870e46be0a58f78ef29c9 |
| 93bcac21eb413900870497a3d97cfd79d61b9353 | 6112335cb5e12e549ed2fe24deaefa31636e9eb8 |
| 95656d318581783e1e6a9496e3f8d421dd80051f | 1ffbfe0d59c087fb3120c40f1a374a1520649dbc |
| 98e5105389a832b7d073fe35c6c1dfbc39e4780f | 40e334f6bfd970c8881afefce38a91f4bc4be2e9 |
| 9eaa7f8eb1ee7d80828a3de8fcc58ef6ebeda8fb | abf2e99540ed39917dc42c63d9438bc30b30e1e2 |
| a1ec86471f3fcfe3a053a9bedd7f2b8ac327368e | 21a0a71a901edd0057125f02021ebc57aad0e9af |
| aa279557e25599d0a1863bfa77f8b691cad6ecbb | 332fc767d038cfef9c112f9db1965379b1098853 |
| af78178667b6146bf0f809903480722bef51ec88 | d047a86acf3ae4d0bd7737d2a40f23e70be374d1 |
| b09aff05384d5e2af1ee3ca80fd9ef9fc20ab2a5 | efa0e4094d6c05faff5af21726c80f60c792cce5 |
| b69fb3797491f8dc1f6b74d85e321822ecd04ff7 | 8dee806c66c7d17c1271a99dfb7054f66cde41df |
| b6d75d44f6d56b13d7da6dbdb655aac46a07af89 | 590a232d731bb9725aa3e74e5a9af30037eb7286 |
| ba48c73e8c3f4ee7d48fdffadb6b95f181450153 | cc2933f199f18f3355bab96fba3b7748395c1291 |
| badc64e0d310ce1d203dc9763ce3303670afe759 | 3f219a8698fa92538f04a8a9e7a0a48c15882e41 |
| bb9d1c24177384227d99950babaadb8db3123d49 | 65c4b6a2bf8a437c0ffa4791530647ddacef5f82 |
| bf60847a199babd4917debe5a246b982bcdc7edd | d266a569482c78c5ae0c3d9d77341317d52158dd |
| bfbc83b7c1eb173d752edb21a01ec123e5ed13c2 | 1b2d460715bbdd66a24cf7c4c19f03784f02f064 |
| c019004f6a7b116625d1bfc2ea6d1f21251c5546 | a1f2e30179732f24cf2ee88d1d5858051b6f70a7 |
| c3314cf38f889d2242c79bc97931d40b733bd678 | 68071e2d742cf658b047289b2220e8f1a3fd4c0b |
| c7a5493fe100ba2e43fedf64b3ee28cf9d8beee1 | 5b2b2d0bb73050d4f3601cfc0967a90a40c1460f |
| cc199743b18c39a5a91d3299c2152e3686230c99 | 25adb47bc68883ef9d421ebaa37c7e0e12c98b42 |
| cd3a23995fedba3e754df1e0ef9adac276ba0e83 | 1fc0bbf95f98f00978b725fbb65137312341c6d4 |
| ce16a110bcedb7d1bd673e0f80ed105a957744ca | 0ce315602e34ab8cfac70d8733a728a2a05a029f |
| cf399aca6ed142e42222847c9c0f95f6094db740 | 087d0f54e05286e5a8d596dbfd86c708a187cb3d |
| cf5f6645c1769eefe53ffd1376b0a6817fb7e5bf | 6b3a74b1b142a1be69721221e96d529ac0645466 |
| d59ffe7b41815a2d6dca0e8afa0db4a47b556032 | 19177132e1ef6f3ee8c9b349cd9d89f4615616eb |
| d75e41649322c313acaf7efb81a1810c6d9e0b00 | e3cb3bab1ff5ca71fdfd758c643ea1351571f860 |
| dc8ca3e371beb6574ce0309fa1fa501fa2e0518b | a0d3e9eb40560cb1de6c0d2c00e2a7b9365e9c9d |
| dca356016f8583f8c3e5861200d277d928b320d3 | 73d9570b8be0c0ccf46573c3c480c5bf92b9f042 |
| dedd085b3bcef4ce2c79cd7da62f1520915f7514 | 668bb161fddcdb64576d0f06cef5fc242a31d9db |
| df55e14cd5176ccc32838817b006c650a590a95b | 92e3cc95d0471d2a2e9f9fe5cfa1a5cf6085c08f |
| e008d87596687beccb3e20985de58fbd7f0d8705 | 2752fd3a4ef3013e946c887c1a927865d332b7d9 |
| e0222c5933816ad9ef93c62aa8093365736e571e | caf0cd907cc6b6fb321b9b58d0899bca04271b55 |
| e3b7fe3321ceb02783b165e5a4448c7074e69d76 | ddf23d2efe40f6557e91d7eca5a45a0b5ea92bb8 |
| e7b4f9185c0f545b6aa0a40100c9f38e314b91d1 | abe2bc932d8d8f2e1450d77a7e71bd56ee692210 |
| e881598b58cc36d9e977e5341f7ffe899a90637a | 5bd0600e5fefb04183bc1c21a82bedaf391034e7 |
| eaa7477115c659f50ec45b6e72de04290f276807 | 5da50875e53dfefc144b9399ced2e12ff63674bc |
| ec8156cd079f7b8322b381d45fe439ff8cd1bb9a | c43888b5b7f5018141d10cd68cd086f5bcb82e88 |
| f1972b7a0b4673867878055aa084552e54ef36d8 | 6e751bd917e8490490b3d24a60ee083e6313f974 |
| fb63ae138b8f0a9dcd00c8914b9c261ab9b269b8 | dc56f0d57a8a9d46b6c25e735cb2573f549a3d59 |
| fb9b899c2af3e069d4637f812fbb8cc3f43c1981 | 6ef1c5f3e49b1494c0e09794d1c376c5ebb41886 |
| fddfdb0c6bae6d0ac2463f15f6e2c84f7025029d | 2f9e04620033300a4f91c66cec9b139c02fc52cf |

## Pull-request map: every pre-rewrite number to its entry in the custody export (batch sessions-prerewrite-20261104)

| PR | files in the export, each with its sha256 |
| --- | --- |
| #1 | `pr-1-comments.json` sha256 50e80533779882a1a16887faecf8be4c60301b38acd967a9ff5217b0db767209; `pr-1-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-1-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-1.json` sha256 bbb146dc21cee446652e1a7caf4e220303f7d9124fb11bfc13fc55dfcb7ea0fd |
| #2 | `pr-2-comments.json` sha256 823355bad3979f38358ec1c1743df10688f20702d68ae44bd338aad3f11370eb; `pr-2-review-comments.json` sha256 2229e7d0ec7d6052afa774aac7225d2d91b87902a98b0b8ed4f597f9afdcd9b9; `pr-2-reviews.json` sha256 71e6f79aa4dd29f0881bc1baf5303b76b43f1292b2f6d75d3bad7d2913a0aef8; `pr-2.json` sha256 c50d687c74004cb3a979f6cbb8186c5e5152c5b4ee688fb4b846efc3868c9648 |
| #3 | `pr-3-comments.json` sha256 b5a3d251f8a02d6caed3a7a51b236b1b81e502797b7738edc447065c6566e7b6; `pr-3-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-3-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-3.json` sha256 e529fa6086fcaa69f8a76144b97e99abc33328970f033b471e8c69d544764a94 |
| #4 | `pr-4-comments.json` sha256 7f13e382100737c47d028565df89a4db6bb9fa075e2d859ce9dd51df1c41903a; `pr-4-review-comments.json` sha256 6e82effdf5a3695f7a634bf3f82ebb183521082b8e83d842dd997e86b0506c25; `pr-4-reviews.json` sha256 8a4f8cb07c637553bacb2d2dc2a410ad49f9a6363d37646a16a71e42667aca08; `pr-4.json` sha256 d46136ef022fc938fcc0c1a792e6dec5e3c1fe846cf624f518055fd960a3ef8c |
| #5 | `pr-5-comments.json` sha256 7364698a05d096effee360bf13103061c7bc311a5daaf6e8c7d31098f46256cc; `pr-5-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-5-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-5.json` sha256 5c8257383cb8f0cd82a2f300b15286c82a71d869124e9625d48598bef13a0b50 |
| #6 | `pr-6-comments.json` sha256 ff10ddc779413c37b852aa6483e5c006c8189fd9af8fce8990a99520b346fc6e; `pr-6-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-6-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-6.json` sha256 e2ee8bbd3ded7f1c997cd197f1ecb9aaf4272a45bfb21122c290079483965db3 |
| #7 | `pr-7-comments.json` sha256 4bf939f9ef8d62279bad710b3f12f8b57184ba17f9d0ede3b969b34736cf18e9; `pr-7-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-7-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-7.json` sha256 b35da89ddb70673cd51b300602178eec499637cc64abf629b07fffe17f7ada7b |
| #8 | `pr-8-comments.json` sha256 c77bccb6549d425a2ef67b628fd333e81a8c63a988381ed6ab6282419bde605b; `pr-8-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-8-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-8.json` sha256 02902cfb2e298acda9e5d12f1e5a1375e1a9c267b72122a082f89c006c985bb8 |
| #9 | `pr-9-comments.json` sha256 3d899b2ca4b73c9689d3aea345be5fa0f878ef08b4c6cc0c99a83d6fc6a3ba92; `pr-9-review-comments.json` sha256 1bdde7a5d70b0f0562a43e141dbe51dd67fc3118d921bf8117f3dd03e8f6aaac; `pr-9-reviews.json` sha256 0c1d9719436457154747ed97025d4f4cafb48a2f6bf3038b6e0d2f8e513e3f9a; `pr-9.json` sha256 dca3ad8a9be62c9faa660d19ead68c7dd0a6f8f3639075f718756108acf4f04c |
| #10 | `pr-10-comments.json` sha256 4b3971018aca69a38ceae9bdef013a3a2be44df500ff2b8e0b449092492f63fe; `pr-10-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-10-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-10.json` sha256 81001fe5bb5de0dc0a1119636db8e103bb77cc4b0c4dcad7540b503d3bdde9b8 |
| #11 | `pr-11-comments.json` sha256 04d156cba3acca584e3d770b1ea8646dbea4f2f6311a77ab3c74c0cc9f329eba; `pr-11-review-comments.json` sha256 60bc2369ed175e92859556fc4fa9aa45a0a9c39013be542665f301d31946f441; `pr-11-reviews.json` sha256 878bb3bad50bb49ba06d8ea90c08a050e65d047c080ac8514e551585764c93ae; `pr-11.json` sha256 280177c147779fcad58210f87579f6f4e18c3f46f5ae0897e19159cc85d3c59a |
| #12 | `pr-12-comments.json` sha256 f6f3a1f49a5858639f5ff638c6a82d87c6b2f214a5116b29d5ec74690ef53c13; `pr-12-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-12-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-12.json` sha256 6690e440dca856b498c4cd11d67f34f5cd20f38f8f50afa316eec6dfe4772309 |
| #13 | `pr-13-comments.json` sha256 158c467b437d67cdbf1be0eef54c60026ab7faedcfcd5ac7fc0c1dc96ea36ce7; `pr-13-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-13-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-13.json` sha256 6eafb21a2fa3c0f24e30f3d229b01ec5f235e6191f71eb28b13ee10c91f48cab |
| #14 | `pr-14-comments.json` sha256 593a54ae03b1637c302b20908fb9b49053a18aabaf7665a945ca53fae00ee6ed; `pr-14-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-14-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-14.json` sha256 4458d2ccdc43e755814f6bf161d80e0778950467c276223d85526a9bd6e9f6db |
| #15 | `pr-15-comments.json` sha256 ba3d63eceea4f1fd3d1674abcb195541318fba5a8ed52952def4e69d169f5350; `pr-15-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-15-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-15.json` sha256 01481c33a92c6323be14ff6a08c390a138f341fc6a31bfa3617b09d16878a75a |
| #16 | `pr-16-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-16-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-16-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-16.json` sha256 b93a38bf5b829b72e5abb316040e0b344be1629069ea79ce310ddcc99e4b9d3a |
| #17 | `pr-17-comments.json` sha256 0697dc8af72e7cfb066ce89dc497863128023e2c945997755d9bfa99e1ce5812; `pr-17-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-17-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-17.json` sha256 69e60dcde616e309f85bd8a10dedb2379071b3100a8c0f923e94af0a2c34d3dc |
| #18 | `pr-18-comments.json` sha256 502f59027d644be603579175947048ecf6863a4a919986a5a68f829e929c479a; `pr-18-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-18-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-18.json` sha256 52e120823e88d3cc981daee26255699eae547cac760daaaa1f12560632119508 |
| #19 | `pr-19-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-19-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-19-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-19.json` sha256 d2f3afd90b62c7e2079a6a6633dc25636d1a530f3ea1a0ef4dd98c7dae346885 |
| #20 | `pr-20-comments.json` sha256 7613b5ee48c43537f1f6e98b38623a3d193d4d1058f9371edba9b685d7617a5b; `pr-20-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-20-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-20.json` sha256 16b81200343ac9029f8e8ea93a391ab895eef55e2a081a8275e1735c424be6e1 |
| #21 | `pr-21-comments.json` sha256 4bcb26ecb63d023f36ec6aa2526fbad9407775fb846f9e5a874c78acde292cc2; `pr-21-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-21-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-21.json` sha256 910e0312037502ce1b19b196dc144fa6f19383ea340bc1a8f10e75f84e1203f7 |
| #22 | `pr-22-comments.json` sha256 a305a36e6aee5eaad8b00dbbdbd6882ebb338c6aadf9ed08184e1f52cc275a9f; `pr-22-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-22-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-22.json` sha256 1ae9e965f06f2eb3bc4a4a47853a845726b1ae0e1dd0fd89a2bb2b40e6f84448 |
| #23 | `pr-23-comments.json` sha256 69f1bea9486f2f911b415ef70de4adbfe104349b47c0950372686517eba84693; `pr-23-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-23-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-23.json` sha256 06ad51ab34f3619605259a83af6019a56c0824eb4af72f5de1cae35bd2d7c8be |
| #24 | `pr-24-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-24-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-24-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-24.json` sha256 e75859d5ed26037e42ef07e47d06820b87794ca7b0a1ed11cfcfcecd2faaf9c7 |
| #25 | `pr-25-comments.json` sha256 faae313a30a89dbf07f554f53909adf5196d1475f4fde56262a5dee15f76e5e1; `pr-25-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-25-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-25.json` sha256 c1f35a591c778548917310def313210ac0b19d7489f4a958f77c1ae6faa1308b |
| #26 | `pr-26-comments.json` sha256 43a6ed20291b10986f76fcec850b12ef99f9192814cd26cdd9f220feeec63833; `pr-26-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-26-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-26.json` sha256 41d6475841b8694bc87d549aab15aa15a94787ddf4ebb9d5026eaf04bf23e9df |
| #27 | `pr-27-comments.json` sha256 229e137cf2591400cc1ecccf24325c4e2b97437215a8b2bf600e503933f25910; `pr-27-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-27-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-27.json` sha256 f9882f1c788e19a3d45ff50fd234af65efb4c9b096d98267a194dec8053c067e |
| #28 | `pr-28-comments.json` sha256 7aa8438c38f324f71aabea64ee5cbc33fdc2909bb4aab8223bdcc6756b79d2cf; `pr-28-review-comments.json` sha256 c7ed063144c01fcd01c3ce0bc177c43665314a07c400db99ff0ffc91f9b2941f; `pr-28-reviews.json` sha256 378ca73776ccc2a877972ca2c594695b66a974d058df8e64c4d1a83148309030; `pr-28.json` sha256 88eeddfc03194b25a4a3c733d2833586994beb000d632f1f67b424623fce027d |
| #29 | `pr-29-comments.json` sha256 e05a75c9602974ab15fa6cc7abc16fbb844beb20423b70b3ba118b5bca941ccd; `pr-29-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-29-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-29.json` sha256 74f034f4e012c9d4e8403cd08527b281a6e0ac72399d9752a45f9cdde8af5711 |
| #30 | `pr-30-comments.json` sha256 e63cf1655a48a9f69bb89e4f5ba88616c2e45f67e886d5ea2ba27318753e1e3e; `pr-30-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-30-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-30.json` sha256 32e1023992761d966f82cc0a243224cfb38e5a2b824f95e7f5ae8a426a2833cc |
| #31 | `pr-31-comments.json` sha256 775883d6a6b29e6f5f753fafc58c7eff0e8a97c8abab1161634be4aafbb70c1e; `pr-31-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-31-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-31.json` sha256 cdc8524b64833be371443cb15c47f0c6b41311d33115e9fd59dd3c5e6a9b5cd9 |
| #32 | `pr-32-comments.json` sha256 cad7f37c8f5ba8d4e4240a0e3db1922012fa19125c5fc3f5037ab89ef7509604; `pr-32-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-32-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-32.json` sha256 fc8a1e6467c218f5f519c62a746f21fdf603e783578941e33910a90a1f812f92 |
| #33 | `pr-33-comments.json` sha256 c962d2e531247341d89149c9857bc8af52c0547805a30e132c3799adedf65db6; `pr-33-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-33-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-33.json` sha256 818b27570d6077adbdf9883a0fc772e925440a28e04b71d2969e66d8149d9fee |
| #34 | `pr-34-comments.json` sha256 dd99e0a3371707433afe5742ff82b66873d7030c1fd82f0380a06745fb6865aa; `pr-34-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-34-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-34.json` sha256 fbdbbe57e1de0c241328e012ed1e1996c58134df869183a79996a44b5dcecb07 |
| #35 | `pr-35-comments.json` sha256 320a66f499d6272cf9e904462f8610ae524e67d0c109b81c90a14753c18204f1; `pr-35-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-35-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-35.json` sha256 67f5170c8ccfc7c4a28de42847bcae7785cb06e1933c5c34854d2b97637c1c92 |
| #36 | `pr-36-comments.json` sha256 a4a98277e002d8493e384c7bd30eb7f79f984236d91952157b9b1a6d57466bf0; `pr-36-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-36-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-36.json` sha256 97b4926683ef5907ea8e3d23d9653dd0c33dba3fdbb586b5e9f04bb76dda8acb |
| #37 | `pr-37-comments.json` sha256 83fa47ac1c0d5bda4fd5b98189eb15c5ec8e9230db6b192d10b217c43a431a87; `pr-37-review-comments.json` sha256 f666c0e4169a7e57f9dbe895fb768e13c67e25d3ec3c41360207ef034b6fdaef; `pr-37-reviews.json` sha256 2da4a52534d468dd85b19449d554a194ad8456bd9934da112a0c950f471557ab; `pr-37.json` sha256 959d759172158784098bd1836a69e32ad3648f4211fcd91f7b5eb7552c4b5a60 |
| #38 | `pr-38-comments.json` sha256 8d55c55db9f37360cc1670d446cae5e99ecdda5c2e19fbee3b82fdd7f0365430; `pr-38-review-comments.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-38-reviews.json` sha256 4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945; `pr-38.json` sha256 8ed734cfa8e93dba9a6b8c362de90d857bba62036df5c511c6bdce2e8a076938 |
