type SponsorAdProps = {
  variant?: 'inline' | 'rail' | 'banner';
};

export function SponsorAd({ variant = 'inline' }: SponsorAdProps) {
  const text = (import.meta.env.VITE_AD_SLOT_TEXT as string | undefined)?.trim() || '광고 영역';
  const url = (import.meta.env.VITE_AD_SLOT_URL as string | undefined)?.trim();
  const content = (
    <>
      <span>AD</span>
      <strong>{text}</strong>
    </>
  );

  if (url) {
    return (
      <a className={`sponsor-ad sponsor-ad-${variant}`} href={url} target={url.startsWith('http') ? '_blank' : undefined} rel="noreferrer">
        {content}
      </a>
    );
  }

  return (
    <div className={`sponsor-ad sponsor-ad-${variant}`} aria-label="광고 영역">
      {content}
    </div>
  );
}
