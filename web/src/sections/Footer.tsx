import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer
      style={{
        borderTop: '1px solid var(--chai-border)',
        backgroundColor: 'var(--chai-bg)',
        paddingTop: '3.5rem',
        paddingBottom: '3.5rem',
      }}
    >
      <div className="chai-container">
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '2rem',
          }}
        >
          {/* Brand & Mission Statement */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.5rem' }}>
              <img
                src="/app-icon.png"
                alt="Chai AI Logo"
                style={{
                  width: '26px',
                  height: '26px',
                  borderRadius: '6px',
                  objectFit: 'cover',
                }}
              />

              <span className="font-display" style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--chai-brown)' }}>
                CHAI AI
              </span>
            </div>
            <p style={{ fontSize: '0.88rem', color: 'var(--chai-muted-brown)', maxWidth: '420px' }}>
              Image authenticity assessment and forensic image insights.
            </p>
            <p className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--chai-coffee)', marginTop: '0.4rem' }}>
              Created by Noel Ninan Sheri.
            </p>
          </div>

          {/* Download Link */}
          <div>
            <a
              href="/downloads/Chai AI.apk"
              download="Chai AI.apk"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.45rem',
                backgroundColor: 'var(--chai-terracotta)',
                color: '#F8F3E8',
                padding: '0.55rem 1.15rem',
                borderRadius: '4px',
                textDecoration: 'none',
                fontSize: '0.85rem',
                fontWeight: 500,
                letterSpacing: '0.02em',
                transition: 'background-color 0.2s',
              }}
              onMouseOver={(e) => (e.currentTarget.style.backgroundColor = 'var(--chai-terracotta-hover)')}
              onMouseOut={(e) => (e.currentTarget.style.backgroundColor = 'var(--chai-terracotta)')}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              Download APK
            </a>
          </div>

        </div>

        {/* Legal and Timestamp Bar */}
        <div
          style={{
            borderTop: '1px solid var(--chai-border-subtle)',
            marginTop: '2.5rem',
            paddingTop: '1.5rem',
            display: 'flex',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '1rem',
          }}
        >
          <span className="font-mono" style={{ fontSize: '0.72rem', color: 'var(--chai-muted-brown)' }}>
            © {new Date().getFullYear()} Chai AI. Built for forensic transparency.
          </span>
          <span className="font-mono" style={{ fontSize: '0.72rem', color: 'var(--chai-muted-brown)' }}>
            "Look beyond the image. Understand what the image reveals."
          </span>
        </div>
      </div>
    </footer>
  );
};
