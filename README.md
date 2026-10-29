# fmp-guardian

Agent skills for agent-native codebases.

This repository bundles two independent skills:

- **`fmp-guardian`** — the Fractal Mirror Protocol (FMP), a semantic consistency
  protocol for agent-native codebases.
- **`seo-mentor`** — a battle-tested Google SEO toolkit for building and growing
  overseas AI tool sites and content sites.

Each skill lives under `skills/` and can be installed on its own.

## Bundled skills

| Skill | Purpose | Entry point |
| --- | --- | --- |
| `fmp-guardian` | Keep code facts, architecture semantics, agent context, and verification evidence pointed at the same repository reality. | `skills/fmp-guardian/SKILL.md` |
| `seo-mentor` | Plan, build, launch, and monetize overseas AI tool sites with Google SEO, programmatic SEO, and AdSense playbooks. | `skills/seo-mentor/SKILL.md` |

---

## fmp-guardian

Generic Fractal Mirror Protocol Skill for agent-native codebases.

FMP is a semantic consistency protocol. It keeps code facts, architecture
semantics, agent context, and verification evidence pointed at the same
repository reality.

This package is intentionally project-agnostic. It does not know your repository paths in advance. It discovers your project and generates local FMP rules under `.fmp/`.

## Positioning

FMP is not a graph tool, agent memory system, ADR manager, or documentation
generator. Those can be useful inputs, but they must not become competing
sources of truth.

The core invariant is narrow:

```text
P0 code path
  -> mirror matrix
  -> architecture semantic mirror
  -> semantic block or current waiver
  -> check/eval evidence
  -> strict gate
```

Borrowed capabilities should enter FMP as one of three roles:

- detector: finds possibly affected mirrors
- validator: checks mirror, ADR, AGENTS, snapshot, or evidence conformance
- router: tells an agent which low-noise context to read for a task

Do not add a new authoritative knowledge source unless it replaces an existing
one. Dependency graphs, memories, decision journals, and quality contracts should
feed the existing mirror/evidence chain instead.

## Install

### GitHub (skills CLI)

Install one skill at a time from GitHub:

```bash
# fmp-guardian
npx skills add https://github.com/AlixWang/fmp-guardian/tree/main/skills/fmp-guardian -a codex -y

# seo-mentor
npx skills add https://github.com/AlixWang/fmp-guardian/tree/main/skills/seo-mentor -a codex -y
```

### Local checkout

Install all bundled skills into a project:

```bash
./install.sh /path/to/project/.agents/skills
```

Install a single skill by name:

```bash
./install.sh /path/to/project/.agents/skills seo-mentor
```

After installing `fmp-guardian`, initialize FMP:

```bash
node .agents/skills/fmp-guardian/scripts/fmp-init.mjs
```

Optional: add commands to your root `package.json`:

```json
{
  "scripts": {
    "fmp:init": "node .agents/skills/fmp-guardian/scripts/fmp-init.mjs",
    "fmp:scan": "node .agents/skills/fmp-guardian/scripts/fmp-scan.mjs",
    "fmp:check": "node .agents/skills/fmp-guardian/scripts/fmp-check.mjs",
    "fmp:doctor": "node .agents/skills/fmp-guardian/scripts/fmp-doctor.mjs",
    "fmp:seed-l3": "node .agents/skills/fmp-guardian/scripts/fmp-seed-l3.mjs --write",
    "fmp:sync-plan": "node .agents/skills/fmp-guardian/scripts/fmp-sync-plan.mjs",
    "fmp:eval": "node .agents/skills/fmp-guardian/scripts/fmp-eval.mjs"
  }
}
```

For a local checkout, install the skill payload with the commands above.

## Repository layout

```text
README.md
package.json
install.sh
skills/
  fmp-guardian/
    SKILL.md
    scripts/
    templates/
    docs/
    heuristics/
    recipes/
  seo-mentor/
    SKILL.md
    scripts/
    references/
    templates/
test/
```

The root directory intentionally does not contain `SKILL.md`. Each installable
skill is a self-contained directory under `skills/`, so skill installers copy the
bundled resources with the skill instead of treating the repository root as a
single-file skill.

## What it creates

```text
AGENTS.md
CLAUDE.md                    # optional compatibility shim
.fmp/config.json
.fmp/mirror-matrix.yaml
.fmp/architecture-snapshot.json
.fmp/status.md
docs/architecture/overview.md
docs/architecture/modules/*.md   # only for detected boundaries
```

