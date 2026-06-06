# 공무원맵 디자인 시스템 v2

> Opencode 구현 전용 스펙. 모호한 표현 없이 모든 값이 코드로 바로 옮겨질 수 있어야 한다.

---

## 0. 현재 코드베이스 요약 (Before 상태)

구현 전 파악한 실제 코드 상태.

### 라우터
React Router 미사용. `App.tsx`에서 `window.location.pathname`으로 분기.
```tsx
// apps/web/src/app/App.tsx
if (path === '/community') content = <CommunityPage />;
else content = <PlaceExplorer />;
```
→ **AppShell은 App.tsx 레벨에서 두 페이지를 감싸야 한다.**

### 기존 z-index 레이어 (유지)
```
0    kakao-map / fallback-map
80   source-pill
90   map-ad-rail, fallback-back
100  desktop-controls  ← 삭제 예정
120  list-sheet         ← 리팩터링 예정
130  map-status
140  bottom-nav
160  detail-drawer, bottom-sheet
```

### Grade 타입 (변경 없음)
```ts
type Grade = '★★★' | '★★' | '★' | '✦';
```
`★★★` = 최상위(레드), `★★` = 상위(오렌지), `★` = 일반(인디고), `✦` = 신규(시안)

### 현재 Place 타입에 없는 필드 (신규 추가 필요)
```ts
// 카카오맵 Place API 연동 후 추가
photo_url?: string | null;       // 대표 사진
menu_items?: string[] | null;    // 메뉴 2~3개
```

### 현재 폰트 (이미 Pretendard 선언됨)
```css
/* styles.css — 변경 없음, 이미 적용 */
font-family: Pretendard, Inter, -apple-system, ...;
```
→ **Pretendard Variable CDN 링크를 `index.html`에 추가하는 것만 하면 된다.**

---

## 1. 토큰 시스템 (CSS Custom Properties)

`apps/web/src/styles.css` `:root`에 추가한다.

### 컬러
```css
:root {
  /* 브랜드 */
  --color-brand:         #1A2E5A;
  --color-brand-mid:     #2B4589;
  --color-brand-light:   #EEF2FF;
  --color-brand-hover:   #162548;

  /* 포인트 — 앰버 (방문부처 뱃지, 강조) */
  --color-accent:        #F59E0B;
  --color-accent-light:  #FEF3C7;
  --color-accent-text:   #92400E;

  /* 서피스 */
  --color-surface:       #FFFFFF;
  --color-surface-2:     #F8FAFC;
  --color-surface-3:     #F1F5F9;
  --color-surface-4:     #E8EEF3;   /* 지도 배경 */

  /* 테두리 */
  --color-border:        #E2E8F0;
  --color-border-mid:    #CBD5E1;
  --color-border-strong: #94A3B8;

  /* 텍스트 */
  --color-text-primary:   #0F172A;
  --color-text-secondary: #475569;
  --color-text-muted:     #94A3B8;
  --color-text-inverse:   #FFFFFF;

  /* 등급 */
  --color-grade-top:      #DC2626;  /* ★★★ */
  --color-grade-good:     #EA580C;  /* ★★  */
  --color-grade-neutral:  #4F46E5;  /* ★   */
  --color-grade-new:      #0891B2;  /* ✦   */

  /* 상태 */
  --color-closed:         #94A3B8;
  --color-error:          #DC2626;
  --color-error-bg:       #FEF2F2;

  /* 광고 */
  --color-ad-bg:          #F8FAFC;
  --color-ad-border:      #E2E8F0;
  --color-ad-label:       #94A3B8;
}
```

### 스페이싱 스케일
```css
:root {
  --space-1:  4px;
  --space-2:  8px;
  --space-3:  12px;
  --space-4:  16px;
  --space-5:  20px;
  --space-6:  24px;
  --space-8:  32px;
  --space-10: 40px;
  --space-12: 48px;
}
```

