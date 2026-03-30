export default function BrandMark({ compact = false }) {
  return (
    <span className="brand-mark">
      <span className="brand-mark__icon" aria-hidden="true">
        <span className="brand-mark__prompt">&gt;_</span>
      </span>
      {!compact ? <span className="brand-mark__label">Krud AI</span> : null}
    </span>
  );
}
