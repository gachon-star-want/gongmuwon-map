export function roadAddressPart(address) {
  if (!address) return null;
  const match = address.match(/(서울(?:특별시)?|인천(?:광역시)?|대전(?:광역시)?|대구(?:광역시)?|광주(?:광역시)?|울산(?:광역시)?|부산(?:광역시)?|세종(?:특별자치시)?|경기(?:도)?|강원(?:특별자치도)?|충북|충남|전북|전남|경북|경남|제주(?:특별자치도)?)\s+([가-힣]+[구군시])/);
  if (match) {
    let region = match[1];
    if (region.startsWith('서울')) region = '서울';
    else if (region.startsWith('경기')) region = '경기';
    else if (region.startsWith('대전')) region = '대전';
    else if (region.startsWith('인천')) region = '인천';
    else if (region.startsWith('대구')) region = '대구';
    else if (region.startsWith('광주')) region = '광주';
    else if (region.startsWith('울산')) region = '울산';
    else if (region.startsWith('부산')) region = '부산';
    else if (region.startsWith('세종')) region = '세종';
    else if (region.startsWith('강원')) region = '강원';
    else if (region.startsWith('제주')) region = '제주';
    return `${region} ${match[2]}`;
  }
  return null;
}
