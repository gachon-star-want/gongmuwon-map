import { Pool, type QueryResultRow } from 'pg';

let readPool: Pool | undefined;
let writePool: Pool | undefined;

function connectionString(kind: 'read' | 'write') {
  if (kind === 'read') {
    return process.env.DATABASE_URL_READONLY || process.env.DATABASE_URL;
  }
  return process.env.DATABASE_URL;
}

export function pool(kind: 'read' | 'write' = 'read') {
  const url = connectionString(kind);
  if (!url) {
    throw new Error(kind === 'read' ? 'DATABASE_URL_READONLY is not configured' : 'DATABASE_URL is not configured');
  }
  if (kind === 'read') {
    readPool ??= new Pool({ connectionString: url, max: 3 });
    return readPool;
  }
  writePool ??= new Pool({ connectionString: url, max: 2 });
  return writePool;
}

export async function query<T extends QueryResultRow>(
  text: string,
  values: unknown[] = [],
  kind: 'read' | 'write' = 'read',
) {
  return pool(kind).query<T>(text, values);
}
