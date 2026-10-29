import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { execFileSync, spawnSync } from 'node:child_process'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const scriptsDir = path.join(repoRoot, 'skills/seo-mentor/scripts')
const fixturesDir = path.join(repoRoot, 'test/fixtures/seo-mentor')

const hasPython = spawnSync('python3', ['-V']).status === 0
const hasBs4 = hasPython && spawnSync('python3', ['-c', 'import bs4']).status === 0

function run(script, args) {
  return execFileSync('python3', [path.join(scriptsDir, script), ...args], {
    cwd: repoRoot,
    encoding: 'utf8',
  })
}

function runJson(script, args) {
  return JSON.parse(run(script, [...args, '--json']))
}

function fixture(name) {
  return path.join(fixturesDir, name)
}

const KEYWORDS = ['free tts online', 'text to speech', 'mp3 voice generator']
const KEYWORD_ARGS = KEYWORDS.flatMap(keyword => ['-k', keyword])

function keyword(report, name) {
  const item = report.keywords.find(entry => entry.keyword === name)
  assert.ok(item, `keyword ${name} missing from report`)
  return item
}

function buildTopology(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'seo-mentor-topology-'))
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }))

  const pages = [{ url: '/', group: 'en-core' }]
  const core = [
    '/mp3-voice-generator',
    '/spanish-tts',
    '/tiktok-voice-generator',
    '/text-to-speech',
    '/voice-cloner',
    '/audiobook',
    '/podcast',
    '/youtube',
    '/pdf-to-audio',
    '/api',
  ]
  for (const url of core) pages.push({ url, group: 'en-core' })

  for (const locale of ['es', 'ko', 'it', 'pt', 'fr', 'de', 'ja', 'zh', 'ru', 'ar']) {
    for (let index = 0; index < 39; index += 1) {
      pages.push({
        url: index === 0 ? `/${locale}/` : `/${locale}/p${index}`,
        group: `locale-${locale}`,
      })
    }
  }
  for (let index = 0; index < 25; index += 1) {
    pages.push({ url: `/blog/post-${index}`, group: 'blog' })
  }

  const file = path.join(dir, 'site.json')
  fs.writeFileSync(file, JSON.stringify({ site: 'https://tts-free.online', pages }))
  return file
}

test('tokenizer keeps Hangul and kana intact after diacritic folding', { skip: !hasPython }, () => {
  const script = [
    "import json, sys",
    `sys.path.insert(0, ${JSON.stringify(scriptsDir)})`,
    "from lib.seo_text import tokenize, count_words",
    "print(json.dumps({",
    "  'tokens': tokenize('한국어 텍스트 카페 がく カフェ café'),",
    "  'cjk_words': count_words('한국어 텍스트'),",
    "  'latin_words': count_words('café résumé'),",
    "  'arabic_words': count_words('مرحبا بالعالم'),",
    "}))",
  ].join('\n')
  const out = JSON.parse(execFileSync('python3', ['-c', script], { encoding: 'utf8' }))
  assert.ok(out.tokens.includes('한국'), 'Hangul bigrams must survive normalization')
  assert.ok(out.tokens.includes('카페'), 'Hangul bigrams must survive normalization')
  assert.ok(out.tokens.includes('がく'), 'kana with dakuten must stay precomposed')
  assert.ok(out.tokens.includes('カフ'), 'katakana bigrams must survive normalization')
  assert.ok(out.tokens.includes('cafe'), 'Latin diacritics must fold')
  assert.equal(out.cjk_words, 6)
  assert.equal(out.latin_words, 2)
  assert.equal(out.arabic_words, 2)
})

test('extractor keeps only the first H1 when a page duplicates headings', { skip: !hasPython }, () => {
  const script = [
    "import json, sys",
    `sys.path.insert(0, ${JSON.stringify(scriptsDir)})`,
    "from lib.seo_text import extract_page",
    "page = extract_page('<html><body><h1>First</h1><h1>Second</h1></body></html>')",
    "print(json.dumps({'h1': page.h1, 'count': page.h1_count}))",
  ].join('\n')
  const out = JSON.parse(execFileSync('python3', ['-c', script], { encoding: 'utf8' }))
  assert.equal(out.h1, 'First')
  assert.equal(out.count, 2)
})

