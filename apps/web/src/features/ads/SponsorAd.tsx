type SponsorAdProps = {
  variant?: 'inline' | 'rail' | 'banner';
};

export function SponsorAd({ variant = 'inline' }: SponsorAdProps) {
  const text = (import.meta.env.VITE_AD_SLOT_TEXT as string | undefined)?.trim() || '광고 문의: wylee0806@naver.com';
  const url = (import.meta.env.VITE_AD_SLOT_URL as string | undefined)?.trim() || 'mailto:wylee0806@naver.com';
  return (
    <a className={`sponsor-ad sponsor-ad-${variant}`} href={url} target={url.startsWith('http') ? '_blank' : undefined} rel="noreferrer">
      <span>AD</span>
      <strong>{text}</strong>
    </a>
  );
}