### 그림자
```css
:root {
  --shadow-sm:   0 1px 3px rgba(15, 23, 42, 0.08), 0 1px 2px rgba(15, 23, 42, 0.06);
  --shadow-md:   0 4px 12px rgba(15, 23, 42, 0.10), 0 2px 4px rgba(15, 23, 42, 0.06);
  --shadow-lg:   0 18px 46px rgba(15, 23, 42, 0.16), 0 4px 12px rgba(15, 23, 42, 0.08);
  --shadow-panel: 2px 0 20px rgba(15, 23, 42, 0.08);  /* 좌측 패널 오른쪽 그림자 */
  --shadow-detail: -2px 0 20px rgba(15, 23, 42, 0.10); /* 상세 드로어 왼쪽 그림자 */
}
```

### 컨트롤 규격
```css
:root {
  --control-height:      36px;   /* 모든 버튼/셀렉트/칩 */
  --control-height-lg:   40px;   /* 검색창만 예외 */
  --control-radius:      8px;
  --control-radius-pill: 999px;
  --panel-width:         360px;
  --panel-width-narrow:  280px;  /* 태블릿 */
  --panel-header-height: 56px;
  --topbar-height:       56px;   /* 커뮤니티 페이지 동일값 사용 */
}
```

### 애니메이션
```css
:root {
  --ease-standard:   cubic-bezier(0.4, 0, 0.2, 1);
  --ease-decelerate: cubic-bezier(0, 0, 0.2, 1);
  --ease-accelerate: cubic-bezier(0.4, 0, 1, 1);
  --duration-fast:   100ms;
  --duration-base:   150ms;
  --duration-slow:   220ms;
  --duration-enter:  200ms;
  --duration-exit:   150ms;
}
```

---

## 2. Mantine Theme Override

`apps/web/src/main.tsx`의 `<MantineProvider>` 수정.

```tsx
import { createTheme, MantineProvider } from '@mantine/core';

const theme = createTheme({
  fontFamily:
    "'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  primaryColor: 'brand',
  colors: {
    brand: [
      '#EEF2FF', '#E0E8FF', '#C7D4F7', '#A5B8F0',
      '#7B96E6', '#5174DA', '#2B4589', '#1A2E5A',
      '#142446', '#0E1A33',
    ],
  },
  defaultRadius: 'sm',   // 8px
  components: {
    TextInput: {
      defaultProps: { size: 'sm' },
      styles: {
        input: { height: 'var(--control-height-lg)', borderColor: 'var(--color-border-mid)' },
      },
    },
    Select: {
      defaultProps: { size: 'sm' },
      styles: {
        input: { height: 'var(--control-height)', borderColor: 'var(--color-border-mid)' },
      },
    },
    MultiSelect: {
      defaultProps: { size: 'sm' },
      styles: {
        input: { minHeight: 'var(--control-height)', borderColor: 'var(--color-border-mid)' },
      },
    },
    Button: {
      defaultProps: { size: 'sm' },
      styles: { root: { height: 'var(--control-height)', fontWeight: 700 } },
    },
    ActionIcon: {
      defaultProps: { size: 'sm', variant: 'subtle' },
      styles: { root: { width: 'var(--control-height)', height: 'var(--control-height)' } },
    },
  },
});
```

---

## 3. 레이아웃 구조

### 3-1. AppShell (신규)

파일: `apps/web/src/app/AppShell.tsx`

```tsx
export function AppShell({ children }: { children: ReactNode }) {
  const path = window.location.pathname;
  const isMap = path === '/' || !specialPaths.has(path);
  const isCommunity = path === '/community';

  return (
    <div className="app-shell">
      <div className="left-panel">
        <PanelHeader activePage={isCommunity ? 'community' : 'map'} />
        <div className="panel-body">
          {children}
        </div>
      </div>
      {isMap && (
        <main className="map-area" aria-label="지도">
          {/* MapCanvas는 PlaceExplorer에서 렌더 */}
        </main>
      )}
    </div>
  );
}
```

