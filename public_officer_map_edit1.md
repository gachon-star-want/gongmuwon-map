# Public Officer Map UX & Code Issues Report (v1)

이 문서는 에이전트 3개(Android 사용자, iOS Safari 사용자, Desktop 사용자)가 프로젝트의 전체 코드베이스(`PlaceExplorer.tsx`, `BottomSheet.tsx`, `PlaceDetails.tsx`, `styles.css` 등)를 교차 리뷰하여 도출한 UX 불편 사항 및 크리티컬한 버그 리포트입니다. 다른 AI가 이 문서를 읽고 즉시 전체 코드를 패치할 수 있도록 구체적인 파일 경로, 코드 라인 및 구체적인 해결 가이드를 명시합니다.

---

## [목차]
1. **[공통/모바일] 바텀 시트 드래그 제스처 및 클릭 로직 결함**
2. **[공통/모바일] 더블 팝업/모달 겹침 및 Z-Index 충돌**
3. **[iOS Safari] Safe-Area 영역 침범 및 스크롤 바운스 버그**
4. **[Android/Mobile] 키보드 활성화 시 뷰포트 Resizing으로 인한 입력 불가 현상**
5. **[Desktop] CSS 구문 오류 (크리티컬)**
6. **[Desktop] 지도 중심 좌표 가려짐(오프셋 누락) 및 빈 공간 클릭 차단**
7. **[Desktop/공통] 이벤트 버블링 및 애니메이션 뚝 끊김 현상**

---

## 1. [공통/모바일] 바텀 시트 드래그 제스처 및 클릭 로직 결함

