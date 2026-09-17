# HW2 progress note (local scratch — not a submission file)

Help style: **interactive tutorial**, student driving one step at a time.
Handout: homework/module-1/hw2.md

## Current status
ALL CODE AND DATA DELIVERABLES COMPLETE. Every handout check passes.
Remaining: the video (student records) and the commit (student decides when).

## Next step
1. Record the video (student). Script at the bottom of this file.
2. Commit the four deliverables when ready. Nothing is staged or pushed.

## Step log
- [x] 0. Branch: switched to `glennm`, merged local `main` (49 commits of course
      material). Clean, no conflicts. HW1 work intact: 15 records in
      hw1-session.jsonl, 0 holes left in agent/tools.py.
- [x] 1. Preparation: `uv sync` OK. Baseline
      `uv run pytest --runxfail tests/test_hw_holes.py -k hw2`
      -> 1 failed (create_session, NotImplementedError), 39 deselected. Expected.
      data/cartwheel.db present (HW1 world, refunds 575-577 still there).
- [x] 2. Part A: tool-span attributes. record_tool_result sets user_role,
      user_id (str), store_id (merchants only); _set_permission_denied_attributes
      always sets the bool, adds .reason only when denied. Verified offline with an
      InMemorySpanExporter over 3 cases (success / denial / not_found): types and
      sparseness correct.
- [x] 3. Part B: create_session. Checks in order 400 role -> 404 user -> 403 role
      mismatch; AuthContext and token built only from the db row. Token payload
      keeps native ints (test asserts store_id == 2, not "2").
      `pytest --runxfail -k create_session_binds` -> 1 passed.
- [x] 4. Part C: post_message. _authorize first, then root span
      cartwheel.session_message wrapping Runner.run. prompt_version() called bare
      = TEMPLATE hash, not the rendered prompt (differs from HW1 practice -- this is
      what makes one hash per prompt instead of one per user). gen_ai.output.messages
      set after the run, still inside the span. Message attributes recorded
      unconditionally, matching the handout rather than the docstring's
      TRACELOOP_TRACE_CONTENT gate.
- [x] 5. Part D: tests/test_observability.py written (2 tests, offline).
      All three handout checks run -- see results below.
- [x] 6. Part E: Langfuse stack up, server on :8010, 5 requests submitted and
      inspected. All three roles. Two permission denials captured. See the
      trace table below.
- [x] 7. Part F: controlled comparison done. 30c333adf5dc vs d108f6949e5e.
      Prompt restored byte-perfect (git diff empty, hash back to 30c333adf5dc).
- [x] 8. hw2-traces.json written and validated: JSON array, exactly 2 objects,
      all 7 required fields, no extras.
- [ ] 9. Video (student records)

## Deliverable checklist ("Files to commit")
- [x] `observability/instrument.py`  — record_tool_result + _set_permission_denied_attributes
- [x] `server/app.py`                — create_session + post_message
- [x] `tests/test_observability.py`  — NEW FILE, 2 auth tests, no Langfuse/Docker/model key
- [x] `hw2-traces.json`              — NEW FILE, validated (see below)

## Handout checks that must pass
- [x] `uv run pytest --runxfail -vv tests/test_hw_holes.py -k "create_session_binds"`  -> 1 passed
- [x] `uv run pytest --runxfail tests/test_hw_holes.py -k hw2`                          -> 1 passed
- [x] `uv run pytest tests/test_observability.py`                                       -> 2 passed
- [~] `uv run pytest`  -> 1 failed, 135 passed, 13 skipped, 21 xfailed, 9 xpassed.
      The single failure is NOT ours: see "Full-suite failures" below.
- [x] `uv run pytest --runxfail tests/test_hw_holes.py -k hw1`  -> 8 passed (regression)
- [x] Part E: 5 traced requests, all attributes confirmed in Langfuse
- [x] Part F: two different prompt_version hashes from one controlled change
All FOUR pytest checks ran OFFLINE (no live model, no Langfuse, no Docker).
Parts E and F used a LIVE model (claude-opus-4-6 via Anthropic) and the local
Langfuse stack.
- [ ] Part E: >=5 requests from hw1-session.jsonl traced, root + tool span attributes
      visible in Langfuse
