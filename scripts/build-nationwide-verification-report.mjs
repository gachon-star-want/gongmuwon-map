#!/usr/bin/env node
import fs from 'node:fs';
import process from 'node:process';

function parseArgs(argv) {
  const args = {
    productionBaseline: null,
    stagingBaselineBefore: null,
    stagingBaselineAfter: null,
    sourceRegistry: null,
    dryRun: null,
    stagingLoad: null,
    targetedRuns: [],
    publicContract: 'missing',
    productionWriteApproved: false,
    failOnBlockers: false,
    runId: process.env.GITHUB_RUN_ID || null,
    runAttempt: process.env.GITHUB_RUN_ATTEMPT || null,
    commitSha: process.env.GITHUB_SHA || null,
    workflow: process.env.GITHUB_WORKFLOW || null,
    eventName: process.env.GITHUB_EVENT_NAME || null,
    actor: process.env.GITHUB_ACTOR || null,
    artifactName: process.env.NATIONWIDE_ARTIFACT_NAME || null,
    stagingBranch: process.env.NEON_BRANCH || process.env.NEON_BRANCH_NAME || null,
    output: null,
  };
  for (const arg of argv) {
    if (arg === '--help' || arg === '-h') {
      args.help = true;
    } else if (arg === '--production-write-approved') {
      args.productionWriteApproved = true;
    } else if (arg === '--fail-on-blockers') {
      args.failOnBlockers = true;
    } else if (arg.startsWith('--production-baseline=')) {
      args.productionBaseline = valueOf(arg);
    } else if (arg.startsWith('--staging-baseline-before=')) {
      args.stagingBaselineBefore = valueOf(arg);
    } else if (arg.startsWith('--staging-baseline-after=')) {
      args.stagingBaselineAfter = valueOf(arg);
    } else if (arg.startsWith('--source-registry=')) {
      args.sourceRegistry = valueOf(arg);
    } else if (arg.startsWith('--dry-run=')) {
      args.dryRun = valueOf(arg);
    } else if (arg.startsWith('--staging-load=')) {
      args.stagingLoad = valueOf(arg);
    } else if (arg.startsWith('--targeted-run=')) {
      args.targetedRuns.push(parseTargetedRun(valueOf(arg)));
    } else if (arg.startsWith('--public-contract=')) {
      args.publicContract = valueOf(arg);
      if (!['pass', 'fail', 'missing'].includes(args.publicContract)) {
        throw new Error('--public-contract must be pass, fail, or missing');
      }
    } else if (arg.startsWith('--run-id=')) {
      args.runId = valueOf(arg);
    } else if (arg.startsWith('--run-attempt=')) {
      args.runAttempt = valueOf(arg);
    } else if (arg.startsWith('--commit-sha=')) {
      args.commitSha = valueOf(arg);
    } else if (arg.startsWith('--workflow=')) {
      args.workflow = valueOf(arg);
    } else if (arg.startsWith('--event-name=')) {
      args.eventName = valueOf(arg);
    } else if (arg.startsWith('--actor=')) {
      args.actor = valueOf(arg);
    } else if (arg.startsWith('--artifact-name=')) {
      args.artifactName = valueOf(arg);
    } else if (arg.startsWith('--staging-branch=')) {
      args.stagingBranch = valueOf(arg);
    } else if (arg.startsWith('--output=')) {
      args.output = valueOf(arg);
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }
  return args;
}

function valueOf(arg) {
  return arg.slice(arg.indexOf('=') + 1);
}

function parseTargetedRun(value) {
  const separator = value.indexOf(':');
  if (separator <= 0) {
    throw new Error('--targeted-run must be label:path');
  }
  return {
    label: value.slice(0, separator),
    path: value.slice(separator + 1),
  };
}

function usage() {
  return `Usage: node scripts/build-nationwide-verification-report.mjs [options]

Builds a Markdown verification report from generated JSON artifacts.

Inputs:
  --production-baseline=path       JSON from report:db-baseline -- --target=readonly
  --staging-baseline-before=path   JSON from report:db-baseline -- --target=staging before migration/load
  --staging-baseline-after=path    JSON from report:db-baseline -- --target=staging after migration/load
  --source-registry=path           JSON from source-registry --summary-only
  --dry-run=path                   JSON from run-agencies --dry-run
  --staging-load=path              JSON from run-agencies --write-target staging
  --targeted-run=label:path        Optional targeted dry-run JSON. Repeatable
  --public-contract=pass|fail|missing
  --production-write-approved
  --run-id=value                   Workflow/run identifier for audit provenance
  --run-attempt=value              Workflow retry attempt for audit provenance
  --commit-sha=value               Commit SHA used to produce the artifacts
  --workflow=value                 Workflow name used to produce the artifacts
  --event-name=value               Trigger event name
  --actor=value                    Triggering actor
  --artifact-name=value            Uploaded artifact bundle name
  --staging-branch=value           Staging DB branch name or id
  --fail-on-blockers             Exit nonzero when required gates/thresholds are blocked
  --output=path                    Write Markdown to a file instead of stdout
`;
}

function readJson(path, label) {
  if (!path) {
    return null;
  }
  try {
    return JSON.parse(fs.readFileSync(path, 'utf8'));
  } catch (error) {
    throw new Error(`failed to read ${label} JSON at ${path}: ${error.message}`);
  }
}

function queryRows(report, name) {
  const query = report?.queries?.find((item) => item.name === name);
  if (!query?.ok) {
    return [];
  }
  return query.rows ?? [];
}

function tableCounts(report, queryName) {
  return Object.fromEntries(queryRows(report, queryName).map((row) => [row.rel, Number(row.count)]));
}

function firstRow(report, queryName) {
  return queryRows(report, queryName)[0] ?? {};
}

function sourceFileRows(report) {
  return queryRows(report, 'source_file_counts');
}

function sourceSummary(registry) {
  return registry?.summary ?? null;
}

function runSummary(run) {
  return run?.summary ?? null;
}

function baselineQueriesOk(report) {
  return Boolean(report?.queries?.length) && report.queries.every((query) => query.ok === true);
}

function runHasActivity(summary) {
  return Boolean(summary) && Number(summary.posts_seen) > 0 && Number(summary.success) > 0;
}

function stagingLoadHasRows(summary) {
  return (
    Boolean(summary) &&
    Number(summary.loaded_sources) > 0 &&
    Number(summary.loaded_places) > 0 &&
    Number(summary.loaded_visits) > 0
  );
}

function status(value) {
  return value ? '완료' : '미완료';
}

function verdict(value) {
  return value ? '통과' : '차단';
}

function count(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '-';
  }
  return Number(value).toLocaleString('en-US');
}

