import { Pool, type QueryResultRow } from 'pg';

type PoolKind = 'read' | 'write';
type PoolFactory = (connectionString: string, max: number) => Pool;

let readPoolInstance: Pool | undefined;
let writePoolInstance: Pool | undefined;
let poolFactory: PoolFactory = (connectionString, max) => new Pool({ connectionString, max });

function readConnectionString() {
  return process.env.DATABASE_URL_READONLY;
}

function writeConnectionString() {
  return process.env.DATABASE_URL;
}

function requireUrl(url: string | undefined, name: string) {
  if (!url) {
    throw new Error(`${name} is not configured`);
  }
  return url;
}

export function readPool() {
  const url = requireUrl(readConnectionString(), 'DATABASE_URL_READONLY');
  if (!readPoolInstance) {
    readPoolInstance = poolFactory(url, 3);
  }
  return readPoolInstance;
}

export function writePool() {
  const url = requireUrl(writeConnectionString(), 'DATABASE_URL');
  if (!writePoolInstance) {
    writePoolInstance = poolFactory(url, 2);
  }
  return writePoolInstance;
}

export async function readQuery<T extends QueryResultRow>(text: string, values: unknown[] = []) {
  return readPool().query<T>(text, values);
}

export async function writeQuery<T extends QueryResultRow>(text: string, values: unknown[] = []) {
  return writePool().query<T>(text, values);
}

export async function query<T extends QueryResultRow>(
  text: string,
  values: unknown[] = [],
  kind: PoolKind = 'read',
) {
  return (kind === 'write' ? writeQuery<T>(text, values) : readQuery<T>(text, values));
}

export function _setPoolFactoryForTest(factory: PoolFactory) {
  poolFactory = factory;
  readPoolInstance = undefined;
  writePoolInstance = undefined;
}
