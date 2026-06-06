import { ActionIcon, Badge, Button, Group, Text, Title } from '@mantine/core';
import {
  AlertTriangle,
  ExternalLink,
  FileText,
  Navigation,
  ThumbsDown,
  ThumbsUp,
  X,
} from 'lucide-react';
import type { Place, PlaceReactionSummary, Visit } from '../types';
import { formatDate, gradeClass, gradeLabel } from '../format';
import { Metric } from './metric';
import { safeExternalUrl } from '../../../shared/safeExternalUrl';

type PlaceDetailsProps = {
  place: Place;
  visits: Visit[];
  onClose: () => void;
  onReport: () => void;
  onClosureReport: () => void;
  reactions?: PlaceReactionSummary | null;
  reactionPending?: boolean;
  onReact?: (reaction: 'like' | 'dislike') => void;
  isAuthenticated?: boolean;
};

function categoryLabel(category: string | null) {
  if (!category) return '음식점';
  return category.split('>').at(-1)?.trim() || category;
}

function visitSummary(visit: Visit) {
  return [visit.department_name, visit.rank_label, visit.purpose].filter(Boolean).join(' · ');
}

export function PlaceDetails({
  place,
  visits,
  onClose,
  onReport,
  onClosureReport,
  reactions,
  reactionPending,
  onReact,
  isAuthenticated = false,
}: PlaceDetailsProps) {
  const kakaoUrl = `https://map.kakao.com/link/search/${encodeURIComponent(place.name)}`;
  const firstSourceUrl = visits
    .map((visit) => safeExternalUrl(visit.source_url))
    .find((url): url is string => Boolean(url));
  const reactionHint = isAuthenticated
    ? '좋아요/싫어요는 공식 기록과 분리된 커뮤니티 참고 신호입니다.'
    : '로그인 후 좋아요/싫어요 반응을 남길 수 있으며, 공식 데이터와 분리된 참고 신호입니다.';

  return (
    <>
      <div className="detail-header-wrapper">
        <Group justify="space-between" wrap="nowrap" className="detail-header">
          <Group gap={6} wrap="wrap">
            <Badge className={`grade-badge grade-${gradeClass(place.grade)}`}>{gradeLabel(place.grade)}</Badge>
            <Badge variant="light" color="gray">{categoryLabel(place.category)}</Badge>
            {place.is_closed ? <Badge color="gray">폐업</Badge> : null}
            {!place.is_closed && place.closure_report_count > 0 ? (
              <Badge color="yellow">폐업 제보 {place.closure_report_count}건</Badge>
            ) : null}
          </Group>
          <ActionIcon variant="subtle" aria-label="상세 닫기" onClick={onClose}>
            <X size={18} />
          </ActionIcon>
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

        <section className="detail-section reaction-section" aria-labelledby="community-reaction-title">
          <div className="section-headline">
            <div>
              <Text size="xs" className="section-kicker">
                커뮤니티 반응
              </Text>
              <Text id="community-reaction-title" fw={800}>
                참고용 반응
              </Text>
            </div>
            <Badge size="sm" variant="light" color="gray">
              로그인 사용자만 참여
            </Badge>
          </div>
          <div className="reaction-actions">
            <button
              type="button"
              data-active={reactions?.user_reaction === 'like'}
              disabled={reactionPending}
              onClick={() => onReact?.('like')}
            >
              <ThumbsUp size={17} aria-hidden />
              좋아요
              <strong>{reactions?.like_count ?? 0}</strong>
            </button>
            <button
              type="button"
              data-active={reactions?.user_reaction === 'dislike'}
              disabled={reactionPending}
              onClick={() => onReact?.('dislike')}
            >
              <ThumbsDown size={17} aria-hidden />
              싫어요
              <strong>{reactions?.dislike_count ?? 0}</strong>
            </button>
          </div>
          <Text size="xs" c="dimmed" className="reaction-hint">
            {reactionHint}
          </Text>
        </section>

        <section className="detail-section detail-actions">
          <div className="policy-cues">
            <Text size="xs" fw={700}>
              판단/신뢰 안내
            </Text>
            <Text size="xs">
              점수·등급은 공공기록 통계(방문 수·부서 수)로만 산출되며, 맛집 평가·품질점수·비위 판단을 뜻하지 않습니다.
            </Text>
            <Text size="xs">
              원문 링크는 R2 보관본이 아니라 공공기관이 공개한 원문 URL입니다.
            </Text>
            <Text size="xs">
              정보 수정·삭제 요청은 즉시 임시 비공개 처리 후 운영자가 72시간 이내 검토합니다.
            </Text>
          </div>
        </section>
      </div>
    </>
  );
}