function pct(numerator, denominator) {
  if (!denominator) {
    return '-';
  }
  return `${((numerator / denominator) * 100).toFixed(1)}%`;
}

function baselineSection(title, report) {
  if (!report) {
    return `## ${title}\n\n입력 JSON 없음.\n`;
  }

  const tables = tableCounts(report, 'table_counts');
  const publicViews = tableCounts(report, 'public_view_counts');
  const dates = firstRow(report, 'date_windows');
  const places = firstRow(report, 'place_quality_counts');
  const visits = firstRow(report, 'visit_publicity_counts');
  const agencyDistribution = firstRow(report, 'agency_visit_distribution');

  return `## ${title}

| 항목 | 값 |
|---|---:|
| target | ${report.target ?? '-'} |
| agencies | ${count(tables.agencies)} |
| sources | ${count(tables.sources)} |
| places | ${count(tables.places)} |
| place_visits | ${count(tables.place_visits)} |
| agencies_public | ${count(publicViews.agencies_public)} |
| places_public | ${count(publicViews.places_public)} |
| place_visits_public | ${count(publicViews.place_visits_public)} |
| visit date range | ${dates.min_visit_date ?? '-'} ~ ${dates.max_visit_date ?? '-'} |
| distinct visit dates | ${count(dates.distinct_visit_dates)} |
| agencies with visits | ${count(agencyDistribution.agencies_with_visits)} |
| agencies without visits | ${count(agencyDistribution.agencies_without_visits)} |
| Kakao matched places | ${count(places.kakao_matched)} / ${count(places.total_places)} (${pct(places.kakao_matched, places.total_places)}) |
| coordinate places | ${count(places.with_coordinates)} / ${count(places.total_places)} (${pct(places.with_coordinates, places.total_places)}) |
| representative stored visits | ${count(visits.with_representative)} / ${count(visits.total_visits)} |
| avg extractor confidence | ${visits.avg_confidence == null ? '-' : Number(visits.avg_confidence).toFixed(2)} |
`;
}

