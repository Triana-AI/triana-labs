# MORNING CHECKLIST — agentagon demo

Everything buildable overnight is done on branch `demo/agentagon-gate` (agentagon-demo).
Below: how to record, then the auth-gated steps only you can do.

## 1. Record the demo (local, zero setup) — READY NOW
```
cd /Users/akarshgajbhiye/agentagon-demo
git checkout demo/agentagon-gate
npm install      # if not already
npm run dev
```
Open http://localhost:3000 → click the **"PR Demo"** nav tab → in the PR comment box type
**`/agentagon run`** and submit (or click the quick-run button).
You'll see: your comment ("run #1") → ~3.5s "running in GitHub Actions…" stream → a bot comment
with the **real ASCII report** and a red **❌ BLOCK** verdict (agent_looping regressed 21%→62%) →
**"View full release diff →"** → `/release/codefix` with all 13 real measurements, agent_looping
flagged as the reason for the block. Re-type `/agentagon run` to replay ("run #2").
- Second selector tab **"fix: agent looping"** = the GREEN story. Shows real numbers IF the
  post-fix corpus landed (see §3); otherwise a clean "awaiting corpus" placeholder (no fake numbers).

## 2. Push the GitHub Action to hr_agent (the "real CI" artifact) — NEEDS YOUR PUSH
Staged in `handoff/hr_agent/`. Read `handoff/hr_agent/README.md` — summary:
1. Copy `handoff/hr_agent/*` into your hr_agent repo (a new branch, e.g. `demo/agentagon-gate`).
2. Run `vendor/sync_agentagon.sh` (points at your local agentagon checkout) → vendors agentagon in.
3. Copy the frozen inputs (`FROZEN_SET.json`, `exploration.json`, `frozen_labels.json` from
   agentagon's `experiments/hr_ai_seed/out/`) into `frozen/`, and the demo traces into `traces/`.
4. Swap `<AGENTAGON_RELEASE_DIFF_URL>` in the workflow for your UI URL.
5. Push, open a PR, comment `/agentagon run`. No secrets needed (frozen labels = no Bedrock).

## 3. GREEN panel — status depends on HR AI's overnight run
- If `data/gate/fix.json` exists on this branch → I ran the gate on HR AI's post-fix corpus; the
  GREEN panel shows real before/after. Done.
- If it's absent → HR AI's looping-fix run didn't finish / land in a shape I could consume. The
  BLOCK demo still fully works. See the DEMO_TODO.md status log for exactly where it stalled.

## 4. Optional — host the UI (not needed for local recording)
`npm run build` produces a static-exportable app. Deploy to Vercel (`vercel`) or push `out/` to
GitHub Pages if you want a shareable URL instead of localhost.
