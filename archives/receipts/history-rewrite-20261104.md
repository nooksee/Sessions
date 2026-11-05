<!-- redact: public copy; source sha256 ad297e01bba6393f73fcaa167ef6478d092f4f7f3a854ec162cd8d94741d0fab; rules 8; mode record; words 0; sessions 0 whole, 0 truncated; host paths 0; decisions 1 -->
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

Protected acts under this receipt: 1 (the push of two heads, once). Irreversible acts at this writing: 0 (the rename is reversible; the old repository's deletion and the visibility switch are pending). Workers: 0. Deviations: 1 (a deadline written in a message before the clock was read, corrected at once; counted in the handoff of 22:10).

## Pending at this writing (event-time next steps; the current handoff is `storage/handoff/shannon.md`)

The Independent Reviewer's post-push audit on the exact heads; the old repository's deletion after it; the Copilot resident's settlement of his three worktrees and his re-opening of PR #24 on this repository; the Independent Reviewer's final audit that 0 old commits are reachable from any ref of this repository; the switch to public, with secret scanning and push protection switched on at that moment; the attributed corrections for pull-request citations in the records that cite them. Each is recorded beneath this section as an attributed addition when it happens.

## Maps

Pull-request numbers in this repository's records refer to the old repository. The export in the custody batch holds each one's text; the second table maps every number to its files.

## Commit map, old to new (filter-repo commit-map of the rewrite; 89 rows)

| old | new |
| --- | --- |
| 03ffd4947a52b4f85146776c62503c4910d3664b | 53e2c904b1cd2754ef525e86252038638eb4ddc8 |
| 04dc0485bcad7d68f81e29cbdbed7640374dacde | 3a4f631a2c82515a62e2c1a5a5cc7af78b8303c8 |
| 0658842739088dc16048111df70f4c389220a4fa | 2a44c8d72aa24d19ed589487b61b1edb813aad5c |
| 065c6ae52f2f76b99335bd8b6f32be1ab2dc8c41 | 2a0640f1de0d6664c023e7bbd5b36e9002627416 |
| 07cba3b144a19c8f263233f98584e5c127c584bc | a2d99491769ec9e1365a359660c397d26426b5a1 |
| 089d4122c09b80c028686fb7fb9a3f7dfc2ba6d4 | 9a064eb176986d1fed315df2adf39492a39954df |
| 09bbe63ec8f5e7d3dd26287d2fef10f0dedc6fab | 7bc7006422936ef9c29f2b0ca44b99f4695bad3c |
| 0a9e5dc928f16c0afaf1caca4f5a98ecbbe4af16 | 29f5c23e5e07a2238f36e9a4310ce5b55acb74d1 |
| 0b3c193478467d4822c2506f5b4fb447e211856f | 932fe083ab24367d363682b265038826671e43f3 |
| 11d65f99edeccfe5d27b79c1335ebdece9b5670f | c70c77e14a74156663cc2b23955c50085783fb0e |
| 139f4ec89e6a56e9c6aa57dcdefaa9abde482e9a | 651a4cd3c345a8003c5c806e3bb9641b27a1f50a |
| 17abdcf833786f3fdde5ea3cea28992ba4a1644c | 3a0fa7491686b51c10f68889577da3fe0dc28bce |
| 18dad2e8f1cc4360ca9f8dc1e87b69a3d1b09413 | 2cf6c6b1d29cc3d93684e1b16e69c49c9f4f50b2 |
| 191df5ab4eedda7a5ad657a96ee878a1446a8e98 | b306930a4717f5b0a1eaf05b6569ba601bbe3f1f |
| 1a1b1f51e005f4012d3ff428260a2efd93f46d09 | ee8d38488cc9750b6da98388daf50ce89f5a2d8c |
| 1b1bbc8af02bacfef50278d20bee8aad0fa45da4 | 10aaf642de773a8234174170494175ea8b3ec38f |
| 1c4675545e8379f7b2986380f2443e081dca70ae | 4766ca26a301afde571bd393560a1c1fc6f59367 |
| 2158f08c0d220a172c563a5d963fa9d273721a9a | 59902be10a7448203deba040d1a33ce5986b6884 |
| 23aa0010c47a33e155204229781d3ba3e3d2b071 | 4357f130a57e3e8031bfee30add49fde144a6283 |
| 32f26f3326ec2f71e1d9431069f3e212c601876d | c098bb93d0de8cc9e9c821dba9cfea971e55641b |
| 3ca8640a234d098d837cbf20aa6e3a80b2b88754 | 06966ec3d34349374726e171f7f66bbef3c3ff4d |
| 408f9ea98bc5eedceb9ce32ef6f697c95ee9f485 | 7de1607ff257620f8aa75cd96fb516bdf19d1569 |
| 438280b5174a6447b503f0a30ca786ccb2cafe3e | baa0fbb488c0f5822471477c3659cbe8d16b3ede |
| 4581d24e2a73b4fa22eaa689eb160189e5f37815 | 564c7a587f31bb979301eb250e671de8d9eba0a3 |
| 49fa0c66f5b245bdfaeed0c136a8c45c8e194f23 | 8da2d64e0166c9f7d94ee6b0d02eb24b08fc05dc |
| 4ae9207fabc3d32fd66574a3e8cd611188ce8fd1 | 4be9cdeaf0883b4630bd416dd855358161abf0bd |
| 4c02ca9c8b3c2780d961e6d6f24290f2e5840e30 | 389e8f1f8a28dd5f8d0ac85b82dc20744b0d9076 |
| 4d89e537e4149bd7812dd4e9f0365d377c70f5cc | f7fafdda06526d2f3de6b0c234a16ac0fc40a01a |
| 4edcd18ade81682caafc46dbf19cb5a474d849b7 | 523ec4892d5cbb305f0005e37518c34709a8e1c5 |
| 4f67ec0d3ff353e87375ebeb2d37173db3b38005 | 4d1380265fc774fd12e3df8d8894b2763799b54c |
| 54c2d1fc75873b51263a10dc6958b3a3e98f0259 | 27d6697b5696d11eab19ce7d744fa1c63687ad49 |
| 571db3e2ed1c0bf60298c6fafd3f97b968d9e131 | c3fe448d47a9aaebe0911054cfb3357df440d2ea |
| 5736f8c15b9a7727b825987513e1753a1785b53e | 4e8f4ac0072c25d00d1e5c7678fe23c8ed132d69 |
| 57b8021efa11ebbdb0670f1681677c5758c318ff | 3ddaa78ec93a89418d5cfccc5ae24cebaece09ac |
| 5828a2c2878d240ff6af3337002102b8423d5177 | 39c0501f161e87402b940303b4f51703a1c34778 |
| 589c72a23af89741261fb024108402030e9758d4 | 96806bfedcc2a02a9c3cd40a797cb01329a06a79 |
| 5c73ba312ffbbe6fc8a56d31ef4d8316e5600536 | 33b9aa7feadef7a8fe05d29f587248a743f95342 |
| 5cbcd266d73bbf4dd58b39895a95656d1519c23d | abad5b5d9dda0570d96c3fad8a96472f143ff038 |
| 648e834262f9de875aec0240aad1415da2fc6ce4 | 16ad7e1ab8df9ce4d7a58dbf0c19c91dcbe2f984 |
| 685ab5162294218e6385a346b9278c77700ca72b | 457a28c72e02ea806d1210dbcbae07d60f6fb204 |
| 6d208999f59e2cb09399ab47c24a4e2978bb8ad7 | 8c2526c08687d0a4e1928099592405e1e391b385 |
| 6d3130d03cb8573e682f9f4dba23a13b37b140f5 | 14dd6ff72edcade71efe046aaa31caa364907d31 |
| 6db8781bdb4f80191ebe8656b7b58a690ba6215e | 97aebc08d3b3ce8f5694d86c8c3f921b67b67752 |
| 6fe6a1a96118101e065c9e4362f772b42284dff6 | 3dd9935c908bcaf5379ef47df3df73a2401f2045 |
| 714c588aa137c39a26bf4c431e9eb386a29e498f | b6f4d7b86453a3f0a3a1ddd0af107e9219802326 |
| 71a8f1a5d40aa70b50fefc3fcb649e42ef7faf33 | f7faaffe933aa27ad136af8b85a17b68fd6de686 |
| 77384318812befe02657ee701e0a23f506684e86 | 420aeabf32a9323f6314ebd9d3ba7d2c5b48a393 |
| 8c95e8f34c5ed3bc1ad2081237b2b93ada39cf2e | 0c2b47df5264cf640a5569a91f467c9affcd6c17 |
| 8f4f17127fa37ba1b702ff21bba31cdfc86077f3 | 603323a0bbfdf71a0838429bf3043b70df17db47 |
| 93bcac21eb413900870497a3d97cfd79d61b9353 | d518a207dc3f0f1913551fc5c63432536c2b5a64 |
| 95656d318581783e1e6a9496e3f8d421dd80051f | bf85d001f9744070adc364066fa6be7de6ddae93 |
| 98e5105389a832b7d073fe35c6c1dfbc39e4780f | 8e7242af176557753957c3bc6cda28baf7e1f274 |
| 9eaa7f8eb1ee7d80828a3de8fcc58ef6ebeda8fb | 149b8cbd2feb60cd7c7c2fe2c8d02397c9bd36f9 |
| a1ec86471f3fcfe3a053a9bedd7f2b8ac327368e | a2d5cd9c3596f234b15ed2c52d016fa50a95ee28 |
| aa279557e25599d0a1863bfa77f8b691cad6ecbb | 9500edd53537986cd0a2af19eb4413de8dd6b95d |
| af78178667b6146bf0f809903480722bef51ec88 | d827fc162714c6bc84168e75bd52420aa3c6f4ab |
| b09aff05384d5e2af1ee3ca80fd9ef9fc20ab2a5 | 536832b1f2614cfdb8c9742e8c4161e42cee0f7d |
| b69fb3797491f8dc1f6b74d85e321822ecd04ff7 | 3b58ac30a4c97b89e0278516092f57a182e926e6 |
| b6d75d44f6d56b13d7da6dbdb655aac46a07af89 | f29aa3547b7d4538e9ffd4022464b27379ac1371 |
| ba48c73e8c3f4ee7d48fdffadb6b95f181450153 | 0a5614b236f63b15d3e08cf70e8cd2827225c256 |
| badc64e0d310ce1d203dc9763ce3303670afe759 | 1681b3322c884d5e7c8754845a809ed514b85f89 |
| bb9d1c24177384227d99950babaadb8db3123d49 | 8464e27daf41f77e96199886e1a7d1a41db00682 |
| bf60847a199babd4917debe5a246b982bcdc7edd | dd3d6780dfffb5c68bfadf9b2c9b5f06b30e1ba3 |
| bfbc83b7c1eb173d752edb21a01ec123e5ed13c2 | 225a39072367bb77a7d899bf88aca6088354017a |
| c019004f6a7b116625d1bfc2ea6d1f21251c5546 | 23ac2aee85fd899bb06667a6e1b7c31642878783 |
| c3314cf38f889d2242c79bc97931d40b733bd678 | 24e39fbc9c758485d488f194bdbd048344944d2f |
| c7a5493fe100ba2e43fedf64b3ee28cf9d8beee1 | 3e482c6d228fd617b38b25f32fc51101d57db800 |
| cc199743b18c39a5a91d3299c2152e3686230c99 | bf270b5643aa45782b82e85f2d075a3cfa80fa3d |
| cd3a23995fedba3e754df1e0ef9adac276ba0e83 | 135cd35b7a83ec3a50fb831a8a2fabd62daf1e7b |
| ce16a110bcedb7d1bd673e0f80ed105a957744ca | d77bb22d88dc486581aaec3e656c8550b6c72636 |
| cf399aca6ed142e42222847c9c0f95f6094db740 | 138ebc75970c80235b17617db35c36d5c39bb486 |
| cf5f6645c1769eefe53ffd1376b0a6817fb7e5bf | 0ce034ca7fa528145b1b4cd21326e5a8b56dca06 |
| d59ffe7b41815a2d6dca0e8afa0db4a47b556032 | 0ef44fb2d08dfb7738acd1b14cf428fd5dac12f3 |
| d75e41649322c313acaf7efb81a1810c6d9e0b00 | 23c5c60a30217e6d0ff062160ac2e4319f18a214 |
| dc8ca3e371beb6574ce0309fa1fa501fa2e0518b | bfc493dfe35eb5e7d108438b6e727d89b6d3503a |
| dca356016f8583f8c3e5861200d277d928b320d3 | 22d34d456dd560cceef6e87eb6ee3e0a04322156 |
| dedd085b3bcef4ce2c79cd7da62f1520915f7514 | f7d007275d2c19e09a6f03b82f8f4ac67c7ad3c6 |
| df55e14cd5176ccc32838817b006c650a590a95b | 67e7a0abf58bc7b750c3ab09d953831bd7b45e97 |
| e008d87596687beccb3e20985de58fbd7f0d8705 | 427593168a97afae094ed503d88b2547afe36338 |
| e0222c5933816ad9ef93c62aa8093365736e571e | aa499a7e041867e0121d647e15a0df096623e99b |
| e3b7fe3321ceb02783b165e5a4448c7074e69d76 | 252c7ae4b5e4197f5de7840169988fcd74391d1d |
| e7b4f9185c0f545b6aa0a40100c9f38e314b91d1 | 435294ca864024f6b40938ac56452287d955c9ad |
| e881598b58cc36d9e977e5341f7ffe899a90637a | 8565ae13ee14ac2a675f3485516e51387d590d2d |
| eaa7477115c659f50ec45b6e72de04290f276807 | 7263df8f7c4c5223d4042e136c28ee5527519ea5 |
| ec8156cd079f7b8322b381d45fe439ff8cd1bb9a | 16d46a46e5a209f2077aca1a1ef15bcde347e95a |
| f1972b7a0b4673867878055aa084552e54ef36d8 | 7c1b60bfbaf8e4b03737ac2144d2af554e0701b8 |
| fb63ae138b8f0a9dcd00c8914b9c261ab9b269b8 | b47471bc31b6d0ae78d4678e104e320ed5cd15c2 |
| fb9b899c2af3e069d4637f812fbb8cc3f43c1981 | ac6b74e7c625d647cd4289695a2e74cc6c57b844 |
| fddfdb0c6bae6d0ac2463f15f6e2c84f7025029d | 8c406a525d44d7069e911b4df00c3f0f77d5c78b |

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
