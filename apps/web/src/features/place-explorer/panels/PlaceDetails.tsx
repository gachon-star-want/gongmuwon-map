import { ActionIcon, Badge, Button, Group, Text, Title } from '@mantine/core';
import {
  AlertTriangle,
  ExternalLink,
  FileText,
  Navigation,
  X,
} from 'lucide-react';
import type { Place, Visit } from '../types';
import { formatDate, gradeClass, gradeLabel } from '../format';
import { Metric } from './metric';
import { safeExternalUrl } from '../../../shared/safeExternalUrl';

type PlaceDetailsProps = {
  place: Place;
  visits: Visit[];
  onClose: () => void;
  onReport: () => void;
  onClosureReport: () => void;
};

function visitSummary(visit: Visit) {
  return [visit.department_name, visit.rank_label, visit.purpose].filter(Boolean).join(' · ');
}

function getFallbackImage(category: string | null) {
  const cat = (category ?? '').toLowerCase();
  if (cat.includes('카페') || cat.includes('커피') || cat.includes('제과') || cat.includes('디저트')) {
    return 'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=600&auto=format&fit=crop&q=80';
  }
  if (cat.includes('일식') || cat.includes('초밥') || cat.includes('회') || cat.includes('돈까스')) {
    return 'https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=600&auto=format&fit=crop&q=80';
  }
  if (cat.includes('고기') || cat.includes('갈비') || cat.includes('삼겹살') || cat.includes('곱창')) {
    return 'https://images.unsplash.com/photo-1544025162-d76694265947?w=600&auto=format&fit=crop&q=80';
  }
  if (cat.includes('중식') || cat.includes('짜장') || cat.includes('짬뽕')) {
    return 'https://images.unsplash.com/photo-1563245372-f21724e3856d?w=600&auto=format&fit=crop&q=80';
  }
  return 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=600&auto=format&fit=crop&q=80';
}

