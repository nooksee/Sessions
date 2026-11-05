<!-- redact: public copy; source sha256 96754c78e9db93e1c35d3c307ce9e3bb4e1e0861cfa391c2d1bad04158f43374; rules 8; mode record; words 1; sessions 0 whole, 0 truncated; host paths 1; decisions 1 -->
# Landing, stage A: the code and the documents (2026-11-01)

Written 2026-11-01 11:57:01 EST by the Session Continuity Manager (Claude Shannon), writer of the landing branch `agent/landing-a-20261101`. Plan: `storage/landing-plan.md` (working copy; its text is quoted in the pull request). Direction: Kevin, 2026-11-01 02:2x EST, "[words sha256=cf0305b3aee64c76a193153db4e3b6f037929985ee590d484ea6b17e12a44881]".

**Source:** the port `[host path 1]` at the hashes of Claudine section 14 and Joe's pinned manifest (2026-11-01 02:03 to 02:13 EST), after Claudio sections 134 to 137.

**Lanes replaced whole from the port:** `ops/bin`, `ops/lib`, `ops/src`, `tools`, `docs`. **Single files from the port:** `logs/.gitkeep`, `ops/etc/.gitkeep`; the five root pointers were copied and then restored (see Deferred). **Untouched:** `CLAUDE.md` (the live door, PR #1), `PoT.md` (`ef2e16c0`, RoR-12), `RoR.md`, `NOW.md`, `Scripts/`, `Evidence/`, `Receipts/`, `Config/`, `Resident-Center/`, `storage/`, every body and mind. **Not landed on purpose:** `ops/etc/*.json` (stage B), `archives/receipts/` and `archives/legacy/` (stage D), `.github/workflows/` (the connection cannot push workflows).

**Counts (corrected 2026-11-01 12:14:17 EST after Claudine section 19):** rows copied from the port 163; in the commit 152; on disk only 5; Control-tracked files restored to their recorded bytes and deferred to stage D 6; live files removed from the replaced lanes 41, each listed below with its pre-removal sha256 and disposition; unlinked outside those lanes 0; services, timers, hooks, settings, registry changed 0.

**Interim rule until stage B:** the landed tools default to a registry at `ops/etc/`, which does not exist in the live room yet; run them with `--registry Evidence/resident-identities.json`.

## Deferred to stage D: Control-tracked files (restored; port version not landed)

Control tracks these; they change only through Control's writer process (PoT 6.1.4). Each is back at the bytes recorded below.

- `DOCTRINE.md` | recorded `69d1fa2bf6b3fb6f0e2224462d615329b60cd1ea96347757f21b5cc980c98c40` | port `6e0455dadb5520e42f1a6bdca5dee305d9a6a41142d64dd281cb30c2072eacf5`
- `INDEX.md` | recorded `6589b752b447e0df1d906885558bd8fcd292d601667ff56a9aada5931aeb72b6` | port `2b2693816cd635d8061e5c4aa017c382b16375516b0f6cea5bfe4f18aaeafe19`
- `START-HERE.md` | recorded `fdf0fd95539793ac66e7ef33f611a7044f07192ebbb9b29d7c5d727bbe8d5669` | port `18dd35e6113db2f926e16c032732a7d319fb7fd64e9d2f0dea18905260732975`
- `AGENTS.md` | recorded `14d34b4dae49167f5a9d5985ccc3b71efc37a7104e52e70778ce7daaf1cf2d0c` | port `14d34b4dae49167f5a9d5985ccc3b71efc37a7104e52e70778ce7daaf1cf2d0c`
- `README.md` | recorded `3922c5323f0252e6139a928bde1aebc3741ed701d544e2816fa7ff40ff2fec39` | port `3922c5323f0252e6139a928bde1aebc3741ed701d544e2816fa7ff40ff2fec39`
- `docs/resource-state-contract.md` | recorded `9a984c6a54ad1b6cdeb8d797b1f54e990b31fac3f5a50ddb0f4b6e41dd338bf8` | port `a486ac5e624c9c95ca5db8bb64c5080c0504f766b4baf65b85a17f01bd53980f`

## On disk only (copied, not in the commit)

- `docs/clinic-aggregate-contract.md` | `a6c1bf09ecba8e2d333101a976ebc5658dbb46372fa2874537edd1821eb96634` | Control-tracked and byte-identical to Control's copy; not tracked here
- `docs/session-clinic-integration-review-response.md` | `f6e252d0f590de4a1b296aa753ed66c2b117ac50c9b937814407287346732bf1` | Control-tracked and byte-identical to Control's copy; not tracked here
- `docs/session-continuity-apprentice-field-guide.md` | `a0641485c2ad3c476ea995289b8875c214c131674c20e24c3d4f1effe8707a45` | Control-tracked and byte-identical to Control's copy; not tracked here
- `docs/tray-session-clinic-watchdog-20260724.patch` | `b61ad1b53a6411eda41ccd24fc8eaeb220e9fbcd3d5cfd536f45dba70cbfa8e6` | Control-tracked and byte-identical to Control's copy; not tracked here
- `ops/src/runbook/agents/registry-key-goes-here.yaml` | `2bcf98bcf7cc6688579922ab12bd1a306b3bcbcf439e3637bf1b49a50065be6f` | Kevin's placeholder sketch; committed when it has content

## Removed from the replaced lanes before the copy (41)

- `ops/bin/help` | nooksee/sessions main | before `039967c7b4aea2d48be979a6cd537c8bf443c67d940a759ddbe3990d283d8106` | now `d19293026e3a0cb34fd8bd545df9fedf5bd52bf13907127623c44555a4c26dd3` | replaced by the port version
- `ops/bin/template` | nooksee/sessions main | before `309415a0c67b13c190957bc38d395200ff00fe65f6d498c4b7b93d062d9d57f9` | now `309415a0c67b13c190957bc38d395200ff00fe65f6d498c4b7b93d062d9d57f9` | replaced by identical bytes
- `ops/lib/scripts/closeout.py` | nooksee/sessions main | before `ca1135811aa4e9533bbcdfac1aa38f1307c93a18bbfa61bfad7cf941f06b0dca` | now `c2177b6ee466bef6b5e8d09e38866d2a42339928535ff66bb1deba22e31012aa` | replaced by the port version
- `ops/lib/scripts/mind.py` | nooksee/sessions main | before `4159b57fc52cb923bbe2e3f248416fc32d2c5da1d6127a93df97b55eaadfe836` | now `16fcce28fbbc27e96d853faeccabe53a004f0b0c7016792969cf5244e73d603c` | replaced by the port version
- `ops/lib/scripts/gauge.py` | nooksee/sessions main | before `d86b3c8fa2450088e4a4231d0bb1283a91ca0f56ef2f2a77b81acaf0d174e58b` | now `1887099ce638a0936c277a3a4f559a8e8e7c5fe532c6179ad68874affeb3f2b5` | replaced by the port version
- `ops/src/docs/readme.md.tpl` | nooksee/sessions main | before `8c83b6e1eaaaf9b29a2af4a9a1b50698774c0bb48df7d2aef7b03f5143858af6` | now `8c83b6e1eaaaf9b29a2af4a9a1b50698774c0bb48df7d2aef7b03f5143858af6` | replaced by identical bytes
- `ops/src/docs/spec.md.tpl` | nooksee/sessions main | before `7cc75efd270d1173212a55fa12771c28b1dbec258e386ffed657e9596e6adf6c` | now `ea02a1798b0d982a0a24c602eac24589efbf624acb65be48c7ec06adeb87e453` | replaced by the port version
- `ops/src/reports/receipt.md.tpl` | nooksee/sessions main | before `12bf91bb4d5cefe8e8a171c5224962f8ba9ab2502402203a7c8ff2d9cf721121` | now `62d6bc881c2300208376dc2746c30d518a7d8adb20b83394d806806afab83f90` | replaced by the port version
- `ops/src/reports/ror.md.tpl` | nooksee/sessions main | before `ead427d1b3c23e1b833f932f978537fa3f3abfd70059f336819ca9458feb7070` | now `ead427d1b3c23e1b833f932f978537fa3f3abfd70059f336819ca9458feb7070` | replaced by identical bytes
- `ops/src/reports/closeout.md.tpl` | nooksee/sessions main | before `fa38f6cc64dfb7934582367b0e85fed8159c193960c63bac828ed7ded7aad245` | now `fa38f6cc64dfb7934582367b0e85fed8159c193960c63bac828ed7ded7aad245` | replaced by identical bytes
- `ops/src/reports/custody.md.tpl` | nooksee/sessions main | before `8178f51c626ea9cdcce033b2d8ae0f24dfca487a8baa337ba5f3b1edd9f8be9d` | now `8178f51c626ea9cdcce033b2d8ae0f24dfca487a8baa337ba5f3b1edd9f8be9d` | replaced by identical bytes
- `ops/src/reports/validation.md.tpl` | nooksee/sessions main | before `e939d8aa7b49fd3aebbb9e4bd36f29fc4e070efe7a691f9d073f4e1da8066911` | now `e939d8aa7b49fd3aebbb9e4bd36f29fc4e070efe7a691f9d073f4e1da8066911` | replaced by identical bytes
- `ops/src/reports/packet.md.tpl` | nooksee/sessions main | before `f8595276d8c064a878c685cf1c7cb8367fd7aa496bb9ad240cf62aa8f398cbf4` | now `f8595276d8c064a878c685cf1c7cb8367fd7aa496bb9ad240cf62aa8f398cbf4` | replaced by identical bytes
- `ops/src/scripts/script.py.tpl` | nooksee/sessions main | before `804ea32dec17e4a81ce7ea1a86bfcae2f5f066ae097d52a639439ee8d713c883` | now `4ee4ff1539692c648dd37773a932c2f47f7bab9191246beb750f67a739c8a4f4` | replaced by the port version
- `ops/src/tests/test.py.tpl` | nooksee/sessions main | before `f42aa1f7b355809145ffc9c8d6b83e201ff4071965e4275b0603be5fee58d3f5` | now `f42aa1f7b355809145ffc9c8d6b83e201ff4071965e4275b0603be5fee58d3f5` | replaced by identical bytes
- `ops/src/runbook/agent-input.yaml` | nooksee/sessions main | before `2bcf98bcf7cc6688579922ab12bd1a306b3bcbcf439e3637bf1b49a50065be6f` | now `2bcf98bcf7cc6688579922ab12bd1a306b3bcbcf439e3637bf1b49a50065be6f` | replaced by identical bytes
- `tools/test/test_gauge.py` | nooksee/sessions main | before `eba948412185fa2e1c453899d922f8a8a37af765ac4dab3ed47319002540f05f` | now `eba948412185fa2e1c453899d922f8a8a37af765ac4dab3ed47319002540f05f` | replaced by identical bytes
- `tools/test/test_mind.py` | nooksee/sessions main | before `9a4b6c8cfade74bd8c321edd772a77daf75cc599de72a74663509adcc9013433` | now `bc9dd5ec1c0c5be7ebebb47a4122039b5a70431f08552fbfaad818e2fcb732ab` | replaced by the port version
- `tools/test/test_closeout.py` | nooksee/sessions main | before `7a80812a9687b89bde0f45d51d9328aee03e3ff9ba1957c54edfa04cbeb69ab3` | now `7a80812a9687b89bde0f45d51d9328aee03e3ff9ba1957c54edfa04cbeb69ab3` | replaced by identical bytes
- `docs/clinic-aggregate-contract.md` | Control HEAD | before `a6c1bf09ecba8e2d333101a976ebc5658dbb46372fa2874537edd1821eb96634` | now `a6c1bf09ecba8e2d333101a976ebc5658dbb46372fa2874537edd1821eb96634` | replaced by identical bytes
- `docs/tray-session-clinic-watchdog-20260724.patch` | Control HEAD | before `b61ad1b53a6411eda41ccd24fc8eaeb220e9fbcd3d5cfd536f45dba70cbfa8e6` | now `b61ad1b53a6411eda41ccd24fc8eaeb220e9fbcd3d5cfd536f45dba70cbfa8e6` | replaced by identical bytes
- `docs/resource-state-contract.md` | Control HEAD | before `9a984c6a54ad1b6cdeb8d797b1f54e990b31fac3f5a50ddb0f4b6e41dd338bf8` | now `9a984c6a54ad1b6cdeb8d797b1f54e990b31fac3f5a50ddb0f4b6e41dd338bf8` | Control-tracked; restored to its recorded bytes; the port version waits for stage D
- `docs/session-clinic-integration-review-response.md` | Control HEAD | before `f6e252d0f590de4a1b296aa753ed66c2b117ac50c9b937814407287346732bf1` | now `f6e252d0f590de4a1b296aa753ed66c2b117ac50c9b937814407287346732bf1` | replaced by identical bytes
- `docs/MANUAL.md` | nooksee/sessions main | before `fe2941477da97a7ff2fb63df336807360c050ef9dab40073beb6f75a5bfeb826` | now `de73043834a760eb7b182e2673a5f18cde8edc29add992a85786973be84854d1` | replaced by the port version
- `docs/session-continuity-apprentice-field-guide.md` | Control HEAD | before `a0641485c2ad3c476ea995289b8875c214c131674c20e24c3d4f1effe8707a45` | now `a0641485c2ad3c476ea995289b8875c214c131674c20e24c3d4f1effe8707a45` | replaced by identical bytes
- `docs/INDEX.md` | nooksee/sessions main | before `b1519cea4109160fa19253ac135b5bd03cbc7aed116f09d545c4bd09108d401b` | now `ab5752daba0b43bb7e0f3eb36c61eeffb27f67823af1b4aa3e0e83a069dee3e7` | replaced by the port version
- `docs/ops/README.md` | nooksee/sessions main | before `b5a3cac9decc8a8527f735c8bf12219d67af96c88a0b96f04891050e954b2e69` | now `8ea5ac16811cb624dd472ffa96bd34ca5058047cc8455be1d20e76c1ac117667` | replaced by the port version
- `docs/ops/registry/scripts.md` | nooksee/sessions main | before `93a82d2b48a75ddbaf64f1154546cf1aefde8e1030b719b6b9ca682b0dc61cd4` | now `9bf42e15ff4594f6d242b5642143ad03dfa0e5045192fe8b354eb4853fd13bf3` | replaced by the port version
- `docs/ops/registry/test.md` | nooksee/sessions main | before `8f1e152b188e96c7fba2c136588dddef5d57a3fe75e371de79f027f0c2e9c0d3` | now `a085df1df6189431cbf9fc5379bef43b3002ca5d89944c88a6e82701efe7184f` | replaced by the port version
- `docs/ops/registry/runbook.md` | nooksee/sessions main | before `7fe07c89b017e5510bffaf517772985034d295c2c62e68980173fd9992d0cfef` | now `2d8a18a91ab8365e0700b02942b354a8333329c89a099c689d48c818c3b45ab1` | replaced by the port version
- `docs/ops/registry/binaries.md` | nooksee/sessions main | before `5d628cdea588f7c6dbd698d315af805608310a4875dc9248e3f4e695b1e942aa` | now `5d628cdea588f7c6dbd698d315af805608310a4875dc9248e3f4e695b1e942aa` | replaced by identical bytes
- `docs/ops/specs/scripts/mind.md` | nooksee/sessions main | before `423e6620c93645332649b0826c3515c2510ab1817a972db99cc5cdc8bcf460af` | now `58cfe241607992a3a5710c0120ff61020ee531075699f7589760a24b79c376ae` | replaced by the port version
- `docs/ops/specs/scripts/rotate.md` | nooksee/sessions main | before `7ec9646330c24d58930c49c6badccbae1f9b76468885c1b74bce830157389407` | now `c7555fe2bd1e0d337ee8216aca24e30982d57180a4c4b196654f27085f4c6a3d` | replaced by the port version
- `docs/ops/specs/scripts/closeout.md` | nooksee/sessions main | before `68a080a778b6f559ed45ce49c7d6c8bc6e1cd0347ffede4acd481563d25d0125` | now `68a080a778b6f559ed45ce49c7d6c8bc6e1cd0347ffede4acd481563d25d0125` | replaced by identical bytes
- `docs/ops/specs/scripts/gauge.md` | nooksee/sessions main | before `5774df1c52eeff3776aa4adf00760401543035d9ed383061eeb4aed2de16b7e4` | now `a95aab7bea644ac361890cb731d1d5ef82695be0ee3dfddc54825cab697c82bb` | replaced by the port version
- `docs/ops/specs/tools/test/mind.md` | nooksee/sessions main | before `40e48c16b2576475ae746dce17ae2c9ce1184bcc1eba924bad83ce190ca9ebd4` | now `40e48c16b2576475ae746dce17ae2c9ce1184bcc1eba924bad83ce190ca9ebd4` | replaced by identical bytes
- `docs/ops/specs/tools/test/gauge.md` | nooksee/sessions main | before `d11328b66be0442706ce180051374276880d61ce603a32e5ebb4660e5d9aa4e5` | now `d11328b66be0442706ce180051374276880d61ce603a32e5ebb4660e5d9aa4e5` | replaced by identical bytes
- `docs/ops/specs/binaries/template.md` | nooksee/sessions main | before `39867ca92e82b7dd346447c37bf18ad2f7797bea10e8fd0062a6ff34a1a008e0` | now `a0831851659baf42309cdaa7054d363273539be92890664cd891b21e00f40a6a` | replaced by the port version
- `docs/ops/specs/binaries/help.md` | nooksee/sessions main | before `80c375a304f03720b016a2c1516bb92db6b203af03299d63ae34ab3a0f6fc172` | now `5852fbfe42dbe01252a0e8f04d5625a34958aa401f707cf9acf0e990d4cde9ae` | replaced by the port version
- `docs/ops/specs/runbook/agent-input.md` | nooksee/sessions main | before `990946309155e6b63da1e2919d4fa189e0c12a0d2cf35c4f898e4bbaf58dbc86` | now `b0f98358e3333ae7a771aa3489d2075d4de03b022f072dabc8d05d103520024d` | replaced by the port version
- `docs/ops/specs/runbook/repository.md` | nooksee/sessions main | before `96f195f62ef67be85d8045878f86eaea79bb73ad1a894d76dd8711eb83df0aa5` | now `96f195f62ef67be85d8045878f86eaea79bb73ad1a894d76dd8711eb83df0aa5` | replaced by identical bytes

## Manifest of the commit (path | sha256)

- `docs/INDEX.md` | `ab5752daba0b43bb7e0f3eb36c61eeffb27f67823af1b4aa3e0e83a069dee3e7`
- `docs/MANUAL.md` | `de73043834a760eb7b182e2673a5f18cde8edc29add992a85786973be84854d1`
- `docs/START-HERE.md` | `ede014b20fe4527387d23f62c1649eaf8fc55f5400ff276637af0402990509ee`
- `docs/ops/README.md` | `8ea5ac16811cb624dd472ffa96bd34ca5058047cc8455be1d20e76c1ac117667`
- `docs/ops/registry/binaries.md` | `5d628cdea588f7c6dbd698d315af805608310a4875dc9248e3f4e695b1e942aa`
- `docs/ops/registry/runbook.md` | `2d8a18a91ab8365e0700b02942b354a8333329c89a099c689d48c818c3b45ab1`
- `docs/ops/registry/scripts.md` | `9bf42e15ff4594f6d242b5642143ad03dfa0e5045192fe8b354eb4853fd13bf3`
- `docs/ops/registry/test.md` | `a085df1df6189431cbf9fc5379bef43b3002ca5d89944c88a6e82701efe7184f`
- `docs/ops/specs/binaries/help.md` | `5852fbfe42dbe01252a0e8f04d5625a34958aa401f707cf9acf0e990d4cde9ae`
- `docs/ops/specs/binaries/template.md` | `a0831851659baf42309cdaa7054d363273539be92890664cd891b21e00f40a6a`
- `docs/ops/specs/runbook/agent-input.md` | `b0f98358e3333ae7a771aa3489d2075d4de03b022f072dabc8d05d103520024d`
- `docs/ops/specs/runbook/port.md` | `84e09f03c9c15b3e5c2789f7fcdea515a5d9d7cefc728feb1970b4c0c00eb8ca`
- `docs/ops/specs/runbook/repository.md` | `96f195f62ef67be85d8045878f86eaea79bb73ad1a894d76dd8711eb83df0aa5`
- `docs/ops/specs/scripts/alerts.md` | `d69d99e669335c8d0bb99064f1256cf8d09e3aeb66d734d6dfe33b043262f7e4`
- `docs/ops/specs/scripts/archive.md` | `bbca0d75f8ea408710a1f38ef22c78f8f86deb379b9b901829bd535cb23de492`
- `docs/ops/specs/scripts/bloat.md` | `749afdd1a3f56655b2e74f8347feb28f6e9139149aac00674b417aaec1176396`
- `docs/ops/specs/scripts/capsule.md` | `2b0a3893d91d2485b4e5abe9fe125f636959e343eef7f43f2c6a4680a01e8dd1`
- `docs/ops/specs/scripts/chamber.md` | `69c0d0d0bb247a0d9920aec609d64aea35fb00b58531de26af8f263104d052c4`
- `docs/ops/specs/scripts/closeout.md` | `68a080a778b6f559ed45ce49c7d6c8bc6e1cd0347ffede4acd481563d25d0125`
- `docs/ops/specs/scripts/condense.md` | `399982e643df4962065a13f6893a5f5c0213a2ebb3876cad0e9d1858e70d31a9`
- `docs/ops/specs/scripts/conflicts.md` | `e2b2ba4bfd9a39c2b723d281a66f997d89ed7fe8ab11e811772aa1509e6de140`
- `docs/ops/specs/scripts/dossier.md` | `5faa9c836759c559e22d6ee1f8caf08810e58042ebc7e5866f8ef5bfe60b26ab`
- `docs/ops/specs/scripts/elide.md` | `d5c373687be141679f16a20186133d83dc87ca0ae1b03a4835d66e2322ada099`
- `docs/ops/specs/scripts/estimate.md` | `c26aed0b32780fb12b580a681a4f974192f68be599a0316a072485cbb2a0325c`
- `docs/ops/specs/scripts/gate.md` | `6350eedd2e45977d26adfb035f2439914d49b690c7eac0c0e58c8752e47ece91`
- `docs/ops/specs/scripts/gauge.md` | `a95aab7bea644ac361890cb731d1d5ef82695be0ee3dfddc54825cab697c82bb`
- `docs/ops/specs/scripts/history.md` | `b8866136311bafee23118d1b2a019063283bcc7f513b7fd7eb4f541f59e963cb`
- `docs/ops/specs/scripts/identity.md` | `d8f06d8d6c198b4e9a97ac3b863311e8fcf335e633d1f975f13c84338c005f66`
- `docs/ops/specs/scripts/images.md` | `9d6e3f0d190ae8b06457a76395906bba71840e20a47a3fb133f83bb1c8217619`
- `docs/ops/specs/scripts/inventory.md` | `3b6bc93442943c2f79c1c3bc9c24549d089d3809c275b19c21a80c47df80e560`
- `docs/ops/specs/scripts/items.md` | `5f1214751f0e1c3002a54955b8147469e80811db13999743a91f95fb6b837aa9`
- `docs/ops/specs/scripts/janitor.md` | `0849862e3a2cb88f05883063533834bf2369ba6e40a238e317b13317ee49d1dd`
- `docs/ops/specs/scripts/limits.md` | `55e0b04c57d267bc2ae63773c2c7ec7e25eca1e91c6cf77f82cc98b016bf3a9f`
- `docs/ops/specs/scripts/media.md` | `98bd96343143855a9f7e9b76ed1b29b123420cf06c7939a64fbdad032f2a3e5e`
- `docs/ops/specs/scripts/mind.md` | `58cfe241607992a3a5710c0120ff61020ee531075699f7589760a24b79c376ae`
- `docs/ops/specs/scripts/miner.md` | `963bf12557a546d7da939368efb4aaf1833bda5d845bc59c786e34f5ef36260e`
- `docs/ops/specs/scripts/myself.md` | `37d9a07dfd0f60901f58abf7e02d797e307112bbc34a2edaee5c91cfdf1f1fdf`
- `docs/ops/specs/scripts/pressure.md` | `fa5177b712983214a42502bdd7d360a2c362afdc2bccd2439a7cc34f1d9add67`
- `docs/ops/specs/scripts/prime.md` | `2003707e066109d0d48b631f0a3e644265c8f673e0f5c78f4d5270636fd03c49`
- `docs/ops/specs/scripts/pycharm.md` | `1cfbc5c1cb198e331000d7f51f920e3b8d43fb484fdcf3f152952ecdf114c245`
- `docs/ops/specs/scripts/reid.md` | `b1bf530cdb758def773e2b5d99575554818f7f038fe40396f736bf4e43e9e89c`
- `docs/ops/specs/scripts/resources.md` | `62c9d6fd936093aaaec068da7359584eef2904938d9cd1f61f3f275a706135d9`
- `docs/ops/specs/scripts/retention.md` | `be63ad774f4b25ada8605846b813bd3c65eca7260bff77283bb19af7097ff760`
- `docs/ops/specs/scripts/rotate.md` | `c7555fe2bd1e0d337ee8216aca24e30982d57180a4c4b196654f27085f4c6a3d`
- `docs/ops/specs/scripts/rotation.md` | `8587d46aa1744ada3e5f94c72ecb5ec379b9c19288bdf9590d8d9249bf81ddae`
- `docs/ops/specs/scripts/sandbox.md` | `b2dac05d02be723cacaab81f7ed46ae47a662d0c24494d3833ceb860034d3110`
- `docs/ops/specs/scripts/successor.md` | `4a7460a91714ab1a22056a49842d4755a92920eb86aba1936269b12053ff2903`
- `docs/ops/specs/scripts/tablet.md` | `fc58a6d9caf42be45bb7c0c985fe7457f4de6db625ab4ab8de7836f8402d5d7a`
- `docs/ops/specs/scripts/telemetry.md` | `cc96ad07390da95eb5e308131e14ea6ad964522490dc084d2c40fb9129f161fd`
- `docs/ops/specs/scripts/transcripts.md` | `5d0fe76198024189719cc6f20811b295cb0a3b3d2fc4eaa0bf73862cf09ba766`
- `docs/ops/specs/scripts/vitals.md` | `cf0ef9af65f6ec3b098b240d5c31b4c6ab2143ef546488a005b24a384c8734f2`
- `docs/ops/specs/scripts/watch.md` | `dec9ed5408927c7146e6715e9606b032686be18bd9f5d387ef8fc8413950dbc9`
- `docs/ops/specs/scripts/workers.md` | `108f72e06c5dd4df00d7a69583aa0ef4cef1226635c33f54a3c6511348341e3d`
- `docs/ops/specs/tools/test/gauge.md` | `d11328b66be0442706ce180051374276880d61ce603a32e5ebb4660e5d9aa4e5`
- `docs/ops/specs/tools/test/mind.md` | `40e48c16b2576475ae746dce17ae2c9ce1184bcc1eba924bad83ce190ca9ebd4`
- `logs/.gitkeep` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `ops/bin/help` | `d19293026e3a0cb34fd8bd545df9fedf5bd52bf13907127623c44555a4c26dd3`
- `ops/bin/template` | `309415a0c67b13c190957bc38d395200ff00fe65f6d498c4b7b93d062d9d57f9`
- `ops/etc/.gitkeep` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `ops/lib/scripts/alerts.py` | `e06f766e5cb7c7a315725a2fd0953b0ff1aa4e359ae6cd64ffa5a6358e3ee10a`
- `ops/lib/scripts/archive.py` | `a12badee8065e798857fd27a21a377eb281021cb690a56adfbae2e75a085c758`
- `ops/lib/scripts/bloat.py` | `fc72d10c0c60f5389f9826a0d6d17cf5262ca22d76036634a144e2f4a39c4260`
- `ops/lib/scripts/capsule.py` | `acf0e9763b43a816061b58e568ab89f3739dd23bf2079adb44f38228d4fb1a0e`
- `ops/lib/scripts/chamber.py` | `1f6e53ebf705e5a98de33c091a115260c643039899b70980d83e793713465956`
- `ops/lib/scripts/closeout.py` | `c2177b6ee466bef6b5e8d09e38866d2a42339928535ff66bb1deba22e31012aa`
- `ops/lib/scripts/condense.py` | `240a8e486e7708c820f74cc1e9940ad02d42e11b1913c06ccef3af7f5c46b608`
- `ops/lib/scripts/conflicts.py` | `1e10c2dd8d7a33e9c19f22e1d1cf572dd478ac0534f32a104ff63959386b51a5`
- `ops/lib/scripts/dossier.py` | `a0d2b13f9b97cf2b34b9006c4c76bf7775cf009a9906e3c23d4bb10fce94cb32`
- `ops/lib/scripts/elide.py` | `78f124a890db445ad474c5eacd748643e173474839c1db445e8caa55d78efc8f`
- `ops/lib/scripts/estimate.py` | `8913acbb7ac87340ac3723173d0647931f5e67d179086c71245a26a969aa4b4e`
- `ops/lib/scripts/gate.py` | `f6f3f97153c600bb23ce1503dee33615732024de2cbeebaf6dfec60b05a7f053`
- `ops/lib/scripts/gauge.py` | `1887099ce638a0936c277a3a4f559a8e8e7c5fe532c6179ad68874affeb3f2b5`
- `ops/lib/scripts/history.py` | `cc30e387f8e1645d0be43db1269bdd867c78f4211583c45db15ca48c5be06224`
- `ops/lib/scripts/identity.py` | `232fdd8d5d91538a613926ffe72e4b4d0eda28c73a03de69fafc87aa2cc3cf50`
- `ops/lib/scripts/images.py` | `ffe450f8ecfb63a759dc866bee958dfb4cbee0d8faf1c674caa5d41173eda2b9`
- `ops/lib/scripts/inventory.py` | `c1125baa456f9c85e5c122c44aa0d453f19fd542dc7d738b0b21adcaa99ce462`
- `ops/lib/scripts/items.py` | `dda2b0e2066a732b63c14af8e27db182d3a47e51075eb05b3a0af4db2144273e`
- `ops/lib/scripts/janitor.py` | `317a866b078d67a7a7973b10e69b0378bc09b6d053bc526f859c97a56aba3520`
- `ops/lib/scripts/limits.py` | `15fb9e44b8e2dc2e2fa52851e8de51e9612360bd14043cea395c5655fbc9023d`
- `ops/lib/scripts/media.py` | `3c852eb0da228e2676749e3002d134bd5f538bdac71e333bad4b937ac8e849d2`
- `ops/lib/scripts/mind.py` | `16fcce28fbbc27e96d853faeccabe53a004f0b0c7016792969cf5244e73d603c`
- `ops/lib/scripts/miner.py` | `82c726eb7bddb90c81d76e30d5c7b454beceaaabce9075ea7dba6a1fd174c343`
- `ops/lib/scripts/myself.py` | `4a490cca299e1c89659b49604b928bb46a640e741fc4495c17a17bd353af9f3c`
- `ops/lib/scripts/pressure.py` | `baee1dcce50ec6f3277a0033e7b8e24460c4d9f06c5212daa02446e321255ee0`
- `ops/lib/scripts/prime.py` | `48e80187553c87cb80d8213cbbdcebcaf65bc7daae1ab802485194eccb715baf`
- `ops/lib/scripts/pycharm.py` | `3c666f747d3684ce30b711b15f476168ee6fa19b93cfb99f55ac09e157970111`
- `ops/lib/scripts/reid.py` | `a9a416001eb2ec9d849606fff282040d1d3ce4c63f59a0129af20d4cf080d6c9`
- `ops/lib/scripts/resources.py` | `b14a91d75754379c6173d58a3cc71e284c362e2845290c9df07755e91a578302`
- `ops/lib/scripts/retention.py` | `43c6c5905ffc3cddb6de7be25af67cd6fc0513dd006d1efe54f8fcc66cdc3765`
- `ops/lib/scripts/rotation.py` | `ff19215b3f83450662950b78b37a01cf4212bd79d749972aa46a621a2a7cf375`
- `ops/lib/scripts/rounds.sh` | `26f3b44efd74072af4b2935e11cd11953a772007303080bb6466d8648374c7f8`
- `ops/lib/scripts/sandbox.py` | `8e14c9a938b61859631b29095fea1641cc0ae1d7d4fbe48957a832518ede99dd`
- `ops/lib/scripts/successor.py` | `d07b77b797fed235ff59901dd6bec5f500e8d8f3280c1f0a3cab0d19d28fd90d`
- `ops/lib/scripts/tablet.py` | `72129c800e67661c0ce6e4c051238f0d7b9213b2de3dade4432eda371fcb04ea`
- `ops/lib/scripts/telemetry.py` | `c0a92fe81a887773dd4f76c60a762cf22aff218ea0321c40e4b26a0aaa1777ed`
- `ops/lib/scripts/transcripts.py` | `28d5a6818cdd91252dff71858c232e1c58de861441fd35394e0a408016049297`
- `ops/lib/scripts/vitals.py` | `30b0aaf71347260cdb3e679573ac7dde3809ec574446027baaeac8aef3a1d233`
- `ops/lib/scripts/watch.py` | `319b9fb39f07198c329f9c4a72ded9e32ba4fe2210313a8f92f0a47d4f6a31a8`
- `ops/lib/scripts/workers.py` | `9303a0a438d1fd0cbe5797c87277576982a5fefbabb89c82ecf3c50138489af2`
- `ops/src/docs/readme.md.tpl` | `8c83b6e1eaaaf9b29a2af4a9a1b50698774c0bb48df7d2aef7b03f5143858af6`
- `ops/src/docs/spec.md.tpl` | `ea02a1798b0d982a0a24c602eac24589efbf624acb65be48c7ec06adeb87e453`
- `ops/src/reports/closeout.md.tpl` | `fa38f6cc64dfb7934582367b0e85fed8159c193960c63bac828ed7ded7aad245`
- `ops/src/reports/custody.md.tpl` | `8178f51c626ea9cdcce033b2d8ae0f24dfca487a8baa337ba5f3b1edd9f8be9d`
- `ops/src/reports/packet.md.tpl` | `f8595276d8c064a878c685cf1c7cb8367fd7aa496bb9ad240cf62aa8f398cbf4`
- `ops/src/reports/receipt.md.tpl` | `62d6bc881c2300208376dc2746c30d518a7d8adb20b83394d806806afab83f90`
- `ops/src/reports/ror.md.tpl` | `ead427d1b3c23e1b833f932f978537fa3f3abfd70059f336819ca9458feb7070`
- `ops/src/reports/validation.md.tpl` | `e939d8aa7b49fd3aebbb9e4bd36f29fc4e070efe7a691f9d073f4e1da8066911`
- `ops/src/runbook/agent-input.yaml` | `2bcf98bcf7cc6688579922ab12bd1a306b3bcbcf439e3637bf1b49a50065be6f`
- `ops/src/scripts/script.py.tpl` | `4ee4ff1539692c648dd37773a932c2f47f7bab9191246beb750f67a739c8a4f4`
- `ops/src/tests/test.py.tpl` | `f42aa1f7b355809145ffc9c8d6b83e201ff4071965e4275b0603be5fee58d3f5`
- `tools/test/test_alerts.py` | `7883b806aec8e9fe26552b26c8e1580dabc1029e1dadb3700e926250e4fb8811`
- `tools/test/test_alerts_arity.py` | `e134d4350bc99ce90ff400cb9a283945082cb436fe6ad2d942512de3ed240a46`
- `tools/test/test_archive.py` | `78dfa060c8700b6b2ae3d5c6ccafd3712fe2bde58d1f8d13bc2df1e93a93d03c`
- `tools/test/test_bloat.py` | `d9534bb15b5bf1d2b01c14f7d07356fd8c0da5dca833c67e785a7d2b6081f98c`
- `tools/test/test_capsule.py` | `a9ee1829eeffc5fc9c4f4e98e0d03746f7dd8ff344d939204abb1e6512e78885`
- `tools/test/test_chamber.py` | `cfde6ddcd1071d7aeb628c68e693631e16bcd887f9aa4d074469cea0341f34b9`
- `tools/test/test_closeout.py` | `7a80812a9687b89bde0f45d51d9328aee03e3ff9ba1957c54edfa04cbeb69ab3`
- `tools/test/test_condense.py` | `a7c467dbb7186ffef331a9db5ea6ac77617af5eb55ef889eb9371553528699c8`
- `tools/test/test_conflicts.py` | `484fcb74cdfd46ede503e418b75b7a4acb23ef5b94fcd83ddd1518f6ac1eb1a7`
- `tools/test/test_dossier.py` | `cd812e729ab7b949a4d367eb8c32beafb673d757b6b8eb6eabb08df59f3eea97`
- `tools/test/test_elide.py` | `e076da5a4bba3a7b702c707557d0cda14a2bf72f7ae5889d54bf3fe62ab30bed`
- `tools/test/test_estimate.py` | `0d386a3766ede74f19603d42caa3091409840f1674cb2d2f97c35693addefc58`
- `tools/test/test_gate.py` | `f206d0fdff35488436d6da4c3907de70fd123498f2ee17fcf3e54dad5ebcc268`
- `tools/test/test_gauge.py` | `eba948412185fa2e1c453899d922f8a8a37af765ac4dab3ed47319002540f05f`
- `tools/test/test_history.py` | `53e4714bad69442037a82cfba696e5617e4326a6674eed7e5f883be9b5cd04e5`
- `tools/test/test_identity.py` | `5a5005c3346c57947221f239ec163232676057afb87bbec71e57397b9d4f55f5`
- `tools/test/test_identity_held.py` | `f62fb2bcfda61ce1fe3da2d9145b0360f0b49d8c60c5eb2537d7e043a79705c7`
- `tools/test/test_images.py` | `31d5ca0edafa5d5c845d48ef5a8c52fe31403cd5e8211d8ed11f20a35eb34436`
- `tools/test/test_inventory.py` | `7b306fd143d32e75678afb5a34bcceff17d1144d622687e3056c5e6774178fae`
- `tools/test/test_items.py` | `dc2b169de5903d4157c796c13f6ba3b1bcf1826c02f1e671f5004d278f725658`
- `tools/test/test_janitor.py` | `b469662c5370bc10aebb0e01311ebd663e45aedc6a2ecf55c46087234a4a9364`
- `tools/test/test_limits.py` | `dfff85db7359fcb42135793060a7ce67a15e89b91a373cb75b75d6f5964ee871`
- `tools/test/test_media.py` | `96d9156ac8e415acab1d1c794696b624dfb5bc318e7a8cb8940e347b3d263a31`
- `tools/test/test_mind.py` | `bc9dd5ec1c0c5be7ebebb47a4122039b5a70431f08552fbfaad818e2fcb732ab`
- `tools/test/test_miner.py` | `ca0446648d6848cee7766a3076609f8d5fcc13defa062b7ee30c578a54363438`
- `tools/test/test_myself.py` | `44077360ce129a1b7e86ea20e5b6f13106a11ea358f1a1457f1680bf5a818db1`
- `tools/test/test_pressure.py` | `d544dec40861a09b77fcec85afbe54d184ccc9ba355db1f1dee5ab41b7daaff8`
- `tools/test/test_prime.py` | `b567b970a60ad88bea9922f16a970057ada39fde9328c9a3f096a2a5096636ad`
- `tools/test/test_pycharm.py` | `46554301a6b971747b81cec40dc1ee0ec1c0a2be7b3474e061ce3c5f2ec0cfa0`
- `tools/test/test_reid.py` | `5644d1292c1f31a64100fd5780eec36f9119e7a15142781ad50966b52118ca4d`
- `tools/test/test_resources.py` | `45bd03f73852222ec2c4cc3a5bfbe128bc9e684658d31d336179e689400a1b47`
- `tools/test/test_retention.py` | `22c8805863c66721ad05eacef3c7176687905728286a4063ee028b43e7fce4de`
- `tools/test/test_rotation.py` | `874c763ab122e37cac69005f9830b306f3ec2278ba17075315b7db6321e82d5e`
- `tools/test/test_rounds.py` | `e6b7a89019b3ba4a1baac9eb06927ca79918724f80b58f34deaaaa9b10607f66`
- `tools/test/test_sandbox.py` | `7d8d0216bf6e8e00658a288c07bea4805b260ac37ac59ca37af9e533ba0708e4`
- `tools/test/test_successor.py` | `16bc26aa8055940177767e98573fd0d6b8659efae7dca4289629d829e70b0a80`
- `tools/test/test_tablet.py` | `04278318fc00ef6f620868df24e44a6292a3a98f798d52f5681b2e206e5a0c1b`
- `tools/test/test_telemetry.py` | `6f146932f2a3fb3d170e5d74ec4c42f29c89a60841ada7047d0cdacd032a4622`
- `tools/test/test_transcripts.py` | `acb1ba778c9c0218690e2fdcca4cb39b36665e9cd37c304ad2b950aaa1297365`
- `tools/test/test_vitals.py` | `906117071fc7f5ccf581b9bc46cd116dd32e3d810c468c5a5d96724312a6728c`
- `tools/test/test_watch.py` | `f4aeea08252ee00178a03b6612280c71b99f42cc401bd58ff1bb49682a5366f0`
- `tools/test/test_workers.py` | `681fdcab567c7c71329de4d240967ed02f92baeef5cde1389a2da1a5e9f4a5d5`

**Correction, by the Assistant Session Continuity Manager (Claudine Colbert), 2026-11-04 22:26:08 EST.** In this record, PR #1 refers to the nooksee/sessions repository as it stood before its history rewrite of 2026-11-04. Each such pull request's title, body, comments and reviews are in the custody export of batch sessions-prerewrite-20261104, and the map from each number to its export entry is in archives/receipts/history-rewrite-20261104.md, the rewrite receipt.
