/** Marchio Proxima, ripreso dalla landing page in 05-branding. */
export default function Logo({ dimensione = 34 }: { dimensione?: number }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.7rem' }}>
      <svg
        width={dimensione}
        height={dimensione}
        viewBox="0 0 36 36"
        fill="none"
        aria-hidden="true"
        focusable="false"
      >
        <rect
          x="10"
          y="4"
          width="16"
          height="28"
          rx="1.5"
          stroke="var(--navy)"
          strokeWidth="1.8"
          fill="none"
        />
        <rect
          x="2"
          y="20"
          width="5"
          height="9"
          rx="1"
          stroke="var(--navy)"
          strokeWidth="1.2"
          fill="none"
          transform="rotate(-12 4.5 24.5)"
        />
        <rect
          x="3.5"
          y="12"
          width="5"
          height="9"
          rx="1"
          stroke="var(--oro)"
          strokeWidth="1.2"
          fill="none"
          transform="rotate(-8 6 16.5)"
        />
      </svg>
      <span
        style={{
          fontFamily: 'var(--font-display)',
          fontWeight: 600,
          fontSize: '1.05rem',
          letterSpacing: '0.18em',
          textTransform: 'uppercase',
          color: 'var(--navy)',
        }}
      >
        Proxima
      </span>
    </span>
  );
}
