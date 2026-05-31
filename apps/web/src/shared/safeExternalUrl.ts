const DEFAULT_ALLOWED_PROTOCOLS = ['http:', 'https:'] as const;

export type SafeExternalUrlOptions = {
  allowedProtocols?: readonly string[];
  allowProtocolRelative?: boolean;
};

function normalizeProtocol(protocol: string): string {
  const lowered = protocol.trim().toLowerCase();
  return lowered.endsWith(':') ? lowered : `${lowered}:`;
}

export function safeExternalUrl(raw: string | null | undefined, options: SafeExternalUrlOptions = {}): string | null {
  const value = raw?.trim();
  if (!value) {
    return null;
  }

  const allowedProtocols = new Set((options.allowedProtocols ?? DEFAULT_ALLOWED_PROTOCOLS).map(normalizeProtocol));

  try {
    if (value.startsWith('//')) {
      if (!options.allowProtocolRelative) {
        return null;
      }
      const protocolRelativeUrl = new URL(`https:${value}`);
      return allowedProtocols.has(protocolRelativeUrl.protocol) ? protocolRelativeUrl.toString() : null;
    }

    const parsed = new URL(value);
    return allowedProtocols.has(parsed.protocol) ? parsed.toString() : null;
  } catch {
    return null;
  }
}