export function PlaceDetails({
  place,
  visits,
  onClose,
  onReport,
  onClosureReport,
}: PlaceDetailsProps) {
  const kakaoUrl = `https://map.kakao.com/link/search/${encodeURIComponent(place.name)}`;
  const firstSourceUrl = visits
    .map((visit) => safeExternalUrl(visit.source_url))
    .find((url): url is string => Boolean(url));
  const bannerImage = place.photo_url || getFallbackImage(place.category);

  return (
    <>
      <div className="detail-photo-banner" style={{ position: 'relative', height: 160, overflow: 'hidden', flexShrink: 0 }}>
        <img
          src={bannerImage}
          alt={place.name}
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
        <div style={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(to bottom, rgba(0,0,0,0.2) 0%, transparent 40%, rgba(0,0,0,0.5) 100%)',
          zIndex: 1
        }} />
        <ActionIcon
          variant="filled"
          color="rgba(0,0,0,0.45)"
          radius="xl"
          onClick={onClose}
          style={{ position: 'absolute', top: 12, right: 12, zIndex: 2, backdropFilter: 'blur(4px)', border: 'none' }}
          aria-label="상세 닫기"
        >
          <X size={18} color="#fff" />
        </ActionIcon>
      </div>

      <div className="detail-header-wrapper" style={{ marginTop: 0 }}>
        <Group justify="space-between" wrap="nowrap" className="detail-header">
          <Group gap={6} wrap="wrap">
            <Badge className={`grade-badge grade-${gradeClass(place.grade)}`}>{gradeLabel(place.grade)}</Badge>
            {place.is_closed ? <Badge color="gray">폐업</Badge> : null}
            {!place.is_closed && place.closure_report_count > 0 ? (
              <Badge color="yellow">폐업 제보 {place.closure_report_count}건</Badge>
            ) : null}
          </Group>
        </Group>

        <section className="detail-title">
          <Title order={2}>{place.name}</Title>
          <Text c="dimmed">{place.road_address ?? place.road_address_part ?? '주소 확인 중'}</Text>
        </section>

        <div className="detail-primary-actions" aria-label="장소 액션">
          <Button component="a" href={kakaoUrl} target="_blank" rel="noopener noreferrer" leftSection={<Navigation size={16} />}>
            길찾기
          </Button>
          {firstSourceUrl ? (
            <Button
              component="a"
              href={firstSourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              variant="light"
              leftSection={<ExternalLink size={16} />}
            >
              공공기관 원문
            </Button>
          ) : (
            <Button variant="light" leftSection={<ExternalLink size={16} />} disabled>
              공공기관 원문
            </Button>
          )}
          <Button variant="light" leftSection={<FileText size={16} />} onClick={onReport}>
            정보 수정
          </Button>
          <Button variant="outline" color="gray" leftSection={<AlertTriangle size={16} />} onClick={onClosureReport}>
            폐업 신고
          </Button>
        </div>
      </div>

      <div className="detail-content">
        {place.closure_report_count > 0 && !place.is_closed ? (
          <div className="warning-banner" style={{ marginTop: 0, marginBottom: 16 }}>
            <AlertTriangle size={16} aria-hidden />
            폐업 제보 {place.closure_report_count}건 - 방문 전 확인 권장
          </div>
        ) : null}

        <section className="detail-section official-section" aria-labelledby="official-data-title">
          <div className="section-headline">
            <div>
              <Text size="xs" className="section-kicker">
                공식 공개 데이터
              </Text>
              <Text id="official-data-title" fw={800}>
                공공기록 기반 지표
              </Text>
            </div>
            <Badge size="sm" variant="light" color="blue">
              공공누리 제1유형
            </Badge>
          </div>
          <Text size="xs" c="dimmed">
            최근 12개월 공식 공개 방문 기록에 부서 다양성 가중치(log10)를 적용한 지표입니다. 맛/품질/비위 판단 지표가 아닙니다.
          </Text>
          <div className="stat-grid">
            <Metric label="방문" value={`${place.visit_count_12m ?? 0}회`} />
            <Metric label="부서" value={`${place.unique_department_count_12m ?? 0}개`} />
            <Metric label="최근" value={formatDate(place.last_visit_at) ?? '확인 중'} />
            {place.avg_amount_per_person ? (
              <Metric label="평균 1인당" value={`${place.avg_amount_per_person.toLocaleString('ko-KR')}원`} />
            ) : null}
          </div>
        </section>

        <section className="detail-section visit-section">
          <Text fw={800}>방문 기록</Text>
          {visits.length ? (
            <div className="visit-stack">
              {visits.slice(0, 10).map((visit) => {
                const sourceUrl = safeExternalUrl(visit.source_url);
                return (
                  <article className="visit-row" key={visit.id}>
                    <div className="visit-row-top">
                      <span>{formatDate(visit.visit_date) ?? visit.visit_date}</span>
                      <strong>{visit.amount.toLocaleString('ko-KR')}원</strong>
                    </div>
                    <small>{visitSummary(visit) || '집행 목적 확인 중'}</small>
                    <small className="source-link">
                      {sourceUrl ? (
                        <a
                          href={sourceUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          aria-label={`${place.name} 방문 기록 공공기관 원문`}
                        >
                          <ExternalLink size={13} aria-hidden /> 공공기관 원문
                        </a>
                      ) : (
                        <span className="source-link-unavailable">
                          <ExternalLink size={13} aria-hidden /> 원문 링크 없음
                        </span>
                      )}
                    </small>
                    {!sourceUrl ? (
                      <small className="source-note">공공기관 원문 URL이 없어 요약만 제공합니다.</small>
                    ) : null}
                  </article>
                );
              })}
            </div>
          ) : (
            <Text size="sm" c="dimmed" mt="xs">
              방문 기록을 불러오는 중이거나 공개된 기록이 없습니다.
            </Text>
          )}
        </section>

      </div>
    </>
  );
}
