export const meta = {
  name: 'upgrade-round',
  description: 'Run one upgrade round: each task is built by its owning agent in a worktree, then reviewed by the adversary until it ships',
  whenToUse: 'A batch of independent repo changes, each owned by content or tooling, that should each pass an adversary review before the lead merges them',
  phases: [
    { title: 'Build', detail: 'content or tooling agent, one worktree per task' },
    { title: 'Review', detail: 'adversary review, fix, re-review (at most 3 rounds)' },
  ],
}

// args: { base: "<branch to build on>", tasks: [{ id, owner: "content" | "tooling", prompt }] }
// The workflow never merges or pushes. It returns one entry per task with the
// worktree branch, the final verdict and any findings left open, so the lead can
// merge, rebuild the site once with scripts/build_all.py, and push.

const BUILD = {
  type: 'object',
  properties: {
    branch: { type: 'string', description: 'worktree branch name' },
    commits: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
    checks: { type: 'string', description: 'commands run and their results' },
    unverified: { type: 'string', description: 'anything not run or not checked' },
  },
  required: ['branch', 'commits', 'summary', 'checks'],
}

const REVIEW = {
  type: 'object',
  properties: {
    ship: { type: 'boolean' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          severity: { type: 'string', enum: ['high', 'medium', 'low', 'info'] },
          where: { type: 'string', description: 'file:line' },
          problem: { type: 'string' },
          fix: { type: 'string' },
        },
        required: ['severity', 'where', 'problem', 'fix'],
      },
    },
  },
  required: ['ship', 'findings'],
}

const base = (args && args.base) || 'main'
const tasks = (args && args.tasks) || []
if (!tasks.length) {
  log('No tasks given; pass args.tasks')
  return []
}

const RULES = `Start by running \`git merge --ff-only ${base}\` in your worktree and confirm it succeeded.
Follow CLAUDE.md and CONTRIBUTING.md. Commit by explicit path on your worktree branch. Do not push.
Do not edit CLAUDE.md or .claude/settings.json. Run the checks CONTRIBUTING lists for the files you touch.`

const blocking = r => r.findings.filter(f => f.severity === 'high' || f.severity === 'medium')

const results = await pipeline(
  tasks,
  t => agent(`${t.prompt}\n\n${RULES}`, {
    label: `build:${t.id}`, phase: 'Build', agentType: t.owner, isolation: 'worktree', schema: BUILD,
  }),
  async (build, t) => {
    if (!build) return { id: t.id, error: 'build agent returned nothing' }
    let review = null
    for (let round = 1; round <= 3; round++) {
      review = await agent(
        `Review branch ${build.branch} (commits ${build.commits.join(', ')}) in a fresh clone in a uniquely named scratch dir; do not edit the repo.
Task it implements: ${t.prompt}
Author's summary: ${build.summary}
Author's checks: ${build.checks}
Not verified by the author: ${build.unverified || 'nothing stated'}
Try to break it. Verify factual claims against primary sources. Run the repo checks and a deterministic build.
Set ship=true only if no high or medium finding remains.`,
        { label: `review:${t.id}:${round}`, phase: 'Review', agentType: 'adversary', schema: REVIEW })
      if (!review || review.ship || !blocking(review).length) break
      if (round === 3) break
      log(`${t.id}: round ${round} found ${blocking(review).length} blocking issue(s); fixing`)
      const fixed = await agent(
        `Fix these review findings on your branch ${build.branch}. Findings:\n${JSON.stringify(review.findings, null, 2)}\n\n${RULES}`,
        { label: `fix:${t.id}:${round}`, phase: 'Review', agentType: t.owner, schema: BUILD })
      if (fixed) build = { ...fixed, branch: build.branch, commits: build.commits.concat(fixed.commits) }
    }
    return {
      id: t.id, branch: build.branch, commits: build.commits,
      ship: !!(review && (review.ship || !blocking(review).length)),
      open: review ? review.findings : [], unverified: build.unverified || '',
    }
  },
)

const out = results.filter(Boolean)
const held = out.filter(r => !r.ship).map(r => r.id)
if (held.length) log(`Not ready after 3 review rounds: ${held.join(', ')}`)
return out