CSS (`styles.css`에 추가):
```css
.app-shell {
  display: flex;
  width: 100vw;
  height: 100dvh;
  overflow: hidden;
}

.left-panel {
  position: relative;
  z-index: 200;
  display: flex;
  width: var(--panel-width);
  flex-shrink: 0;
  flex-direction: column;
  height: 100dvh;
  background: var(--color-surface);
  box-shadow: var(--shadow-panel);
}

.panel-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.map-area {
  flex: 1;
  position: relative;
  overflow: hidden;
}
```

### 3-2. PanelHeader (신규)

파일: `apps/web/src/app/PanelHeader.tsx`

**이 컴포넌트가 레이아웃 연속성의 핵심이다.**
지도 ↔ 커뮤니티 전환 시 이 컴포넌트는 절대 리렌더링되거나 위치가 바뀌어서는 안 된다.

```tsx
interface PanelHeaderProps {
  activePage: 'map' | 'community';
  currentUser?: CurrentUser | null;
  onLogin?: () => void;
  onLogout?: () => void;
}

export function PanelHeader({ activePage, currentUser, onLogin, onLogout }: PanelHeaderProps) {
  return (
    <header className="panel-header">
      <a className="panel-brand" href="/" aria-label="공무원맵 홈">
        <img src={mascotLogo} alt="" aria-hidden width={28} height={28} />
        <span>공무원맵</span>
      </a>
      <nav className="panel-nav" aria-label="페이지 탐색">
        <a href="/" className="panel-nav-tab" data-active={activePage === 'map'}>
          <MapPin size={15} aria-hidden />
          지도
        </a>
        <a href="/community" className="panel-nav-tab" data-active={activePage === 'community'}>
          <MessageCircle size={15} aria-hidden />
          커뮤니티
        </a>
      </nav>
      <div className="panel-header-auth">
        {currentUser ? (
          <button className="panel-auth-btn" onClick={onLogout}>
            <UserRound size={14} />
            {currentUser.handle}
          </button>
        ) : (
          <button className="panel-auth-btn" onClick={onLogin}>
            <LogIn size={14} />
            로그인
          </button>
        )}
      </div>
    </header>
  );
}
```

CSS:
```css
.panel-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  height: var(--panel-header-height);
  padding: 0 var(--space-4);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
  /* View Transitions: 이 요소는 페이지 전환 중에도 제자리 */
  view-transition-name: panel-header;
}

.panel-brand {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-brand);
  font-size: 17px;
  font-weight: 900;
  text-decoration: none;
  letter-spacing: -0.3px;
  flex-shrink: 0;
  view-transition-name: brand-logo;
}

.panel-brand img {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
}

.panel-nav {
  display: flex;
  gap: var(--space-1);
  flex: 1;
  justify-content: center;
}

.panel-nav-tab {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: var(--control-height);
  padding: 0 10px;
  border-radius: var(--control-radius);
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
  transition: background var(--duration-base) var(--ease-standard),
              color var(--duration-base) var(--ease-standard);
}

.panel-nav-tab:hover {
  background: var(--color-surface-3);
  color: var(--color-text-primary);
}

.panel-nav-tab[data-active='true'] {
  background: var(--color-brand);
  color: var(--color-text-inverse);
}

.panel-header-auth {
  flex-shrink: 0;
}

.panel-auth-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: var(--control-height);
  padding: 0 10px;
  border: 1.5px solid var(--color-border-mid);
  border-radius: var(--control-radius);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  transition: all var(--duration-base) var(--ease-standard);
}

.panel-auth-btn:hover {
  border-color: var(--color-brand-mid);
  color: var(--color-brand-mid);
}
```

### 3-3. 지도 페이지 패널 내부 구조

`PlaceExplorer.tsx`의 패널 부분:

