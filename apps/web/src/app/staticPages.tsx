import { Anchor, AppShell, Button, Group, Text, Title } from '@mantine/core';
import { AlertTriangle, Code2, FileText, Info, MapPin, ShieldCheck } from 'lucide-react';
import mascotLogo from '../assets/officer-mascot-logo.png';

type StaticPath = '/about' | '/privacy' | '/terms' | '/disclaimer' | '/legal' | '/api';

type StaticLink = {
  label: string;
  href: string;
};

type StaticSection = {
  title: string;
  lines: string[];
  links?: StaticLink[];
};

const footerOperatorText = '공공누리 제1유형 · 출처: 서울특별시 정보소통광장 외 수도권·대전·전남·충남 지자체·의회 공식 공개자료';
const footerOperatorInfo = '운영: 이원영/WonYoungLee · wylee0806@naver.com · 010-7133-0806 · 경기도 성남시 분당구 수내로 39';
const trustBanner = '공공기관 의무 공개자료(업무추진비) 기반, 공공누리 제1유형 출처 표시, 맛·품질 점수 아님, 댓글·평점·후기 없음';

export function StaticPage({ path }: { path: string }) {
  const page = staticPageContent(path as StaticPath);
  const PageIcon = page.icon;
  return (
    <AppShell header={{ height: 64 }} padding={0}>
      <AppShell.Header className="app-header">
        <Group h="100%" px="lg" justify="space-between" wrap="nowrap">
          <Group gap="sm" wrap="nowrap">
            <img className="static-logo" src={mascotLogo} alt="" aria-hidden />
            <PageIcon className="static-page-icon" size={20} aria-hidden />
            <Title order={1}>{page.title}</Title>
          </Group>
          <Button component="a" href="/" variant="subtle" leftSection={<MapPin size={16} />}>
            지도
          </Button>
        </Group>
      </AppShell.Header>
      <AppShell.Main className="legal-main">
        <article className="legal-page">
          <Text c="dimmed">{page.lead}</Text>
          {page.sections.map((section) => (
            <section key={section.title} className="legal-section">
              <Title order={2}>{section.title}</Title>
              {section.lines.map((line) => (
                <Text key={line}>{line}</Text>
              ))}
              {section.links ? (
                <Group gap="md" mt="sm">
                  {section.links.map((link) => (
                    <Button key={link.href} component="a" href={link.href} variant="light">
                      {link.label}
                    </Button>
                  ))}
                </Group>
              ) : null}
            </section>
          ))}
        </article>
        <footer className="site-footer static-footer">
          <span>{footerOperatorText}</span>
          <span>{footerOperatorInfo}</span>
          <nav aria-label="문서 링크">
            <Anchor href="/about">서비스 소개</Anchor>
            <Anchor href="/terms">이용약관</Anchor>
            <Anchor href="/privacy">개인정보처리방침</Anchor>
            <Anchor href="/disclaimer">면책조항</Anchor>
            <Anchor href="/legal">데이터 출처</Anchor>
            <Anchor href="/api">API 문서</Anchor>
          </nav>
        </footer>
      </AppShell.Main>
    </AppShell>
  );
}

