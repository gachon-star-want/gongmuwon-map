import { useEffect, useMemo, useState } from 'react';
import { Badge, Button, Card, Group, Loader, Progress, SegmentedControl, Select, Stack, Text, Title } from '@mantine/core';
import { PanelHeader } from '../../app/PanelHeader';
import {
  loadBoundaries,
  loadNeighborhoodDetail,
  loadRegionTree,
  loadSubregions,
  type BoundaryFeature,
  type NeighborhoodDetail,
  type RankItem,
  type SidoNode,
} from './neighborhoodApi';
import { NeighborhoodMap } from './NeighborhoodMap';

const HOUSEHOLD_OPTIONS = [
  { value: '1', label: '1인' },
  { value: '2', label: '2인' },
  { value: '3', label: '3인' },
  { value: '4', label: '4인+' },
];

const CATEGORY_LABEL: Record<string, string> = {
  convenience: '생활편의',
  safety: '안전',
  housing: '주택',
  education: '교육·보육',
  vitality: '인구·활력',
  environment: '자연·환경',
  welfare: '복지·문화',
  demographics: '인구구성',
};

const CATEGORY_STRENGTH: Record<string, string> = {
  convenience: '생활편의·일자리가 가깝고 풍부해요',
  education: '보육·교육 인프라 접근이 좋아요',
  vitality: '젊고 활기 있는 인구 구성이에요',
  welfare: '의료·문화 시설이 가까워요',
  safety: '치안 여건이 상대적으로 좋아요',
  housing: '주거 환경이 상대적으로 양호해요',
  environment: '자연·환경 여건이 좋아요',
};