function metadataSection(args) {
  const shortSha = args.commitSha ? String(args.commitSha).slice(0, 12) : '-';
  return `## 실행 메타데이터

| 항목 | 값 |
|---|---|
| generated_at | ${new Date().toISOString()} |
| workflow | ${args.workflow ?? '-'} |
| event | ${args.eventName ?? '-'} |
| run_id | ${args.runId ?? '-'} |
| run_attempt | ${args.runAttempt ?? '-'} |
| actor | ${args.actor ?? '-'} |
| commit_sha | ${shortSha} |
| artifact | ${args.artifactName ?? '-'} |
| staging_branch | ${args.stagingBranch ?? '-'} |
`;
}

function sourceFileSection(title, report) {
  const rows = sourceFileRows(report);
  if (!rows.length) {
    return `## ${title} Source Files\n\nsource_file_counts 입력 없음.\n`;
  }
  const lines = [
    `## ${title} Source Files`,
    '',
    '| file_kind | count | missing_storage_path | min_published | max_published |',
    '|---|---:|---:|---|---|',
    ...rows.map(
      (row) =>
        `| ${row.file_kind ?? '-'} | ${count(row.count)} | ${count(row.missing_storage_path)} | ${row.min_published ?? '-'} | ${row.max_published ?? '-'} |`,
    ),
    '',
  ];
  return `${lines.join('\n')}\n`;
}

function sourceRegistrySection(summary) {
  if (!summary) {
    return `## Source Registry\n\n입력 JSON 없음.\n`;
  }
  const groups = summary.priority_group_counts ?? {};
  const lines = [
    '## Source Registry',
    '',
    '| 그룹 | total | verified | pending | legal_hold | invalid |',
    '|---|---:|---:|---:|---:|---:|',
  ];
  for (const [group, row] of Object.entries(groups)) {
    lines.push(
      `| ${group} | ${count(row.total)} | ${count(row.verified_in_code)} | ${count(row.pending)} | ${count(row.legal_hold)} | ${count(row.invalid_source_pattern)} |`,
    );
  }
  lines.push(
    `| 합계 | ${count(summary.total)} | ${count(summary.verified_in_code)} | ${count(summary.pending)} | ${count(summary.legal_hold)} | ${count(summary.invalid_source_pattern)} |`,
    '',
  );
  return `${lines.join('\n')}\n`;
}

function runSection(title, summary) {
  if (!summary) {
    return `## ${title}\n\n입력 JSON 없음.\n`;
  }
  const failureReasons = summary.failure_reasons ?? {};
  const failureReasonLines = Object.entries(failureReasons).length
    ? [
        '',
        '| failure_reason | agencies |',
        '|---|---:|',
        ...Object.entries(failureReasons).map(([reason, agencies]) => `| ${reason} | ${count(agencies)} |`),
      ].join('\n')
    : '\n\nfailure_reason 집계 없음.';

  return `## ${title}

| 항목 | 값 |
|---|---:|
| ok | ${String(summary.ok)} |
| scope | ${summary.scope ?? '-'} |
| dry_run | ${String(summary.dry_run)} |
| write_target | ${summary.write_target ?? '-'} |
| concurrency | ${count(summary.concurrency)} |
| max_attempts | ${count(summary.max_attempts)} |
| agency_timeout_seconds | ${count(summary.agency_timeout_seconds)} |
| total | ${count(summary.total)} |
| success | ${count(summary.success)} |
| adapter_required | ${count(summary.adapter_required)} |
| unsupported | ${count(summary.unsupported)} |
| config_error | ${count(summary.config_error)} |
| failed | ${count(summary.failed)} |
| posts_seen | ${count(summary.posts_seen)} |
| posts_fetched | ${count(summary.posts_fetched)} |
| raw_parsed_rows | ${count(summary.raw_parsed_rows)} |
| parsed_rows | ${count(summary.parsed_rows)} |
| normalized_visits | ${count(summary.normalized_visits)} |
| places_seen | ${count(summary.places_seen)} |
| kakao_matched_places | ${count(summary.kakao_matched_places)} |
| loaded_sources | ${count(summary.loaded_sources)} |
| loaded_places | ${count(summary.loaded_places)} |
| loaded_visits | ${count(summary.loaded_visits)} |
| skipped_invalid_places | ${count(summary.skipped_invalid_places)} |

${failureReasonLines}
`;
}