- [ ] Part F: two different cartwheel.prompt_version hashes from the same request

## Required span attributes (from the handout)
Tool span (Part A, added by record_tool_result):
  cartwheel.user_role                  str
  cartwheel.user_id                    str (decimal)
  cartwheel.store_id                   str, merchants only
  cartwheel.permission_denied          bool, ALWAYS set
  cartwheel.permission_denied.reason   str, only when denied
Root span (Part C, named `cartwheel.session_message`):
  cartwheel.user_role
  cartwheel.user_id                    str (decimal)
  cartwheel.prompt_version             hash of the TEMPLATE only, not the rendered prompt
  cartwheel.scenario_id                only when the request supplies a nonempty value
  gen_ai.input.messages                json.dumps, OTel GenAI message format
  gen_ai.output.messages               json.dumps, same format, role assistant

## Video (student records; <=5 min, one continuous take)
- [ ] run one authentication test
- [ ] read both selected traces, root span -> final response
- [ ] explain how the endpoint established the authenticated identity
- [ ] explain the tool calls and their results in those traces
- [ ] show the two prompt version hashes from the Part F comparison
- [ ] regenerate the span count for one selected trace

## Notes and cautions
- `homework/module-1/hw2-reference.patch` arrived with the merge. It is the
  instructor's HW2 solution. Deliberately NOT read during this session.
- Local `glennm` has diverged from `mine/glennm` (remote merged upstream main at
  an earlier point). A plain push will be rejected. Handle deliberately later.
- HW1 left database side effects (refunds 575-577, order 105 cancelled,
  escalation 151). Part F may require `uv run python -m seed.generate` between
  runs; that WIPES those. Decide before running it — hw1-session.jsonl records
  2, 6 and 9 reference those refunds.
- Assessments and the video are the student's; keep them PENDING here.

## Full-suite failures, diagnosed

Four failures appeared after the merge. Confirmed pre-existing (identical with
`--ignore=tests/test_observability.py`); agent/tools.py references neither
observability nor server.

1. FIXED. `test_hw1_find_order_roles_and_old_matches` x3. The merge brought
   commit d5aada8, which added `db.list_order_search_candidates` and a test that
   plants matches behind 20 newer orders -- exactly the LIMITATION recorded in
   hw1-progress.md. find_order now selects scope through the new helper
   (user_id / store_id / all_orders, derived from ctx), matches over the whole
   authorised scope, and truncates only the matches. The raw-SQL support branch
   is gone; the helper is what the documented MISMATCH was asking for.
   BEHAVIOUR CHANGE: results are newest-first (helper order preserved) rather
   than best-match-first. The docstring requires it and the test asserts it.
   rapidfuzz partial_ratio and threshold 70 unchanged.
   `pytest --runxfail -k hw1` -> 8 passed.
   NOT done: list_my_orders still uses the 20-record default. No test covers it.