```
<div className="panel-body">
  <PanelSearchBar />          ← 검색창 (52px)
  <PanelFilterBar />          ← 자치구, 정렬, 칩 (auto height, max 88px)
  <PanelResultLabel />        ← "결과 347곳" (32px)
  <PlaceList />               ← 스크롤 리스트 (flex: 1)
</div>
```

### 3-4. 커뮤니티 페이지

`CommunityPage.tsx`에서 기존 `.community-topbar`를 제거하고 `AppShell`의 `PanelHeader`를 공유한다.
커뮤니티 콘텐츠는 `.panel-body` 안에서 렌더된다.

---

## 4. 컴포넌트 상세 스펙

### 4-1. 검색창 (PanelSearchBar)

파일: `apps/web/src/features/place-explorer/panels/PanelSearchBar.tsx`

```css
.panel-search-wrap {
  flex-shrink: 0;
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

/* Mantine TextInput 오버라이드 */
.panel-search .mantine-TextInput-input {
  height: var(--control-height-lg);
  border-radius: var(--control-radius);
  border-color: var(--color-border-mid);
  font-size: 13px;
  transition: border-color var(--duration-base) var(--ease-standard),
              box-shadow var(--duration-base) var(--ease-standard);
}

.panel-search .mantine-TextInput-input:focus {
  border-color: var(--color-brand-mid);
  box-shadow: 0 0 0 3px rgba(43, 69, 137, 0.12);
}
```

지원 검색 패턴 (검색 로직 확장 시 참고):
- `미스트앤머그` → 식당명 직접 매칭
- `마포구` → `road_address_part` 필터
- `분당 맛집`, `합정역 고기집` → 지역명 + 카테고리 분리 파싱 후 각각 매칭
- `기재부 근처` → `department_name` 기반 위치 검색 (Visit 테이블 join)

자동완성 드롭다운: 검색어 2자 이상 입력 시 표시. 식당명 > 자치구명 > 부처명 우선순위.

### 4-2. 필터 바 (PanelFilterBar)

파일: `apps/web/src/features/place-explorer/panels/PanelFilterBar.tsx`

```css
.panel-filter-bar {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4) var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

/* Mantine Select/MultiSelect 높이 통일 */
.panel-filter-bar .mantine-Select-input,
.panel-filter-bar .mantine-MultiSelect-input {
  min-height: var(--control-height);
  height: var(--control-height);
}

.filter-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  height: var(--control-height);
  padding: 0 12px;
  border: 1.5px solid var(--color-border-mid);
  border-radius: var(--control-radius-pill);
  background: var(--color-surface);
  color: var(--color-text-primary);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  transition: all var(--duration-base) var(--ease-standard);
}

.filter-chip:hover {
  border-color: var(--color-brand-mid);
  color: var(--color-brand-mid);
}

.filter-chip[data-active='true'] {
  border-color: var(--color-brand);
  background: var(--color-brand);
  color: var(--color-text-inverse);
}

.filter-reset-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: var(--control-height);
  padding: 0 10px;
  border: none;
  border-radius: var(--control-radius);
  background: transparent;
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  margin-left: auto;
  transition: color var(--duration-base) var(--ease-standard);
}

.filter-reset-btn:hover {
  color: var(--color-text-primary);
}
```

### 4-3. 결과 레이블 바

```css
.panel-result-label {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 32px;
  padding: 0 var(--space-4);
  border-bottom: 1px solid var(--color-border);
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
```

### 4-4. 식당 카드 (PlaceCard) — 핵심 변경

현재 `.place-row` (grade-dot + 텍스트) → 사진 + 방문부처 포함 신규 카드로 교체.

파일: `apps/web/src/features/place-explorer/panels/PlaceCard.tsx` (신규)

```tsx
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
```

