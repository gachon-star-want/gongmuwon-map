export function SkeletonCard() {
  return (
    <div className="skeleton-card" aria-hidden>
      <div className="skeleton skeleton-grade" />
      <div className="skeleton-body">
        <div className="skeleton skeleton-line-title" />
        <div className="skeleton skeleton-line-sub" />
        <div className="skeleton skeleton-line-badge" />
      </div>
    </div>
  );
}