function staticPageContent(path: StaticPath) {
  if (path === '/privacy') {
    return {
      title: '개인정보처리방침',
      icon: ShieldCheck,
      lead: '공무원맵은 회원가입 없이 이용할 수 있으며, 신고 처리에 필요한 최소 정보만 사용합니다.',
      sections: [
        {
          title: '수집 항목',
          lines: [
            '폐업 신고 중복 방지를 위한 익명 브라우저 식별자, 정보 수정·삭제 요청 시 사용자가 입력한 이메일을 처리합니다.',
            '방문 기록 데이터는 법령에 따라 공개된 업무추진비 집행내역을 가공한 것이며, 일반직 공무원 실명은 적재 단계에서 마스킹합니다.',
          ],
        },
        {
          title: '이용 목적과 보관',
          lines: [
            '닉네임/비밀번호는 게시글·댓글 작성과 좋아요/싫어요 반응 권한 확인에만 사용하며, 공식 등급·방문 통계에는 반영하지 않습니다.',
            '익명 식별자는 중복 신고 차단에 사용하며 90일 단위 삭제를 원칙으로 합니다.',
            '이메일은 요청 회신과 분쟁 대응에만 사용하고, 응답 완료 후 30일 보관을 원칙으로 합니다.',
          ],
        },
        {
          title: '처리 위탁',
          lines: [
            '서비스 운영에는 Vercel, Neon, Cloudflare R2, Resend가 사용될 수 있습니다.',
            '개인정보 보호 책임자는 이원영/WonYoungLee이며 연락처는 wylee0806@naver.com입니다.',
          ],
        },
      ],
    };
  }
  if (path === '/terms') {
    return {
      title: '이용약관',
      icon: FileText,
      lead: '공무원맵은 공무원 업무추진비 공개자료를 기반으로 방문 빈도 신호를 보여주는 무료 정보 지도입니다.',
      sections: [
        {
          title: '서비스 제공',
          lines: [
            '데이터는 법령상 공개된 공무원 업무추진비 자료에서 파생되며 정확성을 보증하지 않습니다.',
            '이용자는 원본 출처와 공공누리 제1유형 조건을 함께 표기해야 합니다.',
          ],
        },
        {
          title: '금지 행위',
          lines: [
            '공무원 개인의 식습관·성향·부정행위를 단정하거나 맛·품질을 평가·등급화하는 방식의 이용을 금지합니다.',
            '서비스 안정성을 해치는 자동화 요청, 권리침해 목적의 재게시, 출처 삭제 재배포를 금지합니다.',
          ],
        },
        {
          title: '분쟁',
          lines: [
            '정보 수정·삭제 요청은 접수 즉시 임시 비공개 처리하고 72시간 내 검토합니다.',
            '분쟁은 대한민국 법령에 따르며 운영자 주소지 관할 법원을 1심 관할로 합니다.',
          ],
        },
      ],
    };
  }
  if (path === '/disclaimer') {
    return {
      title: '면책조항',
      icon: AlertTriangle,
      lead: trustBanner,
      sections: [
        {
          title: '데이터 성격',
          lines: [
            '본 서비스는 정보공개법과 업무추진비 공개기준에 따라 공개된 자료를 가공·재공개합니다.',
            '식당의 개·폐업, 영업시간, 가격은 최신 상태와 다를 수 있으므로 방문 전 별도 확인이 필요합니다.',
          ],
        },
        {
          title: '표현의 한계',
          lines: [
            '업무추진비는 법령상 허용된 공무 집행의 한 형태이며, 본 서비스는 부정행위나 비위를 암시하지 않습니다.',
            '식당 상세에는 사용자 댓글·평점·후기를 붙이지 않으며, 별도 커뮤니티는 식당 좌표와 분리해 운영합니다.',
          ],
        },
        {
          title: '정정 요청',
          lines: [
            '정보 수정·삭제 요청은 식당 상세 패널 또는 운영자 이메일로 접수할 수 있습니다.',
            '요청이 접수되면 해당 정보는 자동으로 임시 비공개 처리됩니다.',
          ],
        },
      ],
    };
  }
  if (path === '/legal') {
    return {
      title: '데이터 출처와 법적 근거',
      icon: ShieldCheck,
      lead: trustBanner,
      sections: [
        {
          title: '출처 표시',
          lines: [
            '주요 출처는 서울특별시 정보소통광장, 서울시의회, 25개 자치구청, 25개 자치구의회 공개 게시판입니다.',
            '2026년 6월 1일 기준 전국 출처 등록부는 P1-P4 2,200개 기관 중 137개 공식 출처 검증 완료, 1,996개 검증 대기, 67개 법적 검토 보류 상태를 코드에서 추적합니다.',
            '공공누리 제1유형 조건에 따라 출처를 표시하고, 서비스 전 페이지와 API 문서에 데이터 출처를 명시합니다.',
          ],
        },
        {
          title: '수도권 검증 출처',
          lines: [
            '경기 검증 출처: 안양시청, 의정부시청, 동두천시청, 안산시청, 부천시청, 고양시청, 과천시청, 김포시청, 하남시청, 광주시청, 가평군청, 양평군청, 오산시청, 의왕시청, 안성시청, 경기도의회, 수원시의회, 성남시의회, 동두천시의회, 고양시의회, 용인시의회, 부천시의회, 안성시의회, 김포시의회, 화성시의회, 하남시의회, 포천시의회 공식 공개자료.',
            '인천 검증 출처: 인천광역시청, 인천광역시의회, 중구청, 중구의회, 동구청, 미추홀구청, 연수구청, 부평구청, 남동구청, 남동구의회, 서구청, 서구의회, 옹진군청, 옹진군의회 공식 공개자료.',
            '비수도권 검증 출처: 대전광역시청, 대전광역시의회, 전라남도청, 서산시청, 곡성군청, 곡성군의회 공식 공개자료.',
            '법적 검토 보류 기관은 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 크롤·적재 대상에서 제외합니다.',
          ],
        },
        {
          title: '표기 정책',
          lines: [
            '선거직 고위공무원은 실명과 직급 표시가 가능하지만, 임명직과 5급 이하 일반직은 부서·직급 중심으로 마스킹합니다.',
            '민간인 동석자는 원칙적으로 마스킹하며, 식당명·주소·일자·금액은 원본 공개 항목으로 표시합니다.',
            trustBanner,
          ],
        },
        {
          title: '운영자',
          lines: [
            '운영자: 이원영/WonYoungLee',
            '이메일: wylee0806@naver.com · 연락처: 010-7133-0806 · 주소: 경기도 성남시 분당구 수내로 39',
            '사업자등록번호: 해당 없음, 개인 운영',
          ],
        },
      ],
    };
  }
  if (path === '/api') {
    return {
      title: 'API 문서',
      icon: Code2,
      lead: trustBanner,
      sections: [
        {
          title: '주요 엔드포인트',
          lines: [
            'GET /api/v1/places: bbox, grade, limit 파라미터로 식당 목록을 조회합니다.',
            'GET /api/v1/places/search: 검색어, 자치구, 등급, 정렬 기반 UI 목록을 조회합니다.',
            'GET /api/v1/regions: 자치구별 식당 수와 지도 중심 좌표를 조회합니다.',
            'GET /api/v1/places/{id}/visits: 원문 링크가 포함된 방문 기록을 조회합니다.',
            'GET/POST /api/v1/places/{id}/reactions: 공식 지표와 분리된 좋아요/싫어요 반응을 조회·저장합니다.',
          ],
          links: [
            { label: 'OpenAPI JSON', href: '/openapi.json' },
            { label: 'llms.txt', href: '/llms.txt' },
          ],
        },
        {
          title: '이용 조건',
          lines: [
            'GET API는 공개 캐시가 적용되며, 데이터 인용 시 원천 자료와 공무원맵 출처를 함께 표시해야 합니다.',
            '등급은 방문 빈도와 부서 다양성 기반 통계 신호이며 맛·품질·비위 판단 근거로 사용할 수 없습니다.',
          ],
        },
      ],
    };
  }
  return {
    title: '서비스 소개',
    icon: Info,
    lead: trustBanner,
    sections: [
      {
        title: '집계 현황',
        lines: [
          '2026년 5월 25일 기준 52개 기관 중 51개 기관이 지도 집계에 반영되어 있습니다.',
          '2026년 6월 1일 기준 전국 출처 등록부는 P1-P4 2,200개 기관 중 137개 공식 출처 검증 완료, 1,996개 검증 대기, 67개 법적 검토 보류 상태를 추적합니다.',
          '중랑구청은 공식 PDF에 장소·가맹점 열이 없어 보조 출처 확보 전까지 지도 집계에서 제외합니다.',
        ],
      },
      {
        title: '등급 산식',
        lines: [
          '점수는 방문 횟수와 고유 부서 수를 함께 반영합니다.',
          '자치구별 백분위 기준으로 강추, 추천, 중립, 신규 라벨을 부여합니다.',
        ],
      },
      {
        title: '서비스 원칙',
        lines: [
          '공식 공개자료 기반의 식당 상세에는 사용자 댓글·평점·후기를 받지 않습니다.',
          trustBanner,
        ],
      },
    ],
  };
}