function perAgencyFailureSection(title, run) {
  const results = Array.isArray(run?.results) ? run.results : [];
  if (!results.length) {
    return `## ${title} Agency Retry Evidence\n\nresults[] 입력 없음.\n`;
  }
  const failures = results
    .filter((item) => item.result !== 'success' && item.result !== 'adapter_required')
    .slice(0, 30);
  if (!failures.length) {
    return `## ${title} Agency Retry Evidence\n\n실패 기관 없음.\n`;
  }
  const lines = [
    `## ${title} Agency Retry Evidence`,
    '',
    '| agency | region | adapter | result | failure_reason | attempts | timeout_stage | last_error |',
    '|---|---|---|---|---|---:|---|---|',
  ];
  for (const item of failures) {
    const attempts = Array.isArray(item.attempts) ? item.attempts : [];
    const lastAttempt = attempts.at(-1) ?? {};
    const error = truncateCell(item.error ?? lastAttempt.error ?? '-', 140);
    lines.push(
      `| ${escapeCell(item.short_name ?? '-')} | ${escapeCell(item.parent_region ?? '-')} | ${escapeCell(item.adapter ?? '-')} | ${escapeCell(item.result ?? '-')} | ${escapeCell(item.failure_reason ?? '-')} | ${count(item.attempt_count ?? attempts.length)} | ${escapeCell(item.timeout_stage ?? '-')} | ${escapeCell(error)} |`,
    );
  }
  lines.push('');
  return `${lines.join('\n')}\n`;
}

function targetedRunSection(targetedRuns) {
  if (!targetedRuns.length) {
    return '';
  }
  const lines = [
    '## 표적 Dry Run 진단',
    '',
    '전국 dry-run이 차단된 상태에서 개별 수정 경로를 검증한 보조 증거다. production 주입 판정에는 전국/staging 게이트만 사용한다.',
    '',
    '| label | ok | result | failure_reason | timeout_stage | posts_fetched | raw_parsed_rows | parsed_rows | normalized_visits | places_seen | kakao_matched_places | note |',
    '|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|',
  ];
  for (const {label, run} of targetedRuns) {
    const summary = runSummary(run) ?? {};
    const first = Array.isArray(run?.results) ? run.results[0] ?? {} : {};
    lines.push(
      `| ${escapeCell(label)} | ${escapeCell(summary.ok ?? '-')} | ${escapeCell(first.result ?? '-')} | ${escapeCell(first.failure_reason ?? '-')} | ${escapeCell(first.timeout_stage ?? '-')} | ${count(summary.posts_fetched)} | ${count(summary.raw_parsed_rows)} | ${count(summary.parsed_rows)} | ${count(summary.normalized_visits)} | ${count(summary.places_seen)} | ${count(summary.kakao_matched_places)} | ${escapeCell(truncateCell(first.error ?? '-', 120))} |`,
    );
  }
  lines.push('');
  return `${lines.join('\n')}\n`;
}

function escapeCell(value) {
  return String(value).replaceAll('|', '\\|').replaceAll('\n', '<br>');
}

