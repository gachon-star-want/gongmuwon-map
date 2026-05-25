import { Anchor, AppShell, Button, Group, Text, Title } from '@mantine/core';
import { AlertTriangle, Code2, FileText, Info, MapPin, ShieldCheck } from 'lucide-react';

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

const footerOperatorText = '공공누리 제1유형 · 출처: 서울특별시 정보소통광장 외 51개 기관';
const footerOperatorInfo = '운영: 이원영/WonYoungLee · wylee0806@naver.com · 010-7133-0806 · 경기도 성남시 분당구 수내로 39';

export function StaticPage({ path }: { path: string }) {
  const page = staticPageContent(path as StaticPath);
  const PageIcon = page.icon;
  return (
    <AppShell header={{ height: 64 }} padding={0}>
      <AppShell.Header className="app-header">
        <Group h="100%" px="lg" justify="space-between" wrap="nowrap">
          <Group gap="sm" wrap="nowrap">
            <PageIcon size={21} aria-hidden />
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
      lead: '공무원맵은 공공 공개자료를 시민이 쉽게 탐색할 수 있도록 제공하는 무료 정보 서비스입니다.',
      sections: [
        {
          title: '서비스 제공',
          lines: [
            '데이터는 원문 공개자료, 자동 추출, 카카오 로컬 매칭 결과를 바탕으로 제공되며 정확성을 보증하지 않습니다.',
            '사용자는 데이터 재이용 시 원 출처와 공공누리 제1유형 조건을 함께 확인해야 합니다.',
          ],
        },
        {
          title: '금지 행위',
          lines: [
            '공무원 개인의 식습관·성향을 추론하거나 부정행위를 단정하는 방식의 이용을 금지합니다.',
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
      lead: '등급은 방문 빈도와 부서 다양성에 따른 통계 신호이며 맛·품질·비위 여부를 단정하지 않습니다.',
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
            '사용자 댓글·평점·후기는 v1에서 제공하지 않습니다.',
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
      lead: '공무원맵은 법령상 공개 대상인 업무추진비 집행내역과 공공누리 제1유형 자료를 사용합니다.',
      sections: [
        {
          title: '출처 표시',
          lines: [
            '주요 출처는 서울특별시 정보소통광장, 서울시의회, 25개 자치구청, 25개 자치구의회 공개 게시판입니다.',
            '공공누리 제1유형 조건에 따라 출처를 표시하고, 서비스 전 페이지와 API 문서에 데이터 출처를 명시합니다.',
          ],
        },
        {
          title: '표기 정책',
          lines: [
            '선거직 고위공무원은 실명과 직급 표시가 가능하지만, 임명직과 5급 이하 일반직은 부서·직급 중심으로 마스킹합니다.',
            '민간인 동석자는 원칙적으로 마스킹하며, 식당명·주소·일자·금액은 원본 공개 항목으로 표시합니다.',
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
      lead: '공무원맵은 지도 화면과 동일한 공개 데이터를 REST API와 OpenAPI 3.1 스펙으로 제공합니다.',
      sections: [
        {
          title: '주요 엔드포인트',
          lines: [
            'GET /api/v1/places: bbox, grade, limit 파라미터로 식당 목록을 조회합니다.',
            'GET /api/v1/places/search: 검색어, 자치구, 등급, 정렬 기반 UI 목록을 조회합니다.',
            'GET /api/v1/regions: 자치구별 식당 수와 지도 중심 좌표를 조회합니다.',
            'GET /api/v1/places/{id}/visits: 원문 링크가 포함된 방문 기록을 조회합니다.',
          ],
          links: [
            { label: 'OpenAPI JSON', href: '/openapi.json' },
            { label: 'llms.txt', href: '/llms.txt' },
          ],
        },
        {
          title: '이용 조건',
          lines: [
            'GET API는 공개 캐시가 적용되며, 데이터 인용 시 공무원맵과 원 공공자료 출처를 함께 표시해야 합니다.',
            '등급은 통계 신호이므로 식당 평가나 공무원 비위 판단 근거로 단정해서 사용할 수 없습니다.',
          ],
        },
      ],
    };
  }
  return {
    title: '서비스 소개',
    icon: Info,
    lead: '공무원맵은 서울 52개 기관의 업무추진비 집행내역에서 식당 방문 신호를 추출해 지도에 표시합니다.',
    sections: [
      {
        title: '집계 현황',
        lines: [
          '2026년 5월 25일 기준 52개 기관 중 51개 기관이 지도 집계에 반영되어 있습니다.',
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
          '공식 공개자료만 사용하며 사용자 댓글·평점·후기는 받지 않습니다.',
          '공무원의 부정행위나 식당의 맛을 단정하지 않고, 출처 확인 가능한 방문 빈도 신호만 제공합니다.',
        ],
      },
    ],
  };
}
