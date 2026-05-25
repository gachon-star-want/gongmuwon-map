#!/usr/bin/env node
import fs from 'node:fs';

const CONTRACT_PATH = 'docs/public-route-contracts.json';
const OPENAPI_PATH = 'apps/web/public/openapi.json';
const LLM_TXT_PATH = 'apps/web/public/llms.txt';
const LLM_FULL_PATH = 'apps/web/public/llms-full.txt';

const errors = [];

function fail(message) {
  errors.push(message);
}

function isObject(value) {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function normalizeMethod(value) {
  return String(value).toUpperCase();
}

function routeKey(method, path) {
  return `${normalizeMethod(method)} ${path}`;
}

function loadJson(path) {
  const raw = fs.readFileSync(path, 'utf8');
  return JSON.parse(raw);
}

const contractRaw = loadJson(CONTRACT_PATH);
if (!isObject(contractRaw) || !Array.isArray(contractRaw.routes)) {
  fail(`Invalid contract file shape: expected { routes: [] } in ${CONTRACT_PATH}`);
}

const allowedStatuses = new Set(['implemented', 'planned', 'removed_from_public_docs']);
const allowedMethods = new Set(['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS', 'TRACE']);
const contractByKey = new Map();

if (isObject(contractRaw)) {
  for (const route of contractRaw.routes) {
    if (!isObject(route)) {
      fail(`Invalid route entry: expected object in ${CONTRACT_PATH}`);
      continue;
    }

    const path = route.path;
    const method = normalizeMethod(route.method ?? '');
    const status = route.status;
    const kind = route.kind;

    if (typeof path !== 'string' || !path.startsWith('/')) {
      fail(`Invalid route path: ${JSON.stringify(route.path)} in contract`);
      continue;
    }

    if (!allowedMethods.has(method)) {
      fail(`Invalid method ${JSON.stringify(route.method)} for ${path} in contract`);
      continue;
    }

    if (!allowedStatuses.has(status)) {
      fail(`Invalid status ${JSON.stringify(status)} for ${routeKey(method, path)}`);
      continue;
    }

    if (typeof kind !== 'string' || !kind.trim()) {
      fail(`Missing kind for ${routeKey(method, path)}`);
      continue;
    }

    for (const field of ['source_notice_required', 'documented_in_openapi', 'documented_in_llms']) {
      if (typeof route[field] !== 'boolean') {
        fail(`Missing or invalid ${field} for ${routeKey(method, path)}`);
      }
    }

    const key = routeKey(method, path);
    if (contractByKey.has(key)) {
      fail(`Duplicate contract route key: ${key}`);
      continue;
    }
    contractByKey.set(key, route);
  }
}

const openapi = loadJson(OPENAPI_PATH);
if (!isObject(openapi) || !isObject(openapi.paths)) {
  fail(`Invalid OpenAPI shape: expected paths object in ${OPENAPI_PATH}`);
}

const openapiMethods = new Set(['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']);
const documentedOpenapiKeys = new Set();

if (isObject(openapi) && isObject(openapi.paths)) {
  for (const [path, methods] of Object.entries(openapi.paths)) {
    if (!isObject(methods)) continue;
    for (const [method, pathDef] of Object.entries(methods)) {
      if (!openapiMethods.has(method)) continue;
      if (!isObject(pathDef)) continue;
      const key = routeKey(method, path);
      const contract = contractByKey.get(key);
      if (!contract) {
        fail(`OpenAPI exposes undocumented route: ${key}`);
        continue;
      }
      documentedOpenapiKeys.add(key);
      if (contract.status !== 'implemented') {
        fail(`OpenAPI documents non-implemented route: ${key} status=${contract.status}`);
      }
    }
  }
}

const llmContent = (() => {
  const txt = fs.readFileSync(LLM_TXT_PATH, 'utf8');
  const full = fs.readFileSync(LLM_FULL_PATH, 'utf8');
  return `${txt}\n${full}`;
})();

function includesRoutePath(path) {
  return llmContent.includes(path);
}

for (const [key, route] of contractByKey.entries()) {
  if (route.documented_in_openapi && !documentedOpenapiKeys.has(key)) {
    fail(`Registry marks route documented in OpenAPI but missing there: ${key}`);
  }

  if (route.status !== 'implemented' && (route.documented_in_openapi || route.documented_in_llms)) {
    fail(`Non-implemented route is documented as callable: ${key}`);
  }

  if (route.documented_in_llms) {
    if (!includesRoutePath(route.path)) {
      fail(`Registry marks route documented in llms but not found in llms docs: ${key}`);
    }
  }

  if (route.status === 'implemented' && route.kind === 'json' && route.source_notice_required && !includesRoutePath(route.path)) {
    fail(`Implemented JSON route with source_notice_required is missing from llms docs: ${key}`);
  }
}

if (!/공공누리 제1유형/.test(llmContent)) {
  fail('llms docs missing 공공누리 출처 표기 required by policy');
}

if (errors.length > 0) {
  console.error('[public-route-contracts] validation failed');
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exitCode = 1;
} else {
  console.log('[public-route-contracts] validation passed');
}