CSS:
```css
.place-card {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: none;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
  color: inherit;
  cursor: pointer;
  text-align: left;
  transition: background var(--duration-fast) var(--ease-standard);
}

.place-card:hover {
  background: var(--color-surface-3);
}

.place-card[data-selected='true'] {
  background: var(--color-brand-light);
  box-shadow: inset 3px 0 0 var(--color-brand);
}

/* 사진 영역 */
.place-card-thumb-wrap {
  position: relative;
  width: 80px;
  height: 80px;
  flex-shrink: 0;
}

.place-card-thumb {
  width: 80px;
  height: 80px;
  border-radius: var(--control-radius);
  object-fit: cover;
  background: var(--color-surface-3);
  display: block;
}

.place-card-thumb-empty {
  background:
    linear-gradient(135deg, var(--color-surface-3) 0%, var(--color-surface-4) 100%);
}

/* GradeDot: 사진 우하단 오버레이 */
.place-card-thumb-wrap .grade-dot {
  position: absolute;
  right: -4px;
  bottom: -4px;
}

/* 텍스트 영역 */
.place-card-body {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
  padding-top: 2px;
}

.place-card-name {
  font-size: 14px;
  font-weight: 800;
  color: var(--color-text-primary);
  line-height: 1.25;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.place-card-category {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-muted);
}

.place-card-dept {
  margin-top: 2px;
}

.dept-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  height: 20px;
  padding: 0 7px;
  border-radius: 4px;
  background: var(--color-accent-light);
  color: var(--color-accent-text);
  font-size: 11px;
  font-weight: 700;
}

.place-card-menus {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-top: 2px;
}

.menu-tag {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--color-surface-3);
  color: var(--color-text-secondary);
  font-size: 11px;
  font-weight: 500;
}

.place-card-location {
  display: flex;
  align-items: center;
  gap: 3px;
  margin-top: auto;
  font-size: 11px;
  color: var(--color-text-muted);
}
```

### 4-5. 등급 뱃지 (GradeDot)

현재 캡슐형(42×26px) → 완전 원형(26×26px)으로 변경.

```css
/* 기존 .grade-dot 교체 */
.grade-dot {
  width: 26px;
  height: 26px;         /* width == height 필수 */
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
  line-height: 1;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.2);
}

.grade-top     { background: var(--color-grade-top); }
.grade-good    { background: var(--color-grade-good); }
.grade-neutral { background: var(--color-grade-neutral); }
.grade-new     { background: var(--color-grade-new); }
```

GradeDot 컴포넌트:
```tsx
// apps/web/src/features/place-explorer/panels/GradeDot.tsx
export function GradeDot({ grade }: { grade: Grade }) {
  const cls =
    grade === '★★★' ? 'grade-top' :
    grade === '★★'  ? 'grade-good' :
    grade === '★'   ? 'grade-neutral' :
                      'grade-new';
  const label =
    grade === '★★★' ? '최상위' :
    grade === '★★'  ? '상위' :
    grade === '★'   ? '일반' : '신규';
  return (
    <span className={`grade-dot ${cls}`} aria-label={`${label} 등급`}>
      {grade}
    </span>
  );
}
```

### 4-6. 광고 슬롯 (AdSlot)

파일: `apps/web/src/features/place-explorer/panels/AdSlot.tsx`

카드 5개마다 1개 삽입. `PlaceList.tsx`의 렌더 루프에서 `index % 5 === 4` 조건으로 카드 다음에 삽입.

```css
.ad-slot {
  display: grid;
  gap: var(--space-1);
  padding: 10px var(--space-4);
  border-bottom: 1px solid var(--color-ad-border);
  background: var(--color-ad-bg);
  text-decoration: none;
  color: var(--color-text-primary);
  transition: background var(--duration-fast) var(--ease-standard);
}

.ad-slot:hover {
  background: var(--color-surface-3);
}

.ad-slot-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--color-ad-label);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.ad-slot-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.3;
}

.ad-slot-sub {
  font-size: 11px;
  color: var(--color-text-secondary);
}
```

원칙:
- 첫 번째 카드 위 광고 없음
- 광고는 카드와 동일한 좌우 패딩 유지
- `[광고]` 레이블 반드시 표시

---

## 5. 스켈레톤 로딩

