export function shouldShowAd(index: number) {
  return index > 0 && index % 5 === 4;
}

const AD_LABEL = '광고';

export function AdSlot() {
  return (
    <div className="ad-slot">
      <span className="ad-slot-label">{AD_LABEL}</span>
      <strong className="ad-slot-title">스폰서 광고 자리</strong>
      <span className="ad-slot-sub">지역 맛집 · 식당 · 카페 홍보 문의</span>
    </div>
  );
}
