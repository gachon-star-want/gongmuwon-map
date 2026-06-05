import { MapPin } from 'lucide-react';
import type { Place } from '../types';
import { GradeDot } from './GradeDot';

interface PlaceCardProps {
  place: Place;
  isSelected: boolean;
  onClick: () => void;
}

export function PlaceCard({ place, isSelected, onClick }: PlaceCardProps) {
  return (
    <button
      className="place-card"
      data-selected={isSelected}
      onClick={onClick}
      type="button"
    >
      <div className="place-card-thumb-wrap">
        {place.photo_url ? (
          <img
            className="place-card-thumb"
            src={place.photo_url}
            alt={place.name}
            loading="lazy"
          />
        ) : (
          <div className="place-card-thumb place-card-thumb-empty" aria-hidden />
        )}
        <GradeDot grade={place.grade} />
      </div>
      <div className="place-card-body">
        <div className="place-card-name">{place.name}</div>
        {place.category && (
          <div className="place-card-category">{place.category}</div>
        )}
        {place.unique_department_count_12m && place.unique_department_count_12m > 0 && (
          <div className="place-card-dept">
            <span className="dept-badge">
              🏛 {place.unique_department_count_12m}개 부처 방문
            </span>
          </div>
        )}
        {place.menu_items && place.menu_items.length > 0 && (
          <div className="place-card-menus">
            {place.menu_items.slice(0, 2).map((m) => (
              <span key={m} className="menu-tag">{m}</span>
            ))}
          </div>
        )}
        <div className="place-card-location">
          <MapPin size={11} aria-hidden />
          {place.road_address_part ?? ''}
        </div>
      </div>
    </button>
  );
}