test('dilution analyzer separates the diluted page from the focused one', { skip: !hasPython }, () => {
  const before = runJson('analyze_keyword_dilution.py', ['-f', fixture('page-before.html'), ...KEYWORD_ARGS])
  const after = runJson('analyze_keyword_dilution.py', ['-f', fixture('page-after.html'), ...KEYWORD_ARGS])

  const beforePrimary = keyword(before, 'free tts online')
  const afterPrimary = keyword(after, 'free tts online')

  assert.equal(beforePrimary.fields.title.exact_phrase, false)
  assert.equal(afterPrimary.fields.title.exact_phrase, true)
  assert.equal(beforePrimary.verdict, 'DILUTED')
  assert.equal(afterPrimary.verdict, 'FOCUSED')
  assert.ok(
    afterPrimary.relevance > beforePrimary.relevance + 0.25,
    `expected a large relevance gap, got ${beforePrimary.relevance} -> ${afterPrimary.relevance}`,
  )
  assert.ok(afterPrimary.dilution_index < beforePrimary.dilution_index)
  assert.equal(before.params.idf_mode, 'uniform')
})

test('dilution analyzer flags multi-intent conflict only on the mixed page', { skip: !hasPython }, () => {
  const before = runJson('analyze_keyword_dilution.py', ['-f', fixture('page-before.html'), ...KEYWORD_ARGS])
  const after = runJson('analyze_keyword_dilution.py', ['-f', fixture('page-after.html'), ...KEYWORD_ARGS])

  assert.ok(before.conflicts.length > 0, 'mixed page should report a multi-intent conflict')
  assert.equal(before.conflicts[0].type, 'multi_intent')
  assert.equal(after.conflicts.length, 0, 'focused page should not report a conflict')

  const beforeIds = before.findings.map(item => item.id)
  assert.ok(beforeIds.includes('KWD-01'))
  assert.ok(beforeIds.includes('KWD-06'))

  const split = after.recommendations.find(item => item.action === 'split_page')
  assert.ok(split, 'focused page should push the off-intent keyword to a dedicated URL')
  assert.equal(split.suggested_path, '/mp3-voice-generator')
})

test('dilution analyzer calibrates avgdl and IDF from a competitor corpus', { skip: !hasPython }, t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'seo-mentor-corpus-'))
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }))
  const corpus = path.join(dir, 'titles.txt')
  fs.writeFileSync(corpus, 'free tts online\nfree text to speech\nonline tts converter\n')

  const report = runJson('analyze_keyword_dilution.py', [
    '-f', fixture('page-before.html'), '-k', 'free tts online', '--corpus', corpus,
  ])
  assert.equal(report.params.idf_mode, 'corpus')
  assert.ok(report.params.avgdl_title < 6, 'short competitor titles should lower avgdl')
  assert.equal(report.keywords[0].verdict, 'DILUTED')
})

test('dilution analyzer fails the gate when relevance is below the threshold', { skip: !hasPython }, () => {
  const result = spawnSync(
    'python3',
    [
      path.join(scriptsDir, 'analyze_keyword_dilution.py'),
      '-f',
      fixture('page-before.html'),
      '-k',
      'free tts online',
      '--fail-under',
      '0.6',
    ],
    { cwd: repoRoot, encoding: 'utf8' },
  )
  assert.equal(result.status, 1)
  assert.match(result.stderr, /relevance/)
})

