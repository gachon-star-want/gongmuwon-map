import { useState } from 'react';
import { Button, Modal, PasswordInput, SegmentedControl, Stack, Text, TextInput } from '@mantine/core';
import { LogIn, UserPlus } from 'lucide-react';
import type { CurrentUser } from './authApi';
import { login, register } from './authApi';

type AuthModalProps = {
  opened: boolean;
  onClose: () => void;
  onAuthenticated: (user: CurrentUser) => void;
};

export function AuthModal({ opened, onClose, onAuthenticated }: AuthModalProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [handle, setHandle] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      const user = mode === 'login' ? await login(handle, password) : await register(handle, password);
      if (user) {
        onAuthenticated(user);
        setHandle('');
        setPassword('');
        onClose();
      }
    } catch (err) {
      const message = (err as Error).message;
      setError(
        message === 'handle_taken'
          ? '이미 사용 중인 닉네임입니다.'
          : message === 'invalid_credentials'
            ? '닉네임 또는 비밀번호가 맞지 않습니다.'
            : '처리하지 못했습니다.',
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal opened={opened} onClose={onClose} title="로그인" centered trapFocus>
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
        {error ? (
          <Text size="sm" c="red">
            {error}
          </Text>
        ) : null}
        <Button
          leftSection={mode === 'login' ? <LogIn size={16} /> : <UserPlus size={16} />}
          loading={submitting}
          disabled={!handle.trim() || password.length < 8}
          onClick={() => void submit()}
        >
          {mode === 'login' ? '로그인' : '회원가입'}
        </Button>
      </Stack>
    </Modal>
  );
}

