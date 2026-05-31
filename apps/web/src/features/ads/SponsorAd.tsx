import { safeExternalUrl } from '../../shared/safeExternalUrl';

type SponsorAdProps = {
  variant?: 'inline' | 'rail' | 'banner';
};

export function SponsorAd({ variant = 'inline' }: SponsorAdProps) {
  const text = (import.meta.env.VITE_AD_SLOT_TEXT as string | undefined)?.trim() || '광고 영역';
  const url = safeExternalUrl(import.meta.env.VITE_AD_SLOT_URL as string | undefined);
  const content = (
    <>
      <span>AD</span>
      <strong>{text}</strong>
    </>
  );

  if (url) {
    return (
      <a className={`sponsor-ad sponsor-ad-${variant}`} href={url} target="_blank" rel="noopener noreferrer">
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