카드 로딩 중 PlaceCard 자리에 표시.

```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--color-surface-3) 25%,
    var(--color-surface-2) 50%,
    var(--color-surface-3) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.4s ease infinite;
  border-radius: var(--control-radius);
}

@keyframes skeleton-shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.skeleton-card {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.skeleton-thumb {
  width: 80px;
  height: 80px;
  border-radius: var(--control-radius);
}

.skeleton-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding-top: var(--space-1);
}

.skeleton-line-title  { height: 14px; width: 70%; }
.skeleton-line-sub    { height: 11px; width: 45%; }
.skeleton-line-badge  { height: 20px; width: 30%; }
```

---

## 6. 빈 상태 / 에러 상태

```css
.panel-empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-8) var(--space-6);
  text-align: center;
  color: var(--color-text-muted);
}

.panel-empty-state-icon {
  font-size: 40px;
  line-height: 1;
}

.panel-empty-state-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-secondary);
}

.panel-empty-state-desc {
  font-size: 12px;
  line-height: 1.6;
  max-width: 220px;
}
```

텍스트 예시:
- 검색 결과 없음: "**'분당'에서 결과를 찾지 못했어요.** 다른 지역이나 식당명으로 검색해보세요."
- 데이터 오류: "**목록을 불러오지 못했습니다.** 잠시 후 다시 시도해주세요."

---

## 7. 포커스 링 (Accessibility)

```css
/* 기존 브라우저 기본 outline 제거 후 커스텀 */
:focus-visible {
  outline: 2px solid var(--color-brand-mid);
  outline-offset: 2px;
  border-radius: var(--control-radius);
}

/* 카드는 inset focus ring */
.place-card:focus-visible {
  outline: 2px solid var(--color-brand-mid);
  outline-offset: -2px;
}
```

---

## 8. 스크롤바 스타일링

```css
/* 패널 스크롤 영역에 적용 */
.panel-scroll-area {
  overflow-y: auto;
  overscroll-behavior: contain;
}

.panel-scroll-area::-webkit-scrollbar {
  width: 4px;
}

.panel-scroll-area::-webkit-scrollbar-track {
  background: transparent;
}

.panel-scroll-area::-webkit-scrollbar-thumb {
  background: var(--color-border-mid);
  border-radius: 2px;
}

.panel-scroll-area::-webkit-scrollbar-thumb:hover {
  background: var(--color-border-strong);
}
```

---

## 9. 페이지 전환 — CSS View Transitions

`App.tsx`에서 내비게이션 시 `document.startViewTransition()` 사용.

```tsx
// App.tsx 수정
function navigateTo(path: string) {
  if (!document.startViewTransition) {
    window.location.href = path;
    return;
  }
  document.startViewTransition(() => {
    window.history.pushState({}, '', path);
    // React 리렌더 트리거 (useState나 전역 상태로 처리)
  });
}
```

```css
/* 공유 요소: 전환 중 제자리 */
.panel-header    { view-transition-name: panel-header; }
.panel-brand     { view-transition-name: brand-logo; }

/* 패널 콘텐츠 전환 */
@keyframes panel-content-in {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

::view-transition-new(.panel-body) {
  animation: panel-content-in var(--duration-enter) var(--ease-decelerate);
}

::view-transition-old(.panel-body) {
  animation: none;
  opacity: 0;
}
```

---

## 10. 반응형 브레이크포인트

모든 CSS 파일에서 동일한 값 사용. 커뮤니티의 `1160px`은 폐기.

```css
/* ── 데스크탑 (기본) ─────── ≥ 1024px */
/* 좌측 패널 360px, 지도 전체 */

/* ── 태블릿 ──────────────── 768px–1023px */
@media (max-width: 1023px) {
  .left-panel { width: var(--panel-width-narrow); }
}

/* ── 모바일 ──────────────── ≤ 767px */
@media (max-width: 767px) {
  .left-panel      { display: none; }
  .bottom-sheet    { display: flex; }
  .bottom-nav      { display: flex; }
}
```

