import { useEffect, useState } from 'react';
import { Anchor, Button, Checkbox, Modal, PasswordInput, SegmentedControl, Stack, Text, TextInput } from '@mantine/core';
import { LogIn, UserPlus } from 'lucide-react';
import type { CurrentUser } from './authApi';
import { login, register } from './authApi';
import { TurnstileWidget } from '../../shared/TurnstileWidget';

type AuthModalProps = {
  opened: boolean;
  onClose: () => void;
  onAuthenticated: (user: CurrentUser) => void;
};

export function AuthModal({ opened, onClose, onAuthenticated }: AuthModalProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [handle, setHandle] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [turnstileReset, setTurnstileReset] = useState(0);

  useEffect(() => {
    setTurnstileToken(null);
    setTurnstileReset((value) => value + 1);
    setError(null);
    setPasswordConfirm('');
    setTermsAccepted(false);
  }, [mode, opened]);

  async function submit() {
    const trimmedHandle = handle.trim();
    if (mode === 'register') {
      if (trimmedHandle.length < 2 || trimmedHandle.length > 24) {
        setError('닉네임은 2~24자로 입력해주세요.');
        return;
      }
      if (password !== passwordConfirm) {
        setError('비밀번호 확인이 일치하지 않습니다.');
        return;
      }
      if (!termsAccepted) {
        setError('이용약관과 개인정보처리방침에 동의해주세요.');
        return;
      }
    }
    if (!turnstileToken) {
      setError('보안 확인을 완료해주세요.');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const user = mode === 'login' ? await login(handle, password, turnstileToken) : await register(handle, password, turnstileToken);
      if (user) {
        onAuthenticated(user);
        setHandle('');
        setPassword('');
        setPasswordConfirm('');
        setTermsAccepted(false);
        setTurnstileToken(null);
        onClose();
      }
    } catch (err) {
      const message = (err as Error).message;
      setError(
        message === 'handle_taken'
          ? '이미 사용 중인 닉네임입니다.'
          : message === 'invalid_credentials'
            ? '닉네임 또는 비밀번호가 맞지 않습니다.'
            : message.startsWith('turnstile_')
              ? '보안 확인을 다시 시도해주세요.'
            : '처리하지 못했습니다.',
      );
      setTurnstileToken(null);
      setTurnstileReset((value) => value + 1);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal opened={opened} onClose={onClose} title={mode === 'login' ? '로그인' : '회원가입'} centered trapFocus>
      <Stack>
        <SegmentedControl
          value={mode}
          onChange={(value) => {
            setMode(value as 'login' | 'register');
            setError(null);
          }}
          data={[
            { value: 'login', label: '로그인' },
            { value: 'register', label: '회원가입' },
          ]}
        />
        <TextInput
          label="닉네임"
          placeholder="2~24자"
          value={handle}
          onChange={(event) => setHandle(event.currentTarget.value)}
        />
        <PasswordInput
          label="비밀번호"
          placeholder="8자 이상"
          value={password}
          onChange={(event) => setPassword(event.currentTarget.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') void submit();
          }}
        />
        {mode === 'register' ? (
          <>
            <PasswordInput
              label="비밀번호 확인"
              placeholder="한 번 더 입력"
              value={passwordConfirm}
              onChange={(event) => {
                setPasswordConfirm(event.currentTarget.value);
                if (error) setError(null);
              }}
              onKeyDown={(event) => {
                if (event.key === 'Enter') void submit();
              }}
            />
            <Checkbox
              checked={termsAccepted}
              onChange={(event) => {
                setTermsAccepted(event.currentTarget.checked);
                if (error) setError(null);
              }}
              label={(
                <Text size="xs">
                  <Anchor size="xs" href="/terms" target="_blank" rel="noopener noreferrer">
                    이용약관
                  </Anchor>
                  {' 및 '}
                  <Anchor size="xs" href="/privacy" target="_blank" rel="noopener noreferrer">
                    개인정보처리방침
                  </Anchor>
                  에 동의합니다.
                </Text>
              )}
            />
          </>
        ) : null}
        {error ? (
          <Text size="sm" c="red">
            {error}
          </Text>
        ) : null}
        <TurnstileWidget
          action={mode === 'login' ? 'auth_login' : 'auth_register'}
          resetSignal={turnstileReset}
          onTokenChange={setTurnstileToken}
        />
        <Text size="xs" c="dimmed">
          닉네임/비밀번호는 게시글·댓글 작성과 좋아요/싫어요 반응 권한 확인용으로만 사용되며, 이메일·실명은 받지 않습니다. 지도 등급/방문 통계에는 반영되지 않습니다. 자세한 내용은{' '}
          <Anchor size="xs" href="/privacy">
            개인정보처리방침
          </Anchor>
          을 참고해 주세요.
        </Text>
        <Button
          leftSection={mode === 'login' ? <LogIn size={16} /> : <UserPlus size={16} />}
          loading={submitting}
          disabled={
            !handle.trim()
            || password.length < 8
            || !turnstileToken
            || (mode === 'register' && (password !== passwordConfirm || !termsAccepted))
          }
          onClick={() => void submit()}
        >
          {mode === 'login' ? '로그인' : '회원가입'}
        </Button>
      </Stack>
    </Modal>
  );
}
