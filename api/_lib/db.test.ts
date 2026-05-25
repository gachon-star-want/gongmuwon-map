import { beforeEach, describe, expect, it } from 'vitest';
import { _setPoolFactoryForTest, readQuery, writeQuery } from './db';

function factory(url: string, max: number) {
  return {
    async query() {
      return { rows: [{ url, max }] };
    },
  } as any;
}

describe('db helpers', () => {
  beforeEach(() => {
    _setPoolFactoryForTest(factory);
    delete process.env.DATABASE_URL_READONLY;
    delete process.env.DATABASE_URL;
  });

  it('read query throws when DATABASE_URL_READONLY is missing', async () => {
    process.env.DATABASE_URL = 'postgres://write';
    await expect(readQuery('SELECT 1')).rejects.toThrow('DATABASE_URL_READONLY is not configured');
  });

  it('read pool does not fall back to DATABASE_URL', async () => {
    process.env.DATABASE_URL_READONLY = '';
    process.env.DATABASE_URL = 'postgres://write';
    await expect(readQuery('SELECT 1')).rejects.toThrow('DATABASE_URL_READONLY is not configured');
  });

  it('write query throws when DATABASE_URL is missing', async () => {
    process.env.DATABASE_URL_READONLY = 'postgres://read';
    await expect(writeQuery('SELECT 1')).rejects.toThrow('DATABASE_URL is not configured');
  });

  it('readQuery uses read pool and writeQuery uses write pool', async () => {
    process.env.DATABASE_URL_READONLY = 'postgres://read';
    process.env.DATABASE_URL = 'postgres://write';
    const readResult = await readQuery('SELECT 1');
    const writeResult = await writeQuery('SELECT 1');

    expect(readResult.rows).toEqual([{ url: 'postgres://read', max: 3 }]);
    expect(writeResult.rows).toEqual([{ url: 'postgres://write', max: 2 }]);
  });
});
