import React from 'react';

export const Download: React.FC = () => {
  return (
    <section id="download" style={{ paddingTop: '7rem', paddingBottom: '7rem' }}>
      <div className="chai-container">
        <div
          className="specimen-card"
          style={{
            maxWidth: '880px',
            margin: '0 auto',
            borderRadius: '8px',
            padding: 'clamp(2rem, 5vw, 4rem)',
            textAlign: 'center',
            border: '1px solid var(--chai-border)',
            background: 'linear-gradient(145deg, #F8F3E8 0%, #EFE5D3 100%)',
          }}
        >
          <span className="forensic-badge" style={{ marginBottom: '1.25rem' }}>
            Section 04 // Mobile Application
          </span>


          <h2
            className="font-display"
            style={{
              fontSize: 'clamp(2.4rem, 4.5vw, 3.8rem)',
              color: 'var(--chai-brown)',
              lineHeight: 1.15,
              marginBottom: '1.25rem',
            }}
          >
            Take Chai with you.
          </h2>

          <p
            style={{
              fontSize: '1.15rem',
              color: 'var(--chai-coffee)',
              lineHeight: 1.65,
              maxWidth: '580px',
              margin: '0 auto 2.5rem auto',
            }}
          >
            Download the Chai AI Android application and run complete image authenticity assessments and forensic signal inspections directly from your phone.
          </p>

          {/* Download Action Card */}
          <div
            style={{
              display: 'inline-flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '1rem',
            }}
          >
            <a
              href="/downloads/ChaiAI.apk"
              download="ChaiAI.apk"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.75rem',
                backgroundColor: 'var(--chai-terracotta)',
                color: '#F8F3E8',
                padding: 'clamp(0.9rem, 2.5vw, 1.1rem) clamp(1.4rem, 4vw, 2.5rem)',
                borderRadius: '6px',
                textDecoration: 'none',
                fontSize: 'clamp(1rem, 2.8vw, 1.15rem)',
                fontWeight: 600,
                letterSpacing: '0.02em',
                boxShadow: '0 6px 20px rgba(169, 87, 61, 0.32)',
                transition: 'all 0.2s ease',
                maxWidth: '100%',
                flexWrap: 'wrap',
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.backgroundColor = 'var(--chai-terracotta-hover)';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.backgroundColor = 'var(--chai-terracotta)';
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              <span>Download Chai AI</span>
              <span
                className="font-mono"
                style={{
                  fontSize: '0.75rem',
                  backgroundColor: 'rgba(0, 0, 0, 0.2)',
                  padding: '2px 8px',
                  borderRadius: '4px',
                }}
              >
                54.3 MB
              </span>
            </a>


            {/* Spec / Package Details */}
            <div
              className="font-mono"
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                justifyContent: 'center',
                gap: '1rem',
                fontSize: '0.78rem',
                color: 'var(--chai-muted-brown)',
              }}
            >
              <span>PACKAGE: ChaiAI.apk</span>
              <span>•</span>
              <span>PLATFORM: Android 8.0+</span>
              <span>•</span>
              <span>BUILD: Production Release</span>
            </div>


            {/* Disclaimer */}
            <p
              style={{
                fontSize: '0.82rem',
                color: 'var(--chai-muted-brown)',
                maxWidth: '480px',
                lineHeight: 1.5,
                marginTop: '1rem',
              }}
            >
              Android package file. When installing, your device may ask for standard confirmation to install applications downloaded outside the Google Play Store.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};
