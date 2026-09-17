# HW1 progress note (local scratch — not a submission file)

Help style: **instructor tutorial** (homework/module-1/hw1-tutorial.md)

## Current status
Parts A, B and C complete. Only the video remains.

## Next step
1. Record the video (student). Checklist at the bottom of this file.
2. Commit the staged deliverables once the student gives the go-ahead. Nothing is pushed.

## Final check results (all green, all offline)
- `uv run pytest --runxfail tests/test_hw_holes.py -k hw1` -> 5 passed
- `uv run pytest tests/test_agent_tools.py tests/test_auth.py tests/test_eligibility.py` -> 24 passed
- `uv run pytest` -> 109 passed, 12 skipped, 22 xfailed, 5 xpassed
The recorded conversations were live against claude-opus-4-6 via Anthropic.

## Deliverable checklist
- [x] Part A: `get_policy` — exact match over load_policy_docs(); miss returns not_found
      naming the id and pointing at search_help_center
- [x] Part A: `search_products` — AND over whitespace tokens, substring match on
      title+description; store via get_store_by_name; limit clamped 1..25; sorted price,id
- [x] Part A: `list_my_orders` — role dispatch; support returns invalid_argument
- [x] Part A: `cancel_order` — not_found -> scope (can_cancel_order) -> status=='placed';
      scope before status so a stranger learns nothing about shipment state
- [x] Part A: `find_order` — rapidfuzz partial_ratio vs product title, cutoff 70, top 5
- [x] Part A: additional tool `get_product(product_id)`, registered in _COMMON_TOOLS for
      all three roles. Supporting `db.get_product` + `_product_from_row` added to
      agent/db.py (list_products refactored to reuse it).
- [x] Part A: focused and regression tests pass
- [x] Part B: 15 records in hw1-session.jsonl, all three roles, all judged
- [x] Part C: RESP-1 under-scoped in the system prompt; revised on recorded evidence
- [ ] Video (<=5 min, continuous) — student records; stays PENDING until done

## Part C, as submitted
**Requirement:** RESP-1, "Cite the policy identifier for every claim derived from a
policy document."

**Why it is a prompt problem, not a tool problem.** Eligibility is computed correctly in
code: seed/generate.py runs every order through effective_return_window_days, so a store
override is already applied before the agent ever sees `refund_eligible`. The tools
returned the right answer every time. The model simply did not treat eligibility as a
policy claim.

**The omission.** RESP-1 was present in SYSTEM_PROMPT_TEMPLATE but expressed too vaguely
("Cite the policy id ... for every policy claim") to fire when the agent reasoned from
the refund_eligible flag rather than from a retrieved document.

**Evidence, all recorded before the edit.**
- record 4  (order 3980): "not eligible ... this is *typically* because the refund
  window has passed" — hedged, no citation.
- record 6  (order 961, Northwind): asserted eligible; never looked up the 45-day store
  override that is the actual reason.
- record 12 (order 90, Saltbox): "not eligible based on the system check"; never
  mentioned the 7-day store override.
- record 9 is the control: there the agent happened to call search_help_center, had a
  policy id in context, and did cite cw-refunds twice. Same prompt, inconsistent
  behavior — the signature of an instruction that is not reliably triggered.

**The edit** (agent/agent.py, tool guidance, 3 lines added):
    Whether an order can be returned or refunded is a policy claim: look up the
    governing policy before you state it, and cite the store's own policy doc
    when that store sets its own return window.

**After** (record 15: same request as record 12, fresh session, read-only so the
starting data is unchanged): the agent called get_order, get_product and
search_help_center, explained that Saltbox Pantry's 7-day window overrides the platform
default of 30, and cited store-saltbox-pantry-policy plus cw-disputes.
prompt_version for the support context: 7b851f9404ea -> 1dc575bed00c.
The same edit renders as b3f4a5686618 -> 2fa455489e9e for a shopper context, because
prompt_version hashes the *rendered* prompt, which includes the injected role block.

