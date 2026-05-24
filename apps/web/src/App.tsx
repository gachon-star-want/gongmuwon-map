import { AppShell, Badge, Group, Stack, Text, Title } from '@mantine/core';
import { MapPin } from 'lucide-react';

export function App() {
  return (
    <AppShell header={{ height: 56 }} padding={0}>
      <AppShell.Header className="app-header">
        <Group h="100%" px="md" justify="space-between">
          <Group gap="xs">
            <MapPin size={20} aria-hidden />
            <Title order={1}>공무원맵</Title>
          </Group>
          <Badge variant="light">Phase 1 scaffold</Badge>
        </Group>
      </AppShell.Header>
      <AppShell.Main>
        <Stack className="placeholder-map" align="center" justify="center">
          <Title order={2}>서울시청 업무추진비 데이터 파이프라인 준비 중</Title>
          <Text c="dimmed">Phase 2에서 카카오맵, 필터, 디테일 패널을 연결합니다.</Text>
        </Stack>
      </AppShell.Main>
    </AppShell>
  );
}