### 1-1. 스와이프 제스처 기능 부재 (아래로 쓸어내려도 비작동)
* **파일 위치**: [BottomSheet.tsx](file:///Users/lee_wonyoung/developer/public_officer_map/apps/web/src/features/place-explorer/panels/BottomSheet.tsx#L83-L90)
* **현상**: 모바일 화면에서 드래그 핸들(`.sheet-handle`)을 아래로 스와이프해도 시트 높이가 전혀 줄어들지 않고 무반응입니다.
* **원인**: `.sheet-handle`에 터치 제스처(`onTouchStart`, `onTouchMove`, `onTouchEnd`) 또는 포인터 이벤트 리스너가 구현되어 있지 않고, 정적 HTML `<button>`의 단순 `onClick`만 걸려 있습니다.
* **해결 제안**:
  `react-swipeable`과 같은 제스처 라이브러리를 적용하거나, 아래와 같이 경량 `onTouch` 드래그 인식 핸들러를 도입하여 터치 좌표 변화에 따라 `onSizeChange('peek' | 'mid' | 'full')`를 트리거하도록 개선해야 합니다.

### 1-2. 아래 방향 화살표(꺾쇠) 클릭 오작동
* **파일 위치**: [BottomSheet.tsx](file:///Users/lee_wonyoung/developer/public_officer_map/apps/web/src/features/place-explorer/panels/BottomSheet.tsx#L87)
* **현상**: 바텀 시트가 `mid` 상태(기본 상태)일 때, 아래 방향을 가리키는 꺾쇠(`ChevronDown`) 아이콘을 누르면 시트가 닫히거나 내려가는 것이 아니라, 거꾸로 화면 전체(`full`) 크기로 확장됩니다.
* **원인**:
  ```tsx
  onClick={() => onSizeChange(size === 'full' ? 'mid' : 'full')}
  ```
  현재 단순 토글 형태로 코딩되어 있어, `mid` 상태에서 누를 경우 `full` 상태로 변화하게 됩니다.
* **해결 제안**:
  * `size === 'full'` 상태에서 누르면 `mid`로 축소.
  * `size === 'mid'` 상태에서 누르면 `peek`(최소화) 또는 닫기(`clearSelected` 호출 등)로 상태가 변하도록 세부 토글 로직을 세분화해야 합니다.
  ```tsx
  const handleArrowClick = () => {
    if (size === 'full') onSizeChange('mid');
    else if (size === 'mid') onSizeChange('peek');
  };
  ```

### 1-3. 터치 타겟(영역) 부족
* **파일 및 라인**: [styles.css](file:///Users/lee_wonyoung/developer/public_officer_map/apps/web/src/features/place-explorer/styles.css#L682-L693)
* **현상**: 모바일 화면에서 드래그 핸들이 너무 작아 손가락으로 누르거나 조작하기가 매우 힘듭니다.
* **원인**: `.sheet-handle`의 높이가 `28px`에 불과하고 내부 Lucide 아이콘이 `size={16}`으로 작게 박혀 있어 모바일 터치 최소 규격(44px~48px)에 못 미칩니다.
* **해결 제안**:
  `.sheet-handle`의 패딩/높이를 `44px` 이상 확보하고, 실제 핸들 바 이미지는 `before/after` 가상 요소로 작게 표현하여 터치 영역만 확장해야 합니다.

---

## 2. [공통/모바일] 더블 팝업/모달 겹침 및 Z-Index 충돌

### 2-1. 모달 활성화 시 바텀 시트 및 바텀 네비게이션 미노출 처리 누락
* **파일 위치**: [PlaceExplorer.tsx](file:///Users/lee_wonyoung/developer/public_officer_map/apps/web/src/features/place-explorer/PlaceExplorer.tsx#L580-L615)
* **현상**: 모바일에서 식당 상세 정보를 보던 중 "정보 수정·삭제 요청" 모달이나 "폐업 신고" 모달을 띄우면, 맵 오버레이 중앙에 모달이 뜸과 동시에 **그 뒤쪽 배경에 바텀 시트와 하단 네비게이션 바가 그대로 남아 조작을 방해**하고 레이아웃이 겹칩니다.
* **원인**: 모달의 오픈 상태 플래그(`reportOpened` 또는 `closureOpened`)가 참일 때 하단 패널들(`BottomSheet`, `BottomNav`)을 조건부로 렌더링에서 빼거나 숨기지 않고 항상 렌더링하고 있습니다.
* **해결 제안**:
  모달이 오픈되어 있을 때 바텀 시트의 size를 `'peek'`로 자동 축소하거나, `display: none` 처리를 하도록 제어 상태를 연동합니다.
  ```tsx
  const isAnyModalOpen = reportOpened || closureOpened || authOpened;
  // BottomSheet에 hide={isAnyModalOpen} 등의 prop을 넘겨 CSS로 감추거나 언마운트 처리
  ```

### 2-2. Z-Index 레이어 샌드위치 현상
* **파일 및 라인**: [styles.css](file:///Users/lee_wonyoung/developer/public_officer_map/apps/web/src/features/place-explorer/styles.css#L658) (`bottom-sheet` z-index: 160)
* **현상**: 모바일 바텀 시트의 z-index가 지나치게 높게 설정되어 있어, 화면 중앙에 뜨는 다이얼로그나 로그인 모달(`AuthModal`)의 배경 마스크 레이어 위로 바텀 시트 내부의 특정 버튼이나 요소가 뚫고 올라옵니다.
* **해결 제안**:
  Mantine Modal이 최고 레벨의 레이어(`z-index: 200` 이상)에서 열리도록 Mantine Provider 설정을 맞추거나, 모달 활성화 시 바텀 시트의 `z-index`를 동적으로 낮추어야 합니다.

---

## 3. [iOS Safari] Safe-Area 영역 침범 및 스크롤 바운스 버그

### 3-1. 하단 네비게이션과 바텀 시트의 강제 8px 겹침
* **파일 및 라인**: [styles.css](file:///Users/lee_wonyoung/developer/public_officer_map/apps/web/src/features/place-explorer/styles.css#L1341)
* **현상**: 아이폰에서 볼 때 바텀 시트의 최하단 경계면과 하단 탭 바(네비게이션)의 상단이 8px가량 서로 겹쳐서 글자가 뭉개져 보입니다.
* **원인**:
  * 바텀 시트 배치: `bottom: calc(64px + env(safe-area-inset-bottom, 0px))`
  * 하단 탭 바 배치: `bottom: 8px; min-height: calc(64px + env(safe-area-inset-bottom, 0px))`
  * 탭 바가 8px 떠 있는 상태에서 시트는 64px 공간만 고려하고 있어, 두 요소가 물리적으로 8px만큼 침범하게 됩니다.
* **해결 제안**:
  바텀 시트의 bottom 오프셋 수식을 네비게이션 바의 정확한 플로팅 높이(`72px + env(safe-area-inset-bottom)`)에 일치하도록 수정해야 합니다.
  ```css
  .bottom-sheet {
    bottom: calc(72px + env(safe-area-inset-bottom, 0px));
  }
  ```

### 3-2. 노치(Notch) 및 홈 인디케이터 터치 충돌
* **현상**: 
  1. 가로 회전(Landscape) 시 기기의 노치/다이내믹 아일랜드 영역에 검색 바나 정보 팝업이 파묻혀 가려집니다.
  2. 홈 스크린으로 나가는 화면 하단 홈 인디케이터(바) 근처를 터치할 때 네비게이션이 눌리지 않고 iOS 시스템 제스처가 동작합니다.
* **원인**: `env(safe-area-inset-left / right / bottom)` 인셋 계산이 `left: 12px`, `bottom: 8px` 등으로 하드코딩되어 브라우저 인셋 규칙을 누락했습니다.
* **해결 제안**:
  모든 모바일 고정 요소에 대해 safe-area 변수를 더해줍니다.
  ```css
  .mobile-search {
    left: calc(12px + env(safe-area-inset-left, 0px));
    right: calc(12px + env(safe-area-inset-right, 0px));
  }
  .bottom-nav {
    bottom: calc(8px + env(safe-area-inset-bottom, 0px));
  }
  ```

### 3-3. iOS 스크롤 바운스 버블링(Chaining) 현상
* **현상**: 바텀 시트 목록을 위아래로 끝까지 스크롤하면 바텀 시트 내부만 튕기는 것이 아니라 뒷배경의 전체 맵과 브라우저 창 전체가 흔들리며 스크롤됩니다.
* **해결 제안**:
  모바일 스크롤 컨테이너에 바운스 전파를 막는 CSS를 명시합니다.
  ```css
  .sheet-content, .detail-content, .mobile-panel {
    overscroll-behavior: contain;
    -webkit-overflow-scrolling: touch; /* 구형 iOS 관성 스크롤 보장 */
  }
  ```

---

## 4. [Android/Mobile] 키보드 활성화 시 뷰포트 Resizing으로 인한 입력 불가 현상

### 4-1. 입력 창 포커스 시 모달/창 밀림 및 찌그러짐 현상
* **현상**: 안드로이드 휴대전화에서 검색창이나 문의 모달의 이메일/내용 입력란을 터치하면 가상 키보드가 올라오면서 모달이 찌그러지거나 완료/제출 버튼이 키보드 아래로 완전히 숨어버립니다.
* **원인**: 안드로이드 크롬 등은 키보드가 올라오면 뷰포트의 물리적 크기(`dvh` 또는 `vh`)를 축소시킵니다. 전체 화면 컨테이너가 `100dvh`에 꽉 차 있어 내부 패널의 배치 및 정렬이 무너지며 스크롤 영역이 아닌 영역까지 찌그러집니다.
* **해결 제안**:
  키보드가 올라왔을 때 스크롤이 원활하게 작동하도록 모달 본문(`Mantine Modal` 내의 content)에 `max-height`를 지정하고 `overflow-y: auto`를 명시적으로 적용하며, 모달 컨테이너의 정렬을 `centered` 대신 모바일에서는 `top: 10%` 등으로 유연하게 배치해야 합니다.

---

## 5. [Desktop] CSS 구문 오류 (크리티컬)

### 5-1. 중괄호 미닫힘 버그 (Unclosed CSS Selector)
* **파일 위치**: [styles.css](file:///Users/lee_wonyoung/developer/public_officer_map/apps/web/src/features/place-explorer/styles.css#L1125-L1128)
* **코드 내용**:
  ```css
  .detail-content {
    padding: 20px;
    overflow-y: auto;
    flex: 1;

  .detail-title h2 {
    font-size: 25px;
    /* ... */
  ```
* **현상**: `.detail-content` 스타일 선언 뒤에 닫는 중괄호(`}`)가 누락되어 있습니다. 이로 인해 브라우저가 이후의 스타일(예: 미디어 쿼리나 다른 데스크톱 오버레이 스타일) 전체를 정상적으로 해석하지 못하고 파싱 에러를 유발합니다.
* **해결 제안**:
  반드시 `.detail-content { padding: 20px; ... }` 로 중괄호를 정상적으로 닫아주어야 합니다.

---

## 6. [Desktop] 지도 중심 좌표 가려짐(오프셋 누락) 및 빈 공간 클릭 차단

### 6-1. 마커 선택 시 상세 패널 밑으로 마커가 가려지는 현상
* **파일 위치**: [MapCanvas.tsx](file:///Users/lee_wonyoung/developer/public_officer_map/apps/web/src/features/place-explorer/map/MapCanvas.tsx#L218-L220)
* **현상**: 지도에서 식당 핀을 누르면 화면 중앙으로 지도가 이동하는데, 우측에 넓게 자리잡은 목록 패널(`392px`)과 상세 패널(`420px`)이 지도의 우측 영역 **852px**을 통째로 덮어버려서 마커가 이 패널들 아래에 가려져 보이지 않게 됩니다.
* **원인**: `map.panTo(coords)`가 지도의 기하학적 중심점을 기준으로 마커를 정가운데에 배치하기 때문에 발생합니다. 우측 패널들이 가리는 영역만큼 중심 좌표를 좌측으로 오프셋(보정)해주지 않고 있습니다.
* **해결 제안**:
  카카오맵 API의 `panBy(dx, dy)` 함수를 사용해 지도를 마커 좌표로 이동시킨 후, 우측 패널의 가로 폭 절반만큼 지도를 좌측으로 부드럽게 이동(`panBy(200, 0)`)시키거나, 픽셀 좌표를 계산해 보정된 중심점을 구한 뒤 `panTo`로 이동시켜야 합니다.

### 6-2. 데스크톱 오버레이 컨테이너가 지도 클릭을 차단하는 현상
* **파일 및 라인**: [styles.css](file:///Users/lee_wonyoung/developer/public_officer_map/apps/web/src/features/place-explorer/styles.css#L849-L855) (`.desktop-controls`)
* **현상**: 상단 검색바 주변의 비어 있는 하늘 공간(지도가 보이는 투명 영역)을 마우스로 드래그하여 지도를 움직이려 해도, 드래그가 먹히지 않고 클릭이 무시됩니다.
* **원인**: `.desktop-controls` 오버레이 컨테이너가 `left: 20px; right: 20px;`로 좌우로 길게 펼쳐져 있어, 마우스 이벤트를 가로채고 지도로 이벤트를 흘려보내지 않기 때문입니다.
* **해결 제안**:
  `.desktop-controls` 컨테이너 자체에는 마우스 이벤트를 통과시키는 CSS를 적용하고, 하위 실제 버튼/검색창 요소에만 다시 이벤트를 활성화시켜야 합니다.
  ```css
  .desktop-controls {
    pointer-events: none; /* 컨테이너는 통과 */
  }
  .desktop-controls > * {
    pointer-events: auto; /* 자식 요소는 다시 조작 가능 */
  }
  ```

---

## 7. [Desktop/공통] 이벤트 버블링 및 애니메이션 뚝 끊김 현상

### 7-1. Escape 키 입력 시 인풋 포커스 무시 현상
* **파일 위치**: [PlaceExplorer.tsx](file:///Users/lee_wonyoung/developer/public_officer_map/apps/web/src/features/place-explorer/PlaceExplorer.tsx#L236-L254)
* **현상**: 검색창에 검색어를 입력하던 중 오타를 지우려 하거나 취소하기 위해 `Escape` 키를 누르면, 인풋 창의 포커스만 풀리는 것이 아니라 열려 있던 장소 상세 패널이나 목록이 통째로 닫혀버립니다.
* **원인**: 글로벌 키다운 리스너가 이벤트가 발생한 타겟 요소가 `input` 또는 `textarea` 인지 체크하지 않고 무조건 화면 초기화 및 닫기 기능을 수행합니다.
* **해결 제안**:
  `Escape` 이벤트 핸들러 시작부에 타겟 요소 검사 조건을 추가합니다.
  ```typescript
  if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
    return; // 입력 필드 안에서 누른 것이면 글로벌 닫기 이벤트 무시
  }
  ```

### 7-2. 상세창이 닫힐 때 트랜지션 애니메이션이 먹히지 않고 바로 사라지는 현상
* **파일 위치**: [PlaceExplorer.tsx](file:///Users/lee_wonyoung/developer/public_officer_map/apps/web/src/features/place-explorer/PlaceExplorer.tsx#L564-L578)
* **현상**: 상세 카드의 닫기 버튼을 누르면 우측으로 슬라이딩 아웃되는 부드러운 애니메이션이 보여야 하는데, 팝업창이 즉시 깜빡이듯 뚝 사라집니다.
* **원인**:
  ```tsx
  {selectedPlace ? (
    <aside className="detail-drawer ...">
      <PlaceDetails ... />
    </aside>
  ) : null}
  ```
  `selectedPlace`가 null이 되는 순간 리액트가 `<aside>` 엘리먼트 자체를 즉시 언마운트(제거)하므로 CSS 트랜지션이 작동할 시간적 여유가 없습니다.
* **해결 제안**:
  물리적 DOM은 렌더링을 유지하고, `selectedPlace` 존재 여부에 따라 클래스명(`.active` 또는 `.open`)만 바꾸어 CSS 상에서 `right: -500px` 등으로 밀어내는 방식으로 슬라이딩 전환을 제어해야 합니다.
  ```tsx
  <aside className={`detail-drawer desktop-layer ${selectedPlace ? 'active' : ''} ...`}>
    {selectedPlace && <PlaceDetails ... />}
  </aside>
  ```

### 7-3. 커버 이미지 호버 효과 범위 지정 결함
* **파일 및 라인**: [styles.css](file:///Users/lee_wonyoung/developer/public_officer_map/apps/web/src/features/place-explorer/styles.css#L1095-L1097)
* **현상**: 상세정보 카드 내의 임의의 영역(예: 스크롤 영역, 하단 버튼)에 마우스 커서를 갖다 대거나 조작할 때마다 최상단의 식당 썸네일/커버 이미지가 불필요하게 웅성거리며 확대/축소됩니다.
* **원인**: 호버 감지 대상 셀렉터가 카드 전체인 `.detail-drawer:hover`로 되어 있어, 카드 내의 모든 마우스 활동에 대해 이미지의 스케일 줌인이 트리거됩니다.
* **해결 제안**:
  커버 이미지 영역 자체에 호버되었을 때만 확대되도록 셀렉터를 좁힙니다.
  ```css
  .detail-header-wrapper:hover .detail-cover-image {
    transform: scale(1.05);
  }
  ```