**A second omission tested and rejected.** ESC-2 ("account changes of any kind" go to a
human) is genuinely absent from the prompt, and record 10 shows the agent offering
escalation for an email change without calling escalate_to_human. A prompt edit was
tried and did work — escalate_to_human fired and ticket 151 opened. It was reverted and
its record deleted, because the better diagnosis is that ESC-2 itself is the problem: it
leaves no room to offer the user their own options (change it in account settings)
before opening a ticket, which for a routine account change is likely more appropriate.
Record 10 is therefore filed as problem_source `specification`. The revert was verified
exact: prompt_version returned to b3f4a5686618 byte for byte.

## Part B summary
15 records | shopper 11, merchant 1, support 3 | 11 met, 4 not met
problem_source: null x11, prompt x3, specification x1
Not met: record 4 (RESP-1/prompt), 6 (RESP-1/prompt), 10 (ESC-2/specification),
12 (RESP-1/prompt)

Required-case coverage:
  authorized shopper 4127      -> record 1
  order 3980 outside window    -> record 4
  order 4455 above threshold   -> record 2
  merchant store 2 vs 4127     -> record 3
  store policy override        -> record 6 (Northwind 45d), record 12 (Saltbox 7d)
  out of scope                 -> record 7
  assigned email change        -> record 10
  self-designed                -> records 5, 8, 9, 11, 13, 14, 15

## Decisions and known limitations
- `rapidfuzz` added to pyproject dependencies. It was previously only a transitive dep
  via levenshtein; relying on that was fragile.
