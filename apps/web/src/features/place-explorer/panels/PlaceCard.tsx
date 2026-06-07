import { Building2, CalendarDays, MapPin } from 'lucide-react';
import type { Place } from '../types';
import { formatDate } from '../format';
import { GradeDot } from './GradeDot';
import { classifyFoodCategory } from '../foodCategories';

interface PlaceCardProps {
  place: Place;
  isSelected: boolean;
  onClick: () => void;
}

export function PlaceCard({ place, isSelected, onClick }: PlaceCardProps) {
  const category = classifyFoodCategory(place);
  const region = place.road_address_part || '지역 확인 중';
  const visitCount = place.visit_count_12m ?? 0;
  const departmentCount = place.unique_department_count_12m ?? 0;
  const lastVisit = formatDate(place.last_visit_at);

  return (
    <button
      className="place-card"
      data-selected={isSelected}
      onClick={onClick}
      type="button"
    >
      <div className="place-card-grade" aria-hidden>
        <GradeDot grade={place.grade} />
      </div>
      <div className="place-card-body">
        <div className="place-card-mainline">
          <span className="place-card-name">{place.name}</span>
          {place.is_closed ? <span className="place-card-status">폐업</span> : null}
        </div>
        <div className="place-card-category">
          <img src={category.icon} alt="" aria-hidden />
          {category.label}
          <span aria-hidden>·</span>
          {region}
        </div>
        <div className="place-card-stats" aria-label="최근 12개월 공식 방문 지표">
          <span>
            <Building2 size={12} aria-hidden />
            {visitCount.toLocaleString('ko-KR')}회
          </span>
          <span>
            <MapPin size={12} aria-hidden />
            {departmentCount.toLocaleString('ko-KR')}개 부서
          </span>
          <span>
            <CalendarDays size={12} aria-hidden />
            {lastVisit ?? '최근 미확인'}
          </span>
        </div>
      </div>
    </button>
  );
}