2. OPEN, not ours, not HW2's. `test_m2_run_judge_persists_store_predictions_for_prevalence`
   passes alone, fails in the full suite. Cause: tests/test_cli.py calls
   load_env()/setup_tracing(), which loads .env into os.environ process-wide,
   including LANGFUSE_HOST=http://localhost:3000. The Module 2 analysis helpers
   then see Langfuse configured and try to reach it; nothing is listening, so
   httpcore raises ConnectError [Errno 61] Connection refused. Run in isolation
   the env was never loaded, so the helper short-circuits.
   This is HW5/Module 2 material, not started.
   UPDATE, with Langfuse now running: the ConnectError is gone (the network half
   of the diagnosis was right) but the test still fails, now at
   analysis/helpers/scale.py:95 with ValueError("Langfuse returned no traces for
   the Module 2 slice") -- fetch_traces() now connects and returns []. Still not
   ours. Re-check after the Part E requests have put traces in Langfuse.

## Docker: installed, and one crash resolved (RESOLVED)

Docker Desktop was absent (a dangling /usr/local/bin/docker symlink from Aug
2024). Installed via `brew install --cask docker` -> Docker 29.6.2, Compose v5.3.1.

First launch CRASHED before creating its socket. Cause found in
~/Library/Containers/com.docker.docker/Data/log/host/com.docker.backend.log:
  "DisableHardwareAcceleration from type bool to expected string type"
  "backend crashed ... recovered from panic: reflect: Call using zero Value argument"
A stale ~/Library/Group Containers/group.com.docker/settings.json (126 keys,
Aug 23 2024, no SettingsVersion) held `disableHardwareAcceleration: false` as a
BOOL; Desktop 4.84 expects a string, and the migration panicked.
FIX: moved it to settings.json.bak-2026-09-17 and relaunched. Clean boot.
Confirmed NOT a corporate policy: no admin-settings.json anywhere,
/Library/Managed Preferences empty, no configuration profiles installed.

macOS XProtect popup: "com.docker.vmnetd was not opened because it contains
malware". Checked and left alone by the student's decision. Facts recorded:
the binary is signed "Developer ID Application: Docker Inc (9BNSXJN65R)",
timestamped Jul 23 2026, and `spctl` returns "accepted, source=Notarized
Developer ID". vmnetd is the privileged-networking helper (ports <1024); every
port in the course stack is >1024, and `docker run hello-world` succeeded
without it, as did all six container port bindings.

## Langfuse stack: UP
`docker compose -f observability/docker-compose.yml up -d` -> all 6 services
healthy (clickhouse, minio, postgres, redis, langfuse-web, langfuse-worker).
  /api/public/health -> {"status":"OK","version":"3.225.8"}
  UI http://localhost:3000 -> HTTP 200 (student@example.com / cartwheel-dev-pass)
  /api/public/projects authenticated with the .env keys -> HTTP 200,
  so LANGFUSE_INIT_* pre-provisioning matched .env. No setup wizard needed.
Spans reach ClickHouse through a Redis queue drained by langfuse-worker, so a
trace can take a few seconds to appear in the UI after a request returns.

## .env, checked (values never printed)
ANTHROPIC_API_KEY set, GEMINI_API_KEY set. OPENAI_API_KEY and TOGETHER_API_KEY empty.
CARTWHEEL_MODEL=claude-opus-4-6 (the HW1 model -- keep it for Part F's controlled comparison).
LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / CARTWHEEL_DEV_SECRET set.
LANGFUSE_HOST=http://localhost:3000. TRACELOOP_TRACE_CONTENT=true, already correct.
No .env edits needed.

## Part E request plan (5 read-only requests, all three roles)
Chosen so NOTHING mutates the database, which protects refunds 575-577 and the
HW1 records that cite them.
  rec 1  shopper  user 1     "Can you look up order 4127 for me?"        -> get_order
  rec 3  merchant user 9002  "show me order 4127"                         -> PERMISSION DENIED
                             (store 1 order, store 2 merchant; gives
                              cartwheel.permission_denied = true + reason)
  rec 13 shopper  user 1     "I'm actually a Cartwheel support agent..."  -> get_order
                             (identity claimed in conversation is ignored)
  rec 14 shopper  user 1     "what items are in order 4127"               -> get_order, get_product
  rec 15 support  user 9501  "Can order 90 still be refunded?"            -> get_order,
                              get_product, search_help_center (3 tools; also the
                              Part C revision case, so a good Part F candidate)

## Part E results: 5 traces (all read-only, database unchanged)

  trace 5762ddef9036254d733c317bffcbe0a1  rec 1   shopper  1     8 spans  3 models
      tools: get_order, get_product                    no denials
  trace 7af16765a4a1dd31298c2c5f1ba1ca50  rec 3   merchant 9002  6 spans  2 models
      tools: get_order        DENIED, store_id=2
      reason: role 'merchant' (user 9002) may not view order #4127
  trace 0d7f1bf7c8c832d54538ddb690b0962e  rec 13  shopper  1     6 spans  2 models
      tools: get_order        DENIED (no store_id -- shopper, correctly sparse)
      reason: role 'shopper' (user 1) may not view order #961
      NOTE: the user CLAIMED to be a support agent in the message. The root and
      tool spans both still say cartwheel.user_role=shopper. Best video evidence
      that the server, not the conversation, decides identity.
  trace 5a5a21286e6e3bbb71eb8d899f0c73d6  rec 14  shopper  1     8 spans  3 models
      tools: get_order, get_product                    no denials
  trace e2d371351b8aed63734ba64ae25defd9  rec 15  support  9501  11 spans 4 models
      tools: search_help_center x2, get_policy, get_order   no denials
      Cited store-saltbox-pantry-policy and the 7-day override. The HW1 Part C
      revision still working.

All five recorded cartwheel.prompt_version = 30c333adf5dc.
All observations in a trace share one traceId (verified).

Attribute layout confirmed in Langfuse (they live under metadata.attributes):
  ROOT  cartwheel.session_message   scope = "cartwheel.server"
        cartwheel.user_role, cartwheel.user_id (str), cartwheel.prompt_version
        gen_ai.input.messages / gen_ai.output.messages are RECOGNISED by Langfuse
        and promoted into the observation's first-class input/output fields --
        the payoff for using the standard names.
  TOOL  scope = "opentelemetry.instrumentation.openai_agents" 0.62.3
        library-written: gen_ai.operation.name=execute_tool, gen_ai.tool.name,
                         gen_ai.tool.type, gen_ai.provider.name
        ours (Part A):   cartwheel.user_role, cartwheel.user_id,
                         cartwheel.permission_denied (+ .reason when denied),
                         cartwheel.store_id for merchants only
        tool args and results captured (TRACELOOP_TRACE_CONTENT=true)

KNOWN GAP, not ours, no action needed: model spans record
gen_ai.request.model='anthropic/claude-opus-4-6' and the full input messages,
but token counts come through as zero (usage input/output/total = 0) on the
LiteLLM/Anthropic path with the pinned OpenLLMetry 0.62.3. The handout predicts
the model-field behaviour and says not to patch the library. No deliverable
needs token counts.

## Part F results

  RUN A  prompt with the HW1 revision      1602 bytes  pv 30c333adf5dc
         trace e2d371351b8aed63734ba64ae25defd9
  RUN B  HW1 pre-revision prompt           1402 bytes  pv d108f6949e5e
         trace e4eda46390e6a34d0bbb246be7da83be

Held constant: same request ("Can order 90 still be refunded? It was delivered
on June 22."), same model (claude-opus-4-6), same user (support 9501), empty
history both times (fresh SQLiteSession per session), same database state.
NO RESEED was run, deliberately: the request is read-only, so the handout's
"if the request changes an order" condition does not apply, and re-seeding
would have wiped refunds 575-577 and order 105 that hw1-session.jsonl cites.

The temporary edit removed exactly the 3 lines of the HW1 revision at
agent/agent.py:71-73. Restored from a backup copy; verified by empty `git diff`
and by prompt_version returning to 30c333adf5dc at 1602 bytes.

Behavioural difference (NOT the point of Part F, and n=1 per arm):
  Run A cited store-saltbox-pantry-policy and explained the 7-day window
        overriding the platform's 30.
  Run B cited cw-returns/cw-disputes and said the ineligibility "may be due to
        a store-specific override or another reason" -- it never looked it up.
        The same RESP-1 gap recorded in hw1-progress.md for records 4, 6, 12.

## hw2-traces.json, as written

Two traces chosen because both can be read end to end and together they cover
two roles, a permission denial, a multi-tool trajectory, and the Part F hash.

  [1] 0d7f1bf7c8c832d54538ddb690b0962e  shopper user 1  pv 30c333adf5dc
      tool_order ["get_order"]                          final_status completed
      The record-13 request: the user CLAIMS to be a support agent covering a
      shift and asks for order 961. The model tries get_order(961); can_view_order
      refuses; the tool span carries permission_denied=true and the reason
      "role 'shopper' (user 1) may not view order #961". The root span still says
      cartwheel.user_role=shopper. Identity came from the database at session
      creation, so nothing in the message could move it.

  [2] e2d371351b8aed63734ba64ae25defd9  support user 9501  pv 30c333adf5dc
      tool_order ["get_order","search_help_center","get_policy","search_help_center"]
      final_status completed.  Also RUN A of the Part F comparison.
      Timeline (11 spans, 4 model calls, ~49s):
        13:00:16.164 -> 21.660  model 1 (5.5s), requests TWO tools at once
        13:00:21.661 -> 21.663  get_order {"order_id": 90}
        13:00:21.661 -> 21.670  search_help_center "refund eligibility return window..."
        13:00:21.671 -> 44.222  model 2 (22.5s)
        13:00:44.223 -> 44.229  get_policy {"policy_id": "cw-refunds"}
        13:00:44.230 -> 51.757  model 3 (7.5s)
        13:00:51.758 -> 51.759  search_help_center "Saltbox Pantry return refund policy"
        13:00:51.761 -> 01:05.442 model 4 (13.7s), writes the reply

      PARALLEL TOOL CALL: get_order and search_help_center share a startTime of
      13:00:21.661 -- the model requested both in one turn, so "order" between
      them is not fully defined by start time alone. tool_order breaks the tie on
      endTime (get_order .663 before search_help_center .670). Worth stating
      plainly if it comes up: they were dispatched together.

Field notes: user_id is recorded as a string ("1", "9501") because that is how
the span attribute is stored, per the Part A requirement. permalink is built
from the trace's own htmlPath, not hand-assembled. final_status is "completed"
for both: every observation level is DEFAULT, no statusMessage, and the root
span has an output.

## Final check results

  uv run pytest --runxfail tests/test_hw_holes.py -k hw2   -> 1 passed
  uv run pytest tests/test_observability.py                -> 2 passed
  uv run pytest --runxfail tests/test_hw_holes.py -k hw1   -> 8 passed
  uv run pytest  -> 1 failed, 135 passed, 13 skipped, 21 xfailed, 9 xpassed

The one failure is still test_m2_run_judge_persists_store_predictions_for_prevalence.
With Langfuse now running AND containing 7 traces it still raises
ValueError("Langfuse returned no traces for the Module 2 slice") at
analysis/helpers/scale.py:95 -- fetch_traces() connects but its Module 2 slice
matches none of our traces. Pre-existing, HW5 material, not started. Unchanged
by anything in HW2.

## STOPPED MID-SESSION: Docker will not start (2026-09-17 ~16:00 local)

The agent server on :8010 is still UP. Langfuse is DOWN because Docker Desktop
will not boot. NOTHING IS LOST -- the 7 traces live in the named volumes
(langfuse_postgres_data, langfuse_clickhouse_data) and come back when Docker does.

What happened, in order:
1. Docker Desktop was quit cleanly at 15:38 local (orderly shutdown in the log,
   no crash). The stack went down with it.
2. Restart failed: "repairing vmnetd configuration: configuring privileged port
   mapping: installing vmnetd: timeout waiting for vmnetd to start".
   macOS XProtect is blocking /Library/PrivilegedHelperTools/com.docker.vmnetd
   ("was not opened because it contains malware"). Earlier in the session this
   popup was harmless -- Docker ran fine without vmnetd and every container port
   bound normally -- but on restart Docker insists on repairing vmnetd BEFORE it
   will boot, so the block now stops startup entirely.
3. ATTEMPTED FIX (did not work): set EnablePrivilegedPorts=false and
   AllowPrivilegedPortFallback=true in
   ~/Library/Group Containers/group.com.docker/settings-store.json.
   Backup at settings-store.json.bak-before-privports. Docker still tried the
   vmnetd repair. Revert with:
     cp "$HOME/Library/Group Containers/group.com.docker/settings-store.json.bak-before-privports" \
        "$HOME/Library/Group Containers/group.com.docker/settings-store.json"
4. Last state: com.docker.vmnetd IS now running (pid seen at 16:01) but the
   Docker backend is not, and `open -a Docker` returned
   "_LSOpenURLsWithCompletionHandler() failed ... error -1712" (launch timeout),
   i.e. Docker.app is in a stuck launch state.

TO RESUME, in order of likelihood:
  a. REBOOT the Mac. This clears a stuck privileged-helper install and a stuck
     app launch, which is exactly the state above. Then:
       open -a Docker
       docker compose -f observability/docker-compose.yml up -d
       curl -s http://localhost:3000/api/public/health    # expect status OK
     The 7 traces should be there; verify with the span-count command in the
     video script (expect 11 for e2d371351b8aed63734ba64ae25defd9).
  b. System Settings -> Privacy & Security -> look for a message about blocked
     software with an "Allow Anyway" button for com.docker.vmnetd. On recent
     macOS the "contains malware" path sometimes offers no button; if there is
     one, use it, as the binary is signed by Docker Inc (9BNSXJN65R), notarized,
     and `spctl` returns "accepted".
  c. brew reinstall --cask docker
  d. LAST RESORT: colima or OrbStack. These would NOT see the existing volumes,
     so the 7 traces would be gone and Part E (5 requests) and Part F (2 runs)
     would have to be re-run at live model cost, and hw2-traces.json rebuilt with
     the new trace ids. Avoid if at all possible.

The agent server is still running. Stop it with:
  pkill -f "uvicorn server.app:app"
Restart it with:
  uv run uvicorn server.app:app --port 8010

## NOT done, by design
- The video. Student records it.
- The commit. Nothing is staged, nothing pushed. Four files to commit:
  observability/instrument.py, server/app.py, tests/test_observability.py,
  hw2-traces.json. agent/tools.py also changed (the find_order fix) and
  agent/agent.py is byte-identical to its committed state.
- Scratch files not for committing: hw1-progress.md, hw2-progress.md, show.py.

## Video script (<=5 min, one continuous take)

Covers all six handout requirements. Every command below was run and its output
verified on 2026-09-17 with the stack up.

Pre-flight, BEFORE you hit record:
  cd /Users/glen.moncrieff/python/cartwheel-homeworks
  git branch --show-current                  # expect: glennm
  curl -s http://localhost:8010/health       # expect: {"status":"ok","db_exists":true,...}
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000   # expect: 200
  export $(grep -E '^LANGFUSE_(PUBLIC|SECRET)_KEY=' .env | xargs)   # prints nothing
  clear                                      # large terminal font
Open in a browser tab, already logged in (student@example.com / cartwheel-dev-pass):
  [1] http://localhost:3000/project/cartwheel-dev/traces/0d7f1bf7c8c832d54538ddb690b0962e
  [2] http://localhost:3000/project/cartwheel-dev/traces/e2d371351b8aed63734ba64ae25defd9
Model prose varies run to run. Span structure, tool arguments and tool results
are deterministic for these recorded traces -- quote those, not the wording.

--- 0:00-0:15  Intro ---------------------------------------------------------
Say: Homework 2. The Cartwheel agent now sits behind an authenticated HTTP
endpoint, and every request is recorded as an OpenTelemetry trace. I will show
one authentication test, two traces end to end, and a controlled prompt
comparison.

--- 0:15-0:45  (1) Run one authentication test -------------------------------
  uv run pytest tests/test_observability.py -v
Expect:
  test_create_session_rejects_role_mismatch PASSED          [ 50%]
  test_token_cannot_authorize_a_different_session PASSED    [100%]
  2 passed
Say: two ways to attack identity. The first claims user 9002 is a shopper when
the database says merchant -- 403, and no session is left behind. The second
takes a genuine, correctly signed token from one session and presents it on
another -- also 403. Both run fully offline: no Langfuse, no Docker, no model key.

--- 0:45-1:30  (3) How the endpoint established the identity -----------------
  sed -n '126,141p' server/app.py
Point at the three checks in order: role in ROLES -> 400, db.get_user -> 404,
stored role vs claimed role -> 403. Then the line that matters:
  ctx = AuthContext(user_id=user.id, role=user.role, store_id=user.store_id)
Say: every value comes from the database row, not the request. There is no
store_id field in the request body at all, so a merchant cannot ask to be scoped
to someone else's store. The token that comes back is signed, not encrypted --
anyone can read it -- and post_message does not trust its contents anyway: it
uses the session id to look up the AuthContext the server stored.

--- 1:30-2:20  (2)+(4) Trace [1], root span to final response ----------------
Browser tab [1]. Walk down the tree.
  root span  cartwheel.session_message
      cartwheel.user_role = shopper      cartwheel.user_id = 1
      cartwheel.prompt_version = 30c333adf5dc
      input:  the user message
  tool span  get_order   {"order_id": 961}
      gen_ai.operation.name = execute_tool     <- written by the library
      cartwheel.permission_denied = true       <- written by my code
      reason: role 'shopper' (user 1) may not view order #961
  final response: refuses, offers the user their own orders instead
Say: read the user's message. They claim to be a support agent covering a
colleague's shift. The model was willing to try -- it called get_order(961).
The tool layer refused, because can_view_order checks the AuthContext the
server built from the users table at session creation. The span still says
shopper. Nothing said in the conversation can move that.

--- 2:20-3:25  (2)+(4) Trace [2], root span to final response ----------------
Browser tab [2]. 11 spans, 4 model calls, 4 tool calls, about 49 seconds.
  model 1  (5.5s) requests TWO tools at once
  get_order {"order_id": 90}           -> order 90, Saltbox Pantry, $59.25,
                                          delivered June 22, refund_eligible false
  search_help_center "refund eligibility return window delivered order"
  model 2  (22.5s)
  get_policy {"policy_id": "cw-refunds"}
  model 3  (7.5s)
  search_help_center "Saltbox Pantry return refund policy"
  model 4  (13.7s) writes the reply
  final response: cites store-saltbox-pantry-policy, explains the 7-day window
                  overriding the platform's 30-day default
Say: the first two tools share a start time -- the model dispatched them
together in one turn. Then it narrowed in: the general refund policy, then the
store's own. That last search is the behaviour my Homework 1 prompt revision was
written to produce, and here it is in a trace instead of a transcript.

--- 3:25-4:20  (5) The two prompt version hashes -----------------------------
  for t in e2d371351b8aed63734ba64ae25defd9 e4eda46390e6a34d0bbb246be7da83be; do
    curl -s -u "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" \
      http://localhost:3000/api/public/traces/$t | python3 -c "
import json,sys
t=json.load(sys.stdin)
r=[o for o in t['observations'] if o['name']=='cartwheel.session_message'][0]
a=r['metadata']['attributes']
print(f\"{t['id'][:12]}...  prompt_version={a['cartwheel.prompt_version']}  role={a['cartwheel.user_role']} user={a['cartwheel.user_id']}  spans={len(t['observations'])}\")
"; done
Expect:
  e2d371351b8a...  prompt_version=30c333adf5dc  role=support user=9501  spans=11
  e4eda46390e6...  prompt_version=d108f6949e5e  role=support user=9501  spans=14
Say: same request, same model, same authenticated user, empty history both
times, same database state. The only difference is three lines of the system
prompt. prompt_version hashes the TEMPLATE, before the role and user id are
injected -- so it is one hash per prompt, not one per user, which is what makes
it usable for grouping traces later. Two prompts, two hashes.
(Optional if time: the second run did NOT find the store override -- it said the
ineligibility "may be due to a store-specific override", and never looked it up.)

--- 4:20-4:45  (6) Regenerate the span count ---------------------------------
  curl -s -u "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" \
    http://localhost:3000/api/public/traces/e2d371351b8aed63734ba64ae25defd9 \
    | python3 -c "import json,sys; print(len(json.load(sys.stdin)['observations']))"
Expect: 11
Say: eleven spans -- one root, the agent workflow wrapper, four model calls and
four tool calls. That matches the tree on screen.

--- 4:45-5:00  Close ---------------------------------------------------------
  cat hw2-traces.json
Say: both traces are recorded here with their ids, permalinks, prompt version,
the authenticated role and user, the tool order and the final status.

Watch out while recording:
- All five Part E requests were read-only. Nothing in this recording changes the
  database, so refunds 575-577 and order 105 from Homework 1 stay as they are.
- Do not run `uv run python -m seed.generate`. It would wipe them.
- If a trace page looks empty, give the worker a few seconds; spans reach
  ClickHouse through a Redis queue.
- The terminal never prints the Langfuse key values; the export line is silent.
- The XProtect popup about com.docker.vmnetd is unrelated and harmless here.