test('link equity simulation quantifies page-count dilution', { skip: !hasPython }, t => {
  const siteFile = buildTopology(t)
  const report = runJson('simulate_link_equity.py', ['-s', siteFile, '--compare-group', 'en-core'])

  assert.equal(report.totals.pages, 426)
  assert.equal(report.totals.groups, 12)
  assert.equal(report.totals.oversubscribed, true)
  assert.equal(report.totals.prune_count, 226)
  assert.equal(report.comparison.pages_after, 11)
  assert.ok(
    report.comparison.focus_gain >= 30,
    `expected focus gain >= 30, got ${report.comparison.focus_gain}`,
  )
  assert.ok(report.comparison.avg_share_after_pct > report.comparison.avg_share_before_pct * 10)

  const actions = report.recommendations.map(item => item.action)
  assert.ok(actions.includes('prune_or_noindex'))
  assert.ok(actions.includes('noindex_group'))

  const second = runJson('simulate_link_equity.py', ['-s', siteFile, '--compare-group', 'en-core'])
  assert.deepEqual(second.totals, report.totals)
  assert.deepEqual(second.comparison, report.comparison)

  const custom = runJson('simulate_link_equity.py', ['-s', siteFile, '--core-group', 'locale-es'])
  assert.equal(custom.comparison.include_group, 'locale-es')
  const customNoindex = custom.recommendations.find(item => item.action === 'noindex_group')
  assert.match(customNoindex.detail, /387 页/)
})

test('link equity simulation rejects a malformed topology', { skip: !hasPython }, t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'seo-mentor-bad-'))
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }))
  const file = path.join(dir, 'site.json')
  fs.writeFileSync(file, JSON.stringify({ pages: [{ url: '/' }, { url: '/' }] }))

  const result = spawnSync(
    'python3',
    [path.join(scriptsDir, 'simulate_link_equity.py'), '-s', file],
    { cwd: repoRoot, encoding: 'utf8' },
  )
  assert.equal(result.status, 2)
  assert.match(result.stderr, /duplicate url/)
})

test('ROI gate rejects head terms that a low-DR site cannot reach', { skip: !hasPython }, () => {
  const head = runJson('calculate_kd_roi.py', [
    '-k', 'text to speech', '-v', '301000', '-d', '78', '-c', '2.5', '-a', '1.4',
  ])
  assert.equal(head.verdict, 'NO_GO')
  assert.equal(head.tag, 'OFF_TARGET')
  assert.equal(head.required_dr, 50)
  assert.equal(head.authority_gate, 'FAIL')
  assert.match(head.reason, /kd_ceiling/)

  const tail = runJson('calculate_kd_roi.py', [
    '-k', 'free tts online', '-v', '1900', '-d', '12', '-c', '0.8', '-a', '1.4',
  ])
  assert.equal(tail.verdict, 'GO')
  assert.equal(tail.tag, 'RECOMMENDED')
  assert.equal(tail.required_dr, 0)

  const unrated = runJson('calculate_kd_roi.py', [
    '-k', 'free tts online', '-v', '1900', '-d', '12', '-c', '0.8',
  ])
  assert.equal(unrated.authority_gate, 'UNRATED')
  assert.equal(unrated.verdict, 'GO')
})

test('audit applies the target keyword instead of ignoring -k', { skip: !hasPython }, () => {
  const before = runJson('audit_google_compliance.py', [
    '--keyword-only', '-f', fixture('page-before.html'), '-k', 'free tts online',
  ])
  const after = runJson('audit_google_compliance.py', [
    '--keyword-only', '-f', fixture('page-after.html'), '-k', 'free tts online',
  ])

  const beforeChecks = new Map(before.keyword_targeting.map(item => [item.id, item]))
  const afterChecks = new Map(after.keyword_targeting.map(item => [item.id, item]))

  assert.equal(beforeChecks.get('KWD-01').status, 'PASS')
  assert.equal(afterChecks.get('KWD-01').status, 'PASS')
  assert.equal(beforeChecks.get('KWD-02').status, 'WARN')
  assert.equal(afterChecks.get('KWD-02').status, 'PASS')
  assert.equal(beforeChecks.get('KWD-05').status, 'WARN')
})

test('full audit fails with an actionable message when bs4 is missing', { skip: !hasPython || hasBs4 }, () => {
  const result = spawnSync(
    'python3',
    [
      path.join(scriptsDir, 'audit_google_compliance.py'),
      '-f',
      fixture('page-before.html'),
      '-k',
      'free tts online',
    ],
    { cwd: repoRoot, encoding: 'utf8' },
  )
  assert.equal(result.status, 3)
  assert.match(result.stderr, /beautifulsoup4/)
  assert.match(result.stderr, /requirements\.txt/)
})
