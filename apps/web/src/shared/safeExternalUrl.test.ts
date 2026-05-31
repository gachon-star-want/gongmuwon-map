import { describe, expect, it } from 'vitest';
import { safeExternalUrl } from './safeExternalUrl';

describe('safeExternalUrl', () => {
  it('accepts https urls', () => {
    expect(safeExternalUrl('https://example.com/path?q=1')).toBe('https://example.com/path?q=1');
  });

  it('accepts http urls', () => {
    expect(safeExternalUrl('http://example.com/resource')).toBe('http://example.com/resource');
  });

  it('trims surrounding whitespace before parsing', () => {
    expect(safeExternalUrl('   https://example.com/path   ')).toBe('https://example.com/path');
  });

  it('rejects javascript urls', () => {
    expect(safeExternalUrl('javascript:alert(1)')).toBeNull();
  });

  it('rejects data urls', () => {
    expect(safeExternalUrl('data:text/html,<script>alert(1)</script>')).toBeNull();
  });

  it('rejects blank values', () => {
    expect(safeExternalUrl('   ')).toBeNull();
    expect(safeExternalUrl('')).toBeNull();
    expect(safeExternalUrl(null)).toBeNull();
    expect(safeExternalUrl(undefined)).toBeNull();
  });

  it('rejects malformed urls', () => {
    expect(safeExternalUrl('http://')).toBeNull();
    expect(safeExternalUrl('https://exa mple.com')).toBeNull();
  });

  it('rejects protocol-relative urls by default', () => {
    expect(safeExternalUrl('//example.com/path')).toBeNull();
  });

  it('supports protocol-relative urls only when explicitly enabled', () => {
    expect(safeExternalUrl('//example.com/path', { allowProtocolRelative: true })).toBe('https://example.com/path');
  });

  it('rejects relative urls', () => {
    expect(safeExternalUrl('/internal/path')).toBeNull();
    expect(safeExternalUrl('relative/path')).toBeNull();
  });
});