## Main ideas

- `AGENTS.md` is the primary low-noise agent entry.
- `.fmp/config.json` stores project-local FMP rules.
- `.fmp/mirror-matrix.yaml` maps code areas to semantic mirrors.
- `.fmp/architecture-snapshot.json` is a deterministic architecture fact baseline.
- Dependency edges and inferred matches are detector evidence, not a separate
  architecture authority.
- Architecture docs separate deterministic FMP blocks from nested agent-reviewed
  semantic blocks; human prose and reviewed semantics survive scanner refreshes.
- ADRs, if present, remain the decision source of truth; ADR-aware validators
  should bind findings back to affected mirrors and evidence.
- L3-Lite anchors are required only for `l3Lite.selectedFiles` when `requiredFor` is `["selected-p0"]`.
- Project scans ignore common tool and agent metadata directories such as `.agents`, `.claude`, `.codex`, `.cursor`, `.fmp`, `.kiro`, `.vscode`, and build/cache outputs.
- FMP checks help catch code/doc/eval drift.

## Extension model

FMP can grow by adding checkers, not by multiplying truth sources.

Good extensions:

- boundary validators that use dependency edges to flag cross-layer drift
- sync-plan detectors that find likely affected mirrors
- task routers that recommend the minimal docs an agent should read
- conformance reports for mirror, ADR, AGENTS, snapshot, and eval evidence

Avoid extensions that make `graph.db`, `memory/`, `decisions.jsonl`,
`contracts.yaml`, or `PLAN.md` authoritative FMP state. If a project already has
those files, treat them as inputs to existing mirrors, ADRs, or evidence gates.

## Commands

### Initialize

```bash
node .agents/skills/fmp-guardian/scripts/fmp-init.mjs
```

Useful flags:

```bash
--dry-run
--no-claude
--seed-l3
--write-module-agents
--upgrade
--refresh-map
```

Re-running initialization preserves existing configuration, mirror mappings, and
human-authored documentation. Use `--refresh-map` only when inferred mirror paths
should replace the current matrix. `--upgrade` adds v0.2 defaults without replacing
the matrix.

### Scan architecture facts

```bash
node .agents/skills/fmp-guardian/scripts/fmp-scan.mjs --write
node .agents/skills/fmp-guardian/scripts/fmp-scan.mjs --check
```

The generic scanner detects manifests, applications, packages, services, entrypoints,
docs, and checks. Node/TypeScript projects also receive import/export and
cross-boundary dependency analysis.

Initialization marks semantic sections as pending. The FMP agent must replace those
markers with evidence-backed system purpose, flows, ownership, interactions, and
constraints before strict checks pass.

### Diagnose

```bash
node .agents/skills/fmp-guardian/scripts/fmp-doctor.mjs
```

### Check

```bash
node .agents/skills/fmp-guardian/scripts/fmp-check.mjs
node .agents/skills/fmp-guardian/scripts/fmp-check.mjs --strict
FMP_BASE_REF=origin/main node .agents/skills/fmp-guardian/scripts/fmp-check.mjs --strict
```

For every changed P0 mirror, strict mode requires either a changed mapped
`FMP:SEMANTIC:*` block or a current `no-doc-impact` waiver. Refreshing
deterministic scanner facts alone does not satisfy semantic sync. CI must provide
`--base` or `FMP_BASE_REF`; the checker never guesses a CI comparison range. When
configured check/eval commands exist, strict mode also requires current passing
evidence from `fmp-eval --run`.

If `.fmp/config.json` or `.fmp/mirror-matrix.yaml` changes in the same branch,
strict mode evaluates changed P0 files against the union of base and current FMP
policy so a branch cannot weaken its own gate.

### Seed L3-Lite anchors

```bash
node .agents/skills/fmp-guardian/scripts/fmp-seed-l3.mjs
node .agents/skills/fmp-guardian/scripts/fmp-seed-l3.mjs --write
node .agents/skills/fmp-guardian/scripts/fmp-seed-l3.mjs --all-p0
```

By default this command only targets `.fmp/config.json` `l3Lite.selectedFiles`.
Use `--all-p0` only when broad file-header coverage is intentional.

### Generate sync plan

