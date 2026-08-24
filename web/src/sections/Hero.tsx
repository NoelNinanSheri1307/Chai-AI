import React from 'react';

export const Hero: React.FC = () => {
  return (
    <section
      style={{
        paddingTop: '3.5rem',
        paddingBottom: '5.5rem',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div className="chai-container">
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(12, 1fr)',
            gap: '2.5rem',
            alignItems: 'center',
          }}
        >
          {/* Left Editorial Copy */}
          <div
            style={{
              gridColumn: 'span 12',
            }}
            className="hero-text-col"
          >
            <div style={{ marginBottom: '1.25rem' }}>
              <span className="forensic-badge">
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--chai-terracotta)' }} />
                Authenticity & Forensic Image Inspection
              </span>
            </div>

            <h1
              className="font-display"
              style={{
                fontSize: 'clamp(2.5rem, 5vw, 4.25rem)',
                lineHeight: 1.12,
                color: 'var(--chai-brown)',
                marginBottom: '1.5rem',
                letterSpacing: '-0.01em',
              }}
            >
              Not every image tells the whole story.
            </h1>

            <p
              style={{
                fontSize: 'clamp(1.05rem, 1.3vw, 1.25rem)',
                lineHeight: 1.65,
                color: 'var(--chai-coffee)',
                marginBottom: '2.25rem',
                maxWidth: '540px',
              }}
            >
              Chai AI examines digital images for signs of synthetic generation and forensic characteristics — providing an authenticity assessment alongside the supporting evidence behind it.
            </p>

            {/* CTAs */}
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'center',
                gap: '0.85rem',
                marginBottom: '2.25rem',
              }}
            >
              <a
                href="/downloads/ChaiAI.apk"
                download="ChaiAI.apk"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.65rem',
                  backgroundColor: 'var(--chai-terracotta)',
                  color: '#F8F3E8',
                  padding: '0.85rem 1.65rem',
                  borderRadius: '4px',
                  textDecoration: 'none',
                  fontSize: 'clamp(0.9rem, 2.5vw, 1rem)',
                  fontWeight: 500,
                  letterSpacing: '0.02em',
                  boxShadow: '0 4px 14px rgba(169, 87, 61, 0.28)',
                  transition: 'all 0.2s ease',
                  flexGrow: 1,
                  maxWidth: '360px',
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--chai-terracotta-hover)';
                  e.currentTarget.style.transform = 'translateY(-1px)';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--chai-terracotta)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7 10 12 15 17 10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                <span>Download Chai AI</span>
                <span className="font-mono" style={{ fontSize: '0.72rem', opacity: 0.85, paddingLeft: '0.2rem' }}>
                  [APK]
                </span>
              </a>

              <a
                href="#features"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  backgroundColor: 'transparent',
                  color: 'var(--chai-brown)',
                  border: '1px solid var(--chai-border)',
                  padding: '0.85rem 1.4rem',
                  borderRadius: '4px',
                  textDecoration: 'none',
                  fontSize: 'clamp(0.88rem, 2.2vw, 0.95rem)',
                  letterSpacing: '0.02em',
                  transition: 'all 0.2s',
                  flexGrow: 1,
                  maxWidth: '360px',
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.borderColor = 'var(--chai-brown)';
                  e.currentTarget.style.backgroundColor = 'rgba(43, 33, 27, 0.04)';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.borderColor = 'var(--chai-border)';
                  e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                <span>See how it works</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </a>
            </div>

            {/* Specimen Telemetry Strip */}
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'center',
                gap: '1rem 1.5rem',
                borderTop: '1px solid var(--chai-border-subtle)',
                paddingTop: '1.25rem',
              }}
            >
              <div>
                <span className="font-mono" style={{ fontSize: '0.68rem', color: 'var(--chai-muted-brown)', display: 'block', textTransform: 'uppercase' }}>
                  Architecture
                </span>
                <span style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--chai-coffee)' }}>
                  Sightengine + Chai Forensics
                </span>
              </div>
              <div style={{ width: '1px', height: '24px', backgroundColor: 'var(--chai-border)' }} />
              <div>
                <span className="font-mono" style={{ fontSize: '0.68rem', color: 'var(--chai-muted-brown)', display: 'block', textTransform: 'uppercase' }}>
                  Principle
                </span>
                <span style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--chai-coffee)' }}>
                  Supporting Evidence, Not Absolute Proof
                </span>
              </div>
            </div>
          </div>

          {/* Right Clean Specimen Visual */}
          <div
            style={{
              gridColumn: 'span 12',
            }}
            className="hero-visual-col"
          >
            <div
              className="specimen-card"
              style={{
                borderRadius: '8px',
                padding: 'clamp(0.75rem, 2vw, 1rem)',
                border: '1px solid var(--chai-border)',
                background: 'linear-gradient(145deg, #F8F3E8 0%, #EFE5D3 100%)',
              }}
            >
              {/* Image Viewport */}
              <div
                style={{
                  position: 'relative',
                  width: '100%',
                  height: 'clamp(240px, 42vw, 340px)',
                  borderRadius: '6px',
                  overflow: 'hidden',
                  backgroundColor: '#201A16',
                }}
              >
                <img
                  src="/images/AstronautVenusApple.png"
                  alt="Forensic Image Specimen"
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                  }}
                />

                {/* Subtle Scan Line */}
                <div
                  className="animate-scan"
                  style={{
                    position: 'absolute',
                    left: 0,
                    right: 0,
                    height: '2px',
                    backgroundColor: 'rgba(235, 120, 80, 0.85)',
                    boxShadow: '0 0 10px rgba(235, 120, 80, 0.7)',
                    pointerEvents: 'none',
                  }}
                />

                {/* Authentic Assessment Pill */}
                <div
                  style={{
                    position: 'absolute',
                    bottom: '12px',
                    left: '12px',
                    backgroundColor: 'rgba(32, 26, 22, 0.92)',
                    backdropFilter: 'blur(8px)',
                    border: '1px solid rgba(169, 87, 61, 0.4)',
                    borderRadius: '4px',
                    padding: '6px 10px',
                  }}
                >
                  <span className="font-mono" style={{ fontSize: '0.6rem', color: '#DFD0B8', display: 'block' }}>
                    CLASSIFICATION
                  </span>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--chai-terracotta)' }}>
                    AI Generated
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @media (min-width: 992px) {
          .hero-text-col {
            grid-column: span 7 !important;
          }
          .hero-visual-col {
            grid-column: span 5 !important;
          }
        }
      `}</style>
    </section>
  );
};

