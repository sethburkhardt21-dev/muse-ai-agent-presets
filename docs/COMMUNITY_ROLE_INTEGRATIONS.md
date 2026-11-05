# Community Muse capabilities — role-oriented intake recommendations

**Status: research and interface design only.** A public catalogue entry is not a permitted host connector, paid API entitlement or verified safe installation. New third-party versions must be pinned, inspected, license-checked, and exercised within the receiving account's actual supported Muse environment before adoption.

| Neutral role | High-value candidate integrations | Scope and safety posture |
| --- | --- | --- |
| Coordinator | Task board (Asana/Linear/Todoist), GitHub, local task ledger | Read-only first; task creation/update separately confirmed and receipt-bound |
| Software Engineer | [Superpowers](https://github.com/obra/superpowers) debugging/review methods; GitHub/GitLab; Sentry | Link approved methods; no privileged hook or unattended merge by default |
| Model Builder | Hugging Face model metadata, local trainer, Langfuse traces | Model downloads, GPU runs and paid services each have separate source/resource gates |
| Research & Evaluation Scientist | [Muse Skills](https://github.com/Israelmusondaayliffe/muse-skills) research procedures; Exa/Brave/Tavily | Retrieval is source evidence; original independent rubric and examiner remain separate |
| Creative Studio | Figma/Canva; optional media renderer | Prefer local/owned art; cost and asset redistribution restrictions require opt-in |
| Adversarial Verifier | Source-control fixtures, Sentry, bounded mutation runner | Authorized targets only; negative tests cannot claim external vulnerabilities by analogy |
| Personal Companion | Tasks/calendar, read-only weather; optional smart lighting and media | Sensitive account/device writes disabled; clear user approvals and emergency stop |
| Garden Companion | Read-only weather, plant-reference retrieval; optional Rachio | Irrigation commands are physical effects—never enabled through the default preset |
| Learning Coach | Private documents, Readwise/Notion, evidence retrieval | Owner/source rights, no cross-learner exposure and human review for high-stakes material |
| Claims Adjudicator | GitHub artifacts, read-only trace/provenance evidence | Judgments are a separate responsibility from creating or altering the evidence |
| Reverse Engineering Researcher | Local Desktop Commander with explicit grants; offline Ghidra/tshark/Scapy; source control | Authorized toy apps or pre-supplied PCAP only; no default external probes, malware execution or credentials |
| Evidence Finder | Read-only search/document connectors | Raw findings preserved; no scoring/verdict fields and no direct effect authority |

**Reusable upstream candidates:** [Muse Skills](https://github.com/Israelmusondaayliffe/muse-skills) describes host-adapted skill workflows; [Muse Connectors](https://github.com/bluman1/muse-connectors) describes approximately 150 connector skills with per-file manifests and explicit security assumptions; [Superpowers](https://github.com/obra/superpowers) provides engineering methods and a separate developer-host plugin path. Review one tool at a time; do not vendor an entire third-party repository just because it is reachable on GitHub.

Host boundaries: Muse/Hatch skills and Muse Code plugin configuration may differ. Copying an upstream `SKILL.md`, `manifest.yaml`, hook or MCP declaration is not equivalent to registration. Confirm native discovery and original call output on the specific host. Provider API keys always remain in host-supported credential custody.

**Admission record for every donor item:** exact source URL/commit and file; upstream license; exported artifact identity; declared account scopes; allowed network hosts; side effects; cost; source tests; host-native invocation; independent reviewer; update/rollback owner. No automated download, plugin install, credential request or external action is performed by this document.