---

## 11. 파일 구조 변경 요약

### 신규 생성
```
apps/web/src/
  app/
    AppShell.tsx          ← 레이아웃 쉘, PanelHeader 고정
    PanelHeader.tsx       ← 로고 + 탭 + 로그인
  features/place-explorer/panels/
    PanelSearchBar.tsx    ← 검색창 단독 컴포넌트
    PanelFilterBar.tsx    ← 자치구/정렬/칩 묶음
    PlaceCard.tsx         ← 사진 포함 새 카드
    GradeDot.tsx          ← 원형 등급 뱃지
    AdSlot.tsx            ← 광고 슬롯
    SkeletonCard.tsx      ← 로딩 스켈레톤
```

### 수정
```
apps/web/src/
  app/App.tsx             ← AppShell로 감싸기
  main.tsx                ← Mantine theme 추가
  styles.css              ← CSS 변수 추가, app-shell 레이아웃
  features/place-explorer/
    PlaceExplorer.tsx     ← floating-search 제거, LeftPanel 구조로 리팩터
    styles.css            ← floating-search, desktop-controls, list-sheet 재정의
    panels/SearchFilterBar.tsx ← PanelHeader로 로고/탭 이전, PanelFilterBar로 분리
    panels/PlaceList.tsx  ← PlaceCard로 교체, AdSlot 삽입
  features/community/
    CommunityPage.tsx     ← community-topbar 제거, AppShell PanelHeader 공유
    styles.css            ← community-topbar 제거, 브레이크포인트 1160px→1023px
```

### 삭제 (또는 비워두기)
```
.floating-search 클래스 및 해당 JSX
.desktop-controls 클래스 및 해당 JSX
.community-topbar 클래스 및 해당 JSX
.brand-mark (SearchFilterBar 내부) → PanelHeader로 이전
.map-mode-tabs → PanelHeader의 .panel-nav로 대체
```

---

## 12. index.html 변경사항

```html
<head>
  <!-- Pretendard Variable (기존 Pretendard 대체) -->
  <link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin />
  <link
    rel="stylesheet"
    href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css"
  />
</head>
```

`styles.css`의 `font-family` 첫 값을 `'Pretendard Variable'`로 업데이트:
```css
body {
  font-family:
    'Pretendard Variable', Pretendard,
    -apple-system, BlinkMacSystemFont,
    'Segoe UI', sans-serif;
}
```

---

## 13. 구현 우선순위

| 순서 | 작업 | 영향 범위 |
|------|------|-----------|
| **P0** | CSS 토큰 시스템 (`styles.css` `:root` 변수) | 전체 기반 |
| **P0** | `AppShell` + `PanelHeader` 구조 | 레이아웃 연속성 |
| **P0** | `App.tsx` AppShell로 감싸기 | 라우팅 |
| **P0** | Mantine theme override (`main.tsx`) | 컨트롤 높이 통일 |
| **P0** | Pretendard Variable CDN (`index.html`) | 타이포그래피 |
| **P1** | `PanelSearchBar`, `PanelFilterBar` 분리 | 필터 패널 이전 |
| **P1** | `PlaceCard` (사진 + 방문부처) | 핵심 차별점 |
| **P1** | `GradeDot` 원형화 | 디테일 |
| **P1** | `community-topbar` 제거, 브레이크포인트 통일 | 일관성 |
| **P2** | `SkeletonCard` 로딩 상태 | 체감 속도 |
| **P2** | `AdSlot` (카드 5개마다) | 수익화 |
| **P2** | CSS View Transitions 페이지 전환 | 연속성 완성 |
| **P3** | 검색 자연어 파싱 강화 | 핵심 플로우 |
| **P3** | 카카오맵 Place API 사진 연동 | PlaceCard 완성 |
| **P3** | 포커스 링 / 접근성 정리 | 완성도 |