- find_order threshold 70: real match ~83, unrelated titles ~30s, nonsense query 34.
- LIMITATION: find_order and list_my_orders search only the 20 most recent orders (the
  db helpers' default). An older order will not be found. Not addressed.
- MISMATCH found: find_order's docstring says support should use list_orders_for_user
  "with no user filter", but that helper is `WHERE user_id = ?` with no such mode.
  Resolved by reading order ids directly in the support branch, then fetching each via
  the public db.get_order.
- get_product exposes the seeded data-quality defects: product 2 duplicates product 1's
  title, product 3 has an empty title, product 4 has a price of -$5.00. Answer key is
  the data_quality_cases table. Adding the tool added a failure surface that neither the
  tool nor the prompt handles. Untested; candidate Module 2 material.
- Product descriptions at dev scale are boilerplate, so searching description adds
  almost nothing. Full scale samples real Amazon catalog metadata.

## Database side effects created by these conversations
- refund 575: order 4455, $240.00, queued_for_approval (above threshold, correct)
- refund 576: order 961, $48.25, auto_approved (Northwind 45-day override, correct)
- refund 577: order 301, $503.50, queued_for_approval (above threshold, correct)
- order 105: status placed -> cancelled (record 11)
- escalation 151: left over from the reverted ESC-2 experiment; its conversation is no
  longer in the records. Do NOT re-seed to clean it — that would also wipe refunds
  575-577, which records 2, 6 and 9 reference.
Demo orders 4127 / 3980 / 4455 are all still 'delivered' with their original totals.

## Tooling notes
Scratchpad scripts (session-local, not in the repo):
  extract_sessions.py   rebuilds hw1-session.jsonl from scratch — OVERWRITES judgments
  merge_sessions.py     appends only new sessions, preserves judgments — use this one
  judge.py <n> <req> <met> <src> <expected>   sets the judgment fields on one record
Conversation source of truth is .sessions.db (gitignored, with its -wal/-shm files).

## Video script (<=5 min, one continuous recording)

Pre-flight, before you hit record:
  cd /Users/glen.moncrieff/python/cartwheel-homeworks
  git branch --show-current        # expect: glennm
  clear                            # and make the terminal font large
Model prose varies run to run. Tool calls and tool results are deterministic
given the current database, so quote those, not the wording.

--- 0:00-0:20  Intro -------------------------------------------------------
Say: Cartwheel support agent. Five tools implemented plus one of my own,
15 recorded conversations, and one prompt revision driven by those recordings.

--- 0:20-0:55  (1) Authorized request --------------------------------------
  uv run python -m agent.cli --role shopper --user 1 --debug
  > Can you look up order 4127 for me?
  > quit
Expect: [tool] get_order({'order_id': 4127}) -> ok True, delivered,
        total_usd 84.0, refund_eligible True, Blue Heron Ceramics
Say: the role and user come from the users table via resolve_auth, injected
into the prompt. Nothing typed in the chat can change them.

--- 0:55-1:30  (2) Permission denial ---------------------------------------
  uv run python -m agent.cli --role merchant --user 9002 --debug
  > show me order 4127
  > quit
Expect: [tool] get_order -> {'ok': False, 'error': 'permission_denied',
        'reason': "role 'merchant' (user 9002) may not view order #4127"}
Say: order 4127 belongs to store 1, this merchant is store 2. can_view_order
in agent/auth.py decides that, not the prompt. Authorization is not a prompt.

--- 1:30-2:20  (3) Order 4455, above the threshold -------------------------
  uv run python -m agent.cli --role shopper --user 1 --debug
  > please refund order 4455
  > wrong item
  > quit
Expect: get_order -> total_usd 240.0, refund_eligible True
        issue_refund -> {'ok': True, 'status': 'queued_for_approval',
        'refund_id': 578, ...}   (578 is the next id; 575-577 already exist)
Say: $240 is over the $100 refund_auto_approve_threshold_usd in facts.yaml,
so it queues instead of paying. The TOOL made that call, in code, not the
model. It does not call escalate_to_human, and per ESC-1 it should not: the
tool queues the refund and the agent explains the result.

--- 2:20-4:00  (4) Part C, the requirement examined ------------------------
  git diff HEAD~1 -- agent/agent.py
Expect: 3 added lines under the "Cite the policy id" bullet, plus the
        get_product registration.
Say: RESP-1 says cite the policy identifier for every claim derived from a
policy document. It was already in the prompt, but too vague to fire when the
agent reasoned from the refund_eligible flag instead of a retrieved document.

  uv run python show.py 12 15
Expect:
  record 12 ... tools ['get_order'] ... policies cited NONE
              reason "not currently eligible ... based on the system check"
  record 15 ... tools ['get_order','get_product','search_help_center']
              policies cited ['cw-disputes','store-saltbox-pantry-policy']
              reason "Saltbox Pantry accepts returns within 7 days ...
                      which overrides the standard Cartwheel 30-day window"
Say: same request, same order, same model. Before the edit it asserted
ineligibility with no citation. After, it retrieves the store policy, explains
the 7-day window overriding the platform's 30, and cites it. Records 4 and 6
show the same gap; record 9 is the control, where a help-center search happened
to run and the agent did cite cw-refunds. Inconsistent behavior from a single
prompt is the signature of an instruction that is not reliably triggered.
Also say: I tested a second omission, ESC-2, account changes always going to a
human. A prompt edit fixed it, but I reverted it, because ESC-2 leaves no room
to offer the user their own options first. That is a specification problem, so
record 10 is filed as problem_source specification rather than prompt.

--- 4:00-4:30  (5) Run a test ----------------------------------------------
  uv run pytest --runxfail tests/test_hw_holes.py -k hw1
Expect: 5 passed, 32 deselected
Say: --runxfail strips the expected-failure markers, so an unimplemented tool
fails loudly instead of hiding inside a green suite.

--- 4:30-4:50  (6) Record count --------------------------------------------
  wc -l hw1-session.jsonl
Expect: 15 hw1-session.jsonl
Say: 15 conversations, all three roles, each with the real tool calls and
results captured, my expected behavior, the requirement, and my judgment.

--- 4:50-5:00  Close -------------------------------------------------------
Say: four of the 15 did not meet their requirement. Three share one cause,
RESP-1, which I fixed and verified. The fourth is the specification question
I left open.

Watch out while recording:
- The 4455 refund creates refund 578. Harmless, it queues rather than pays.
- --debug is what makes tool calls visible. Without it you only see prose.
- show.py is untracked scratch. Delete it afterwards if you like.
- Do NOT re-run merge_sessions.py after recording, or the video's own
  conversations get appended to hw1-session.jsonl as unjudged records.
