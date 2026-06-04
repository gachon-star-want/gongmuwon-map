import { ActionIcon, Badge, Button, Group, Text, Title } from '@mantine/core';
import { AlertTriangle, ExternalLink, FileText, Navigation, ThumbsDown, ThumbsUp, X } from 'lucide-react';
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

function getCategoryImageUrl(category: string | null): string {
  if (!category) {
    return 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=600&q=80';
  }
  const cat = category.toLowerCase();
  if (cat.includes('카페') || cat.includes('커피') || cat.includes('디저트') || cat.includes('제과')) {
    return 'https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&w=600&q=80';
  }
  if (cat.includes('일식') || cat.includes('초밥') || cat.includes('회') || cat.includes('스시') || cat.includes('사시미')) {
    return 'https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=600&q=80';
  }
  if (cat.includes('중식') || cat.includes('중국') || cat.includes('짜장') || cat.includes('짬뽕')) {
    return 'https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=600&q=80';
  }
  if (cat.includes('고기') || cat.includes('갈비') || cat.includes('삼겹살') || cat.includes('육류') || cat.includes('곱창')) {
    return 'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=600&q=80';
  }
  if (cat.includes('피자') || cat.includes('파스타') || cat.includes('양식') || cat.includes('이탈리안')) {
    return 'https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=600&q=80';
  }
  if (cat.includes('분식') || cat.includes('떡볶이') || cat.includes('순대') || cat.includes('김밥') || cat.includes('라면') || cat.includes('우동')) {
    return 'https://images.unsplash.com/photo-1627308595229-7830a5c91f9f?auto=format&fit=crop&w=600&q=80';
  }
  if (cat.includes('한식') || cat.includes('찌개') || cat.includes('국밥') || cat.includes('탕') || cat.includes('정식') || cat.includes('낙지') || cat.includes('쌈밥')) {
    return 'https://images.unsplash.com/photo-1608039755401-742074f0548d?auto=format&fit=crop&w=600&q=80';
  }
  return 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=600&q=80';
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
  const reactionHint = isAuthenticated
    ? '좋아요/싫어요는 공식 기록과 분리된 커뮤니티 참고 신호입니다.'
    : '로그인 후 좋아요/싫어요 반응을 남길 수 있으며, 공식 데이터와 분리된 참고 신호입니다.';
  return (
    <>
      <div className="detail-header-wrapper">
        <img
          className="detail-cover-image"
          src={getCategoryImageUrl(place.category)}
          alt={`${place.category ?? '음식'} 카테고리 이미지`}
          loading="eager"
        />
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
      </div>

      <div className="detail-content">
        {place.closure_report_count > 0 && !place.is_closed ? (
          <div className="warning-banner" style={{ marginTop: 0, marginBottom: 16 }}>
            <AlertTriangle size={16} aria-hidden />
            폐업 제보 {place.closure_report_count}건 - 방문 전 확인 권장
          </div>
        ) : null}

      <section className="detail-section detail-title">
        <Title order={2}>{place.name}</Title>
        <Text c="dimmed">{place.road_address ?? place.road_address_part ?? '주소 확인 중'}</Text>
      </section>

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
          근거: 최근 12개월 공식 공개 방문 기록에 부서 다양성 가중치(log10)를 적용한 지표입니다. 맛/품질/비위 판단 지표가 아닙니다.
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

      <section className="detail-section">
        <Text fw={800}>방문 기록</Text>
        {visits.length ? (
          <div className="visit-stack">
            {visits.slice(0, 10).map((visit) => {
              const sourceUrl = safeExternalUrl(visit.source_url);
              return (
                <article className="visit-row" key={visit.id}>
                  <span>{formatDate(visit.visit_date) ?? visit.visit_date}</span>
                  <strong>{visit.amount.toLocaleString('ko-KR')}원</strong>
                  <small>{[visit.department_name, visit.rank_label, visit.purpose].filter(Boolean).join(' · ')}</small>
                  <small className="source-link">
                    {sourceUrl ? (
                      <a
                        href={sourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        aria-label={`${place.name} 방문 기록 원문 보기`}
                      >
                        <ExternalLink size={13} aria-hidden /> 원문 보기
                      </a>
                    ) : (
                      <span className="source-link-unavailable">
                        <ExternalLink size={13} aria-hidden /> 원문 링크 없음
                      </span>
                    )}
                  </small>
                  {!sourceUrl ? (
                    <small className="source-note">원문 링크가 미제공되어 요약만 제공됩니다.</small>
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

      <section className="detail-section detail-actions">
        <div className="policy-cues">
          <Text size="xs" fw={700}>
            판단/신뢰 안내
          </Text>
          <Text size="xs">
            점수·등급은 공공기록 통계(방문 수·부서 수)로만 산출되며, 맛집 평가·품질점수·비위 판단을 뜻하지 않습니다.
          </Text>
          <Text size="xs">원문 출처 확인은 각 방문 기록의 링크 또는 푸터의 공개자료 출처에서 확인 가능합니다.</Text>
          <Text size="xs">
            정보 수정·삭제 요청은 즉시 임시 비공개 처리 후 운영자가 72시간 이내 검토합니다.
          </Text>
        </div>
        <Button component="a" href={kakaoUrl} target="_blank" rel="noopener noreferrer" leftSection={<Navigation size={16} />}>
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
  </>
  );
}