function truncateCell(value, maxLength) {
  const text = String(value);
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength - 1)}…`;
}

function gateSection(inputs, summaries) {
  const sourceRegistryIsValid = isSourceRegistryValid(summaries.registry);
  const gates = [
    ['production 기준선 read-only 리포트', Boolean(inputs.productionBaseline)],
    ['production 기준선 SQL 성공', baselineQueriesOk(inputs.productionBaseline)],
    ['source registry 전국 카운트', Boolean(summaries.registry)],
    ['source registry total/count validity', sourceRegistryIsValid],
    ['staging before baseline', Boolean(inputs.stagingBaselineBefore)],
    ['staging before baseline SQL 성공', baselineQueriesOk(inputs.stagingBaselineBefore)],
    ['staging after baseline', Boolean(inputs.stagingBaselineAfter)],
    ['staging after baseline SQL 성공', baselineQueriesOk(inputs.stagingBaselineAfter)],
    ['nationwide dry-run', Boolean(summaries.dryRun) && summaries.dryRun.ok === true],
    ['dry-run collection activity', runHasActivity(summaries.dryRun)],
    [
      'dry-run retry policy',
      Boolean(summaries.dryRun) && Number(summaries.dryRun.max_attempts) >= 5,
    ],
    ['staging load', Boolean(summaries.stagingLoad) && summaries.stagingLoad.ok === true],
    ['staging load row activity', stagingLoadHasRows(summaries.stagingLoad)],
    [
      'staging load retry policy',
      Boolean(summaries.stagingLoad) && Number(summaries.stagingLoad.max_attempts) >= 5,
    ],
    ['public route contract', inputs.publicContract === 'pass'],
    ['production write approval', inputs.productionWriteApproved],
  ];
  const ready = gates.every(([, ok]) => ok);
  const lines = [
    '## 실행 게이트',
    '',
    '| 게이트 | 상태 | 판정 |',
    '|---|---|---|',
    ...gates.map(([name, ok]) => `| ${name} | ${status(ok)} | ${verdict(ok)} |`),
    '',
    `서비스 주입 판정: ${ready ? 'production 주입 검토 가능' : 'production 주입 불가'}`,
    '',
  ];
  return lines.join('\n');
}

function isSourceRegistryValid(summary) {
  if (!summary) {
    return false;
  }
  const total = Number(summary.total);
  const verified = Number(summary.verified_in_code);
  const pending = Number(summary.pending);
  const legalHold = Number(summary.legal_hold);
  const invalid = Number(summary.invalid_source_pattern);
  const numbers = [total, verified, pending, legalHold, invalid];
  if (numbers.some((value) => Number.isNaN(value) || value < 0)) {
    return false;
  }
  return total === verified + pending + legalHold + invalid;
}

function evaluateBlockers(inputs, summaries) {
  const blockers = [];
  if (!inputs.productionBaseline) {
    blockers.push('missing production baseline JSON');
  } else if (!baselineQueriesOk(inputs.productionBaseline)) {
    blockers.push('production baseline SQL query failed');
  }
  if (!inputs.stagingBaselineBefore) {
    blockers.push('missing staging baseline before JSON');
  } else if (!baselineQueriesOk(inputs.stagingBaselineBefore)) {
    blockers.push('staging baseline before SQL query failed');
  }
  if (!inputs.stagingBaselineAfter) {
    blockers.push('missing staging baseline after JSON');
  } else if (!baselineQueriesOk(inputs.stagingBaselineAfter)) {
    blockers.push('staging baseline after SQL query failed');
  }
  if (!summaries.registry) {
    blockers.push('missing source registry JSON summary');
  } else if (!isSourceRegistryValid(summaries.registry)) {
    blockers.push('source registry total/count validity failed');
  }
  if (!inputs.dryRun) {
    blockers.push('missing dry-run JSON');
  } else {
    if (summaries.dryRun?.ok !== true) {
      blockers.push('dry-run summary ok=false');
    }
    if (!runHasActivity(summaries.dryRun)) {
      blockers.push('dry-run has no collection activity');
    }
    if (Number(summaries.dryRun?.max_attempts) < 5) {
      blockers.push('dry-run retry policy max_attempts<5');
    }
  }
  if (!inputs.stagingLoad) {
    blockers.push('missing staging-load JSON');
  } else {
    if (summaries.stagingLoad?.ok !== true) {
      blockers.push('staging-load summary ok=false');
    }
    if (!stagingLoadHasRows(summaries.stagingLoad)) {
      blockers.push('staging-load has no loaded rows');
    }
    if (Number(summaries.stagingLoad?.max_attempts) < 5) {
      blockers.push('staging-load retry policy max_attempts<5');
    }
  }
  if (inputs.publicContract !== 'pass') {
    blockers.push(`public-contract is ${inputs.publicContract}`);
  }
  if (!inputs.productionWriteApproved) {
    blockers.push('production-write approval missing');
  }
  return blockers;
}

function buildReport(args) {
  const inputs = {
    productionBaseline: readJson(args.productionBaseline, 'production baseline'),
    stagingBaselineBefore: readJson(args.stagingBaselineBefore, 'staging baseline before'),
    stagingBaselineAfter: readJson(args.stagingBaselineAfter, 'staging baseline after'),
    sourceRegistry: readJson(args.sourceRegistry, 'source registry'),
    dryRun: readJson(args.dryRun, 'dry-run'),
    stagingLoad: readJson(args.stagingLoad, 'staging load'),
    targetedRuns: args.targetedRuns.map((item) => ({
      label: item.label,
      run: readJson(item.path, `targeted run ${item.label}`),
    })),
    publicContract: args.publicContract,
    productionWriteApproved: args.productionWriteApproved,
  };
  const summaries = {
    registry: sourceSummary(inputs.sourceRegistry),
    dryRun: runSummary(inputs.dryRun),
    stagingLoad: runSummary(inputs.stagingLoad),
  };

  return `# 전국 수집 검증 리포트

