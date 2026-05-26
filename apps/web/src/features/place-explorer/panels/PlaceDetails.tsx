import { ActionIcon, Badge, Button, Group, Text, Title } from '@mantine/core';
import { AlertTriangle, ExternalLink, FileText, Navigation, ThumbsDown, ThumbsUp, X } from 'lucide-react';
import type { Place, PlaceReactionSummary, Visit } from '../types';
import { formatDate, gradeClass, gradeLabel } from '../format';
import { Metric } from './metric';

type PlaceDetailsProps = {
  place: Place;
  visits: Visit[];
  onClose: () => void;
  onReport: () => void;
  onClosureReport: () => void;
  reactions?: PlaceReactionSummary | null;
  reactionPending?: boolean;
  onReact?: (reaction: 'like' | 'dislike') => void;
};

export function PlaceDetails({ place, visits, onClose, onReport, onClosureReport, reactions, reactionPending, onReact }: PlaceDetailsProps) {
  const kakaoUrl = `https://map.kakao.com/link/search/${encodeURIComponent(place.name)}`;
  return (
    <div className="detail-content">
      <Group justify="space-between" wrap="nowrap" className="detail-header">
        <Group gap={6}>
          <Badge className={`grade-badge grade-${gradeClass(place.grade)}`}>{gradeLabel(place.grade)}</Badge>
          {place.is_closed ? <Badge color="gray">폐업</Badge> : null}
          {!place.is_closed && place.closure_report_count > 0 ? (
            <Badge color="yellow">폐업 제보 {place.closure_report_count}건</Badge>
          ) : null}
        </Group>
        <ActionIcon variant="subtle" aria-label="상세 닫기" onClick={onClose}>
          <X size={18} />
        </ActionIcon>
      </Group>

      {place.closure_report_count > 0 && !place.is_closed ? (
        <div className="warning-banner">
          <AlertTriangle size={16} aria-hidden />
          폐업 제보 {place.closure_report_count}건 - 방문 전 확인 권장
        </div>
      ) : null}

      <section className="detail-section detail-title">
        <Title order={2}>{place.name}</Title>
        <Text c="dimmed">{place.road_address ?? place.road_address_part ?? '주소 확인 중'}</Text>
      </section>

      <section className="detail-section">
        <Text size="sm" fw={700}>
          방문 빈도와 부서 다양성 기반 통계 신호입니다.
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

      <section className="detail-section reaction-section">
        <Group justify="space-between" align="center">
          <div>
            <Text fw={800}>이 식당 반응</Text>
          </div>
        </Group>
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
      </section>

      <section className="detail-section">
        <Text fw={800}>방문 기록</Text>
        {visits.length ? (
          <div className="visit-stack">
            {visits.slice(0, 10).map((visit) => (
              <a className="visit-row" href={visit.source_url ?? '#'} target="_blank" rel="noreferrer" key={visit.id}>
                <span>{formatDate(visit.visit_date) ?? visit.visit_date}</span>
                <strong>{visit.amount.toLocaleString('ko-KR')}원</strong>
                <small>{[visit.department_name, visit.rank_label, visit.purpose].filter(Boolean).join(' · ')}</small>
                <small className="source-link">
                  <ExternalLink size={13} aria-hidden /> 원문 보기
                </small>
              </a>
            ))}
          </div>
        ) : (
          <Text size="sm" c="dimmed" mt="xs">
            방문 기록을 불러오는 중이거나 공개된 기록이 없습니다.
          </Text>
        )}
      </section>

      <section className="detail-section detail-actions">
        <Button component="a" href={kakaoUrl} target="_blank" rel="noreferrer" leftSection={<Navigation size={16} />}>
          카카오맵에서 보기
        </Button>
        <Button variant="light" leftSection={<FileText size={16} />} onClick={onReport}>
          정보 수정·삭제 요청
        </Button>
        <Button variant="outline" color="gray" leftSection={<AlertTriangle size={16} />} onClick={onClosureReport}>
          폐업 신고
        </Button>
      </section>
    </div>
  );
}
