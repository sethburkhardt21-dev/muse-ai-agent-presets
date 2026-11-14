# Tailor a Resume Without Fabricating Experience — operational depth

Read only the branch needed for the current task. These are working methods, not a demand for additional approvals on ordinary reading or drafting.

## Domain method

Resume tailoring maps requirements to evidence without turning aspirations into experience. Separate direct evidence, transferable evidence, exposure and unsupported claims. Preserve contribution scope, dates and maturity: designed, implemented, tested, integrated and deployed are different claims. A portfolio project can be strong evidence without being described as paid employment or production adoption.

## Output contract

Deliver the tailored text requested, a concise requirement-to-evidence map and unresolved gaps. Keep factual claims, metrics, credentials and contribution scope supported by supplied records. Do not guarantee interviews, parsing performance or hiring outcomes.

## Choose the right action

### The posting asks for years of paid experience but the evidence is personal projects.
Present the projects prominently and label their actual context.

**Avoid:** Do not convert elapsed hobby time or repository age into employment tenure.

### A project has tests but no observed deployment.
Use implemented and tested, and identify deployment as unproven if relevant.

**Avoid:** Do not describe it as production-operated or widely adopted.

### A strong metric is missing.
Use the supported qualitative result or a verifiable count from supplied evidence.

**Avoid:** Do not manufacture percentage improvement or user numbers.

### Several people contributed.
Describe the user's exact role and distinguish team outcome from individual ownership.

**Avoid:** Do not claim sole authorship because it makes a stronger bullet.

### The requested requirement is not supported.
Record the gap and use adjacent evidence only with accurate framing.

**Avoid:** Do not add the keyword as a skill just to satisfy a matching score.

## Worked example (authored, synthetic)

**Input:** The candidate built a personal Python tool with 42 passing tests and no deployment evidence. The role asks for Python automation and Kubernetes production operations.

**Method:** Use the tool as direct evidence for Python automation and mark Kubernetes production work unsupported.

**Result:** A truthful bullet is: Built and tested a Python automation tool with 42 regression checks. Do not add production users, an employer or Kubernetes operation claims.

## Edge or recovery example 1 (authored, synthetic)

**Input:** The candidate later supplies a team project but only authored the parser component.

**Method:** Retain the team context and name the parser contribution.

**Result:** Describe parser implementation and its observed tests, not ownership of the entire platform. A team outcome can be referenced only with that scope clear.

## Failure diagnosis

### The tailored resume is stronger but not defensible in an interview.
**Likely cause:** Language inflated scope, seniority or outcome.

**Repair:** Trace each claim to evidence and narrow unsupported wording.

**Recheck:** The user can explain the exact contribution without contradicting the record.

### A credential appears because the role requires it.
**Likely cause:** Requirement text was copied into the candidate profile.

**Repair:** Remove the credential and keep it as an explicit gap.

**Recheck:** Only actually held credentials appear in the resume.

### A project bullet claims deployed capability from a source-only test.
**Likely cause:** Maturity labels were collapsed.

**Repair:** Restore implemented/tested wording and preserve the test evidence.

**Recheck:** Deployment and adoption claims require their own evidence.

## Preserve for the next turn

Keep the base resume, posting version, evidence map, approved phrasing and unresolved claims. Resume the next targeted section without overwriting the master resume or inventing missing qualifications.

## Practice and mechanical checks

Three authored public exercises cover a standard task, an edge condition and recovery or changed evidence. Their answers are development examples, not held-out results. Supplied-output checks cover only declared facts and invariants; language quality, visual quality and real provider behavior remain separate.

Practice case IDs: `resume-tailor-r3-standard`, `resume-tailor-r3-edge`, `resume-tailor-r3-recovery`.
Packaged exercises live under `practice/`. The optional `practice/check_outputs.py` checks supplied JSON outputs; it does not call Muse or certify semantic/visual quality.

## Evidence boundary

Original specialist synthesis with source and fixture checks. No matched Muse comparison has been executed; greater domain detail is not measured superiority over upstream packages.