export function NeighborhoodPage() {
  const [tree, setTree] = useState<SidoNode[]>([]);
  const [sido, setSido] = useState<string | null>(null);
  const [sigungu, setSigungu] = useState<string | null>(null);
  const [household, setHousehold] = useState('1');
  const [items, setItems] = useState<RankItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<NeighborhoodDetail | null>(null);
  const [features, setFeatures] = useState<BoundaryFeature[]>([]);

  useEffect(() => {
    void loadRegionTree()
      .then((res) => setTree(res.items))
      .catch(() => setTree([]));
  }, []);

  const sigunguOptions = useMemo(() => {
    const node = tree.find((s) => s.adm_cd === sido);
    return node ? node.sigungu.map((s) => ({ value: s.adm_cd, label: s.name })) : [];
  }, [tree, sido]);

  const sigunguName = sigunguOptions.find((o) => o.value === sigungu)?.label;

  useEffect(() => {
    if (!sigungu) {
      setItems([]);
      return;
    }
    setLoading(true);
    setSelected(null);
    setDetail(null);
    void loadSubregions(sigungu, Number(household))
      .then((res) => setItems(res.items))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [sigungu, household]);

  useEffect(() => {
    if (!sigungu) {
      setFeatures([]);
      return;
    }
    void loadBoundaries(sigungu, Number(household))
      .then((res) => setFeatures(res.features))
      .catch(() => setFeatures([]));
  }, [sigungu, household]);

  useEffect(() => {
    if (!selected) {
      setDetail(null);
      return;
    }
    void loadNeighborhoodDetail(selected, Number(household))
      .then(setDetail)
      .catch(() => setDetail(null));
  }, [selected, household]);

  const maxScore = items.length ? Math.max(...items.map((i) => i.score)) : 100;
  const householdLabel = HOUSEHOLD_OPTIONS.find((h) => h.value === household)?.label;

  return (
    <>
      <PanelHeader activePage="neighborhood" />
      <div style={{ maxWidth: 980, margin: '0 auto', padding: '1rem' }}>
        <Title order={2}>살기 좋은 동네</Title>
        <Text size="md" fw={500} mt={6}>
          이 동네, 왜 살기 좋을까?
        </Text>
        <Text size="sm" c="dimmed" mt={4}>
          공개 통계(SGIS·KOSIS) 기반 거주 참고 지표입니다. 공무원 개인을 평가하지 않으며, 동네에 절대등급을 매기지 않고
          같은 시군구 안에서 상대 비교만 제공합니다.
        </Text>

        <Group mt="md" gap="sm" align="end" wrap="wrap">
          <Select
            label="시도"
            placeholder="선택"
            data={tree.map((s) => ({ value: s.adm_cd, label: s.name }))}
            value={sido}
            onChange={(v) => {
              setSido(v);
              setSigungu(null);
            }}
            searchable
            w={150}
          />
          <Select
            label="시군구"
            placeholder="선택"
            data={sigunguOptions}
            value={sigungu}
            onChange={setSigungu}
            searchable
            w={200}
            disabled={!sido}
          />
          <div>
            <Text size="sm" mb={4}>
              가구원수
            </Text>
            <SegmentedControl data={HOUSEHOLD_OPTIONS} value={household} onChange={setHousehold} />
          </div>
        </Group>

        {loading && <Loader mt="xl" />}
        {!loading && sigungu && items.length === 0 && (
          <Text mt="xl" c="dimmed">
            아직 이 시군구의 데이터가 없습니다. (적재 전이거나 집계 대기 중일 수 있습니다)
          </Text>
        )}

        {!loading && items.length > 0 && features.length > 0 && (
          <div style={{ marginTop: '1rem' }}>
            <NeighborhoodMap features={features} selected={selected} onSelect={setSelected} />
          </div>
        )}

        {!loading && items.length > 0 && (
          <Group mt="lg" align="flex-start" gap="lg" wrap="wrap">
            <Stack gap={6} style={{ flex: 1, minWidth: 320 }}>
              <Text fw={500}>
                {sigunguName} 읍면동 순위 · {householdLabel} 기준
              </Text>
              {items.map((it) => (
                <Card
                  key={it.adm_cd}
                  withBorder
                  padding="xs"
                  onClick={() => setSelected(it.adm_cd)}
                  style={{
                    cursor: 'pointer',
                    borderColor: selected === it.adm_cd ? 'var(--mantine-color-blue-5)' : undefined,
                  }}
                >
                  <Group justify="space-between" wrap="nowrap">
                    <Group gap={8} wrap="nowrap">
                      <Text fw={500} w={22} ta="right" c={it.rank <= 3 ? 'blue' : 'dimmed'}>
                        {it.rank}
                      </Text>
                      <Text>{it.name}</Text>
                    </Group>
                    <Group gap={10} wrap="nowrap">
                      {it.solo_household_ratio !== null && (
                        <Text size="xs" c="dimmed">
                          1인 {it.solo_household_ratio}%
                        </Text>
                      )}
                      <Text fw={500} size="sm">상위 {Math.round((it.rank / it.total) * 100)}%</Text>
                    </Group>
                  </Group>
                  <Progress value={(it.score / maxScore) * 100} mt={6} size="sm" />
                </Card>
              ))}
            </Stack>

            {detail && (() => {
              const topPct = detail.score ? Math.round((detail.score.rank / detail.score.total) * 100) : null;
              const strengths = detail.fields
                .filter((f) => f.rank <= Math.ceil(f.total / 3))
                .sort((a, b) => a.rank - b.rank);
              const weaknesses = detail.fields
                .filter((f) => f.rank >= Math.ceil((f.total * 2) / 3))
                .sort((a, b) => b.rank - a.rank);
              const strengthNames = strengths.slice(0, 2).map((s) => CATEGORY_LABEL[s.category] ?? s.category);
              const summary = strengthNames.length
                ? `같은 ${sigunguName} 안에서 ${strengthNames.join('·')}이(가) 돋보이는 동네예요.`
                : '같은 시군구 안에서 고르게 평균적인 동네예요.';
              return (
              <Card withBorder w={320} style={{ flexShrink: 0 }}>
                <Group justify="space-between" align="center" wrap="nowrap">
                  <Title order={4}>{detail.region.name}</Title>
                  {topPct !== null && (
                    <Badge color="teal" variant="light">상위 {topPct}%</Badge>
                  )}
                </Group>
                {detail.score && (
                  <Text size="xs" c="dimmed" mt={2}>
                    {sigunguName} {detail.score.total}개 동 중 {detail.score.rank}위 · {householdLabel} 기준
                  </Text>
                )}

                <Text fw={500} mt="md">{summary}</Text>

                {strengths.length > 0 && (
                  <>
                    <Text size="sm" fw={500} mt="md" c="teal">강점</Text>
                    <Group gap={6} mt={4}>
                      {strengths.map((s) => (
                        <Badge key={s.category} color="teal" variant="light">
                          {CATEGORY_LABEL[s.category] ?? s.category} 상위 {Math.round((s.rank / s.total) * 100)}%
                        </Badge>
                      ))}
                    </Group>
                    <Stack gap={2} mt={6}>
                      {strengths.slice(0, 2).map((s) => (
                        <Text key={s.category} size="xs" c="dimmed">
                          · {CATEGORY_STRENGTH[s.category] ?? `${CATEGORY_LABEL[s.category] ?? s.category}이(가) 좋아요`}
                        </Text>
                      ))}
                    </Stack>
                  </>
                )}

                {weaknesses.length > 0 && (
                  <>
                    <Text size="sm" fw={500} mt="md" c="dimmed">아쉬운 점</Text>
                    <Group gap={6} mt={4}>
                      {weaknesses.map((w) => (
                        <Badge key={w.category} color="gray" variant="light">{CATEGORY_LABEL[w.category] ?? w.category}</Badge>
                      ))}
                    </Group>
                  </>
                )}

                {detail.household_distribution.length > 0 && (
                  <>
                    <Text fw={500} mt="md" size="sm">
                      가구원수 분포
                    </Text>
                    <Group gap={6} mt={4}>
                      {detail.household_distribution.map((d) => (
                        <Badge key={d.size} variant="light" color="gray">
                          {d.size === 6 ? '6인+' : `${d.size}인`} {d.households.toLocaleString()}
                        </Badge>
                      ))}
                    </Group>
                  </>
                )}

                <Button
                  mt="md"
                  fullWidth
                  variant="light"
                  component="a"
                  href={`/?region=${encodeURIComponent(sigunguName ?? '')}`}
                >
                  이 동네 공무원픽 맛집 보기
                </Button>
                <Text size="xs" c="dimmed" mt={6}>
                  {detail.source_notice}
                </Text>
              </Card>
              );
            })()}
          </Group>
        )}
      </div>
    </>
  );
}