```bash
node .agents/skills/fmp-guardian/scripts/fmp-sync-plan.mjs "change writer agent tool permissions"
node .agents/skills/fmp-guardian/scripts/fmp-sync-plan.mjs --base origin/main --write-impact "internal refactor"
```

`--write-impact` writes `.fmp/impact.yaml` with the exact base commit and P0 content
fingerprint. Add a waiver only when mapped architecture or public behavior did not
change. Any subsequent P0 edit invalidates it.

### CI

Use `skills/fmp-guardian/templates/fmp-ci.yml.tpl` from this repository, or the
installed skill's `templates/fmp-ci.yml.tpl`, for GitHub Actions. In another CI
system, run the equivalent command with `FMP_BASE_REF` set to the pull request
base commit.

### Plan or run checks/evals

```bash
node .agents/skills/fmp-guardian/scripts/fmp-eval.mjs
node .agents/skills/fmp-guardian/scripts/fmp-eval.mjs --run
```

`--run` executes configured commands and writes `.fmp/check-evidence.json`, which
`fmp-check --strict` validates against the current base commit, changed-P0
fingerprint, and configured command fingerprint.

## seo-mentor

`seo-mentor` is a Google SEO toolkit for overseas (出海) AI tool sites and
content sites. It bundles SOPs, executable scripts, deep reference manuals, and
production-ready templates.

### Capabilities

- Niche and keyword discovery, with a quantified KD/ROI scoring script.
- Keyword dilution diagnosis: BM25 field-budget and exact-phrase scoring per page,
  intent-purity conflict detection, and an internal PageRank dilution simulator.
- 72-hour MVP launch, tool landing page architecture, and static/SSR deployment.
- New-site cold start, indexing, and backlink submission playbooks.
- Programmatic SEO matrix design with doorway/scaled-content risk controls.
- Google AdSense optimization for higher eCPM and Core Web Vitals safety.
- Google Search Central compliance auditing (titles, canonical, H1, hreflang,
  structured data, INP/CLS).

### Bundled resources

```text
skills/seo-mentor/
  SKILL.md
  scripts/
    lib/seo_text.py                # tokenizer, HTML extractor, BM25 helpers
    calculate_kd_roi.py            # keyword ROI scoring with a DR feasibility gate
    analyze_keyword_dilution.py    # per-page BM25 + phrase + intent-purity analysis
    simulate_link_equity.py        # internal PageRank dilution simulator
    generate_schema_jsonld.py      # FAQPage / WebApplication / HowTo JSON-LD
    generate_sitemap_robots.py     # safe robots.txt + sitemap.xml
    audit_google_compliance.py     # Google Search Central technical audit
    requirements.txt               # beautifulsoup4, only for the full HTML audit
  references/
    google_search_compliance_checklist.md
    free_directories_list.md
    pseo_matrix_playbook.md
    adsense_ecpm_maximizer.md
    geo_ai_search_crawler_matrix.md
    keyword_dilution_model.md
  templates/
    tool_landing_page.txt
    keyword_dilution_report.md
    robots.txt
    llms.txt
```

### Typical usage

```bash
python3 .agents/skills/seo-mentor/scripts/calculate_kd_roi.py -k "ai image upscaler" -v 1200 -d 5 -c 1.2 -a 8
python3 .agents/skills/seo-mentor/scripts/analyze_keyword_dilution.py -f output.html -k "ai image upscaler"
python3 .agents/skills/seo-mentor/scripts/simulate_link_equity.py -s site.json --compare-group en-core
python3 .agents/skills/seo-mentor/scripts/audit_google_compliance.py -f output.html -k "ai image upscaler"
```

The three analyzers use only the Python 3 standard library. The full HTML audit
needs `beautifulsoup4`: `python3 -m pip install -r scripts/requirements.txt`
(`--keyword-only` works without it).

See `skills/seo-mentor/SKILL.md` for the full SOP set and response format.

## Safety

The FMP initializer is conservative:

- It does not add L3 to every file.
- It stores selected L3 targets in `.fmp/config.json` under `l3Lite.selectedFiles`.
- It does not create nested AGENTS.md everywhere.
- It does not overwrite existing AGENTS.md unless it owns the generated block.
- It only replaces FMP-managed architecture document blocks.
- It marks missing mirrors as FMP debt instead of pretending they exist.