주의: 이 리포트는 입력 JSON의 집계값만 사용하며 원문 행, 개인정보, 연결 문자열을 포함하지 않는다.

${metadataSection(args)}
${gateSection(inputs, summaries)}
${baselineSection('Production 기준선', inputs.productionBaseline)}
${sourceFileSection('Production 기준선', inputs.productionBaseline)}
${baselineSection('Staging 기준선 Before', inputs.stagingBaselineBefore)}
${sourceFileSection('Staging 기준선 Before', inputs.stagingBaselineBefore)}
${baselineSection('Staging 기준선 After', inputs.stagingBaselineAfter)}
${sourceFileSection('Staging 기준선 After', inputs.stagingBaselineAfter)}
${sourceRegistrySection(summaries.registry)}
${runSection('전국 Dry Run', summaries.dryRun)}
${perAgencyFailureSection('전국 Dry Run', inputs.dryRun)}
${targetedRunSection(inputs.targetedRuns)}
${runSection('Staging Load', summaries.stagingLoad)}
${perAgencyFailureSection('Staging Load', inputs.stagingLoad)}
## 다음 액션

- 차단 게이트가 남아 있으면 production write를 실행하지 않는다.
- staging load가 끝난 뒤 npm run check:public-contracts를 실행하고 --public-contract=pass로 리포트를 재생성한다.
- production write는 별도 승인 후 --write-target production --confirm-production-write --allow-production-write --production-gate-report <검증리포트>로만 실행한다.
`;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(usage());
    return;
  }
  const report = buildReport(args);
  const inputs = {
    productionBaseline: readJson(args.productionBaseline, 'production baseline'),
    stagingBaselineBefore: readJson(args.stagingBaselineBefore, 'staging baseline before'),
    stagingBaselineAfter: readJson(args.stagingBaselineAfter, 'staging baseline after'),
    sourceRegistry: readJson(args.sourceRegistry, 'source registry'),
    dryRun: readJson(args.dryRun, 'dry-run'),
    stagingLoad: readJson(args.stagingLoad, 'staging load'),
    publicContract: args.publicContract,
    productionWriteApproved: args.productionWriteApproved,
  };
  const summaries = {
    registry: sourceSummary(inputs.sourceRegistry),
    dryRun: runSummary(inputs.dryRun),
    stagingLoad: runSummary(inputs.stagingLoad),
  };
  const blockers = evaluateBlockers(inputs, summaries);
  if (args.output) {
    fs.writeFileSync(args.output, report, 'utf8');
  } else {
    console.log(report);
  }
  if (args.failOnBlockers && blockers.length > 0) {
    for (const blocker of blockers) {
      console.error(`[nationwide-verification] blocker: ${blocker}`);
    }
    process.exit(1);
  }
}

try {
  main();
} catch (error) {
  console.error(JSON.stringify({ error: error.message }));
  process.exit(1);
}
