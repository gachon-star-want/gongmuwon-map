import { useEffect, useRef, useState } from 'react';
import { Text } from '@mantine/core';
import './turnstile.css';

type TurnstileAction =
  | 'takedown_request'
  | 'closure_report'
  | 'auth_login'
  | 'auth_register'
  | 'community_post'
  | 'community_comment';

type TurnstileWidgetProps = {
  action: TurnstileAction;
  resetSignal: number | string;
  onTokenChange: (token: string | null) => void;
};

type TurnstileApi = {
  render: (
    container: HTMLElement,
    options: {
      sitekey: string;
      action: TurnstileAction;
      callback: (token: string) => void;
      'expired-callback': () => void;
      'error-callback': () => void;
    },
  ) => string;
  remove: (widgetId: string) => void;
  reset: (widgetId: string) => void;
};

declare global {
  interface Window {
    turnstile?: TurnstileApi;
  }
}

const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY?.trim() ?? '';
let turnstileScriptPromise: Promise<void> | null = null;

function loadTurnstileScript() {
  if (window.turnstile) {
    return Promise.resolve();
  }
  if (turnstileScriptPromise) {
    return turnstileScriptPromise;
  }

  document.querySelector<HTMLScriptElement>('script[data-turnstile-api="true"]')?.remove();
  turnstileScriptPromise = new Promise<void>((resolve, reject) => {
    const script = document.createElement('script');
    const rejectAndRemove = () => {
      script.remove();
      reject(new Error('turnstile_load_failed'));
    };
    script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';
    script.async = true;
    script.defer = true;
    script.dataset.turnstileApi = 'true';
    script.addEventListener(
      'load',
      () => {
        if (window.turnstile) {
          resolve();
          return;
        }
        rejectAndRemove();
      },
      { once: true },
    );
    script.addEventListener('error', rejectAndRemove, { once: true });
    document.head.append(script);
  }).catch((error) => {
    turnstileScriptPromise = null;
    throw error;
  });
  return turnstileScriptPromise;
}

export function TurnstileWidget({ action, resetSignal, onTokenChange }: TurnstileWidgetProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetIdRef = useRef<string | null>(null);
  const [status, setStatus] = useState<'loading' | 'ready' | 'missing' | 'error'>('loading');

  useEffect(() => {
    let cancelled = false;
    onTokenChange(null);

    if (!TURNSTILE_SITE_KEY) {
      setStatus('missing');
      return undefined;
    }

    setStatus('loading');
    void loadTurnstileScript()
      .then(() => {
        if (cancelled || !containerRef.current || !window.turnstile) return;
        widgetIdRef.current = window.turnstile.render(containerRef.current, {
          sitekey: TURNSTILE_SITE_KEY,
          action,
          callback: (token) => {
            setStatus('ready');
            onTokenChange(token);
          },
          'expired-callback': () => {
            onTokenChange(null);
            if (widgetIdRef.current) window.turnstile?.reset(widgetIdRef.current);
          },
          'error-callback': () => {
            onTokenChange(null);
            setStatus('error');
          },
        });
      })
      .catch(() => {
        if (!cancelled) setStatus('error');
      });

    return () => {
      cancelled = true;
      onTokenChange(null);
      if (widgetIdRef.current) {
        window.turnstile?.remove(widgetIdRef.current);
        widgetIdRef.current = null;
      }
    };
  }, [action, onTokenChange, resetSignal]);

  const message =
    status === 'missing'
      ? '보안 확인 설정이 필요합니다.'
      : status === 'error'
        ? '보안 확인을 다시 시도해주세요.'
        : '보안 확인을 완료해주세요.';

  return (
    <div className="turnstile-field">
      <div ref={containerRef} className="turnstile-widget" />
      {status !== 'ready' ? (
        <Text size="xs" c={status === 'missing' || status === 'error' ? 'red' : 'dimmed'}>
          {message}
        </Text>
      ) : null}
    </div>
  );
}
