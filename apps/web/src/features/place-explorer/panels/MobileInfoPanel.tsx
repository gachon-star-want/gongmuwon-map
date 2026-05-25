import { Button, Text } from '@mantine/core';
import { AlertTriangle, Code2, ShieldCheck } from 'lucide-react';

export function MobileInfoPanel() {
  return (
    <div className="mobile-panel">
      <div className="panel-label">정보</div>
      <Text size="sm" c="dimmed">
        공공누리 제1유형 · 출처: 서울특별시 정보소통광장 외
      </Text>
      <Text size="sm">등급은 방문 빈도와 부서 다양성 기반 통계 신호이며 맛·품질·비위 여부를 단정하지 않습니다.</Text>
      <Button component="a" href="/legal" variant="light" leftSection={<ShieldCheck size={16} />}>
        데이터 출처
      </Button>
      <Button component="a" href="/api" variant="light" leftSection={<Code2 size={16} />}>
        API 문서
      </Button>
      <Button component="a" href="/disclaimer" variant="subtle" leftSection={<AlertTriangle size={16} />}>
        면책조항
      </Button>
    </div>
  );
}
