import React, { useState, useEffect } from 'react';

export const Header: React.FC = () => {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header
      className={`sticky top-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-[#F3EBDD]/92 backdrop-blur-md border-b border-[#2B211B]/10 py-3.5 shadow-sm'
          : 'bg-transparent py-5'
      }`}
      style={{
        backgroundColor: scrolled ? 'rgba(243, 235, 221, 0.92)' : 'transparent',
        backdropFilter: scrolled ? 'blur(10px)' : 'none',
        borderBottom: scrolled ? '1px solid rgba(43, 33, 27, 0.1)' : 'none',
      }}
    >
      <div className="chai-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        {/* Brand */}
        <a
          href="#"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            textDecoration: 'none',
            color: 'var(--chai-ink)',
          }}
        >
          <img
            src="/app-icon.png"
            alt="Chai AI Logo"
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '7px',
              objectFit: 'cover',
              boxShadow: '0 2px 6px rgba(43, 33, 27, 0.15)',
            }}
          />

          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span
              className="font-display"
              style={{
                fontSize: '1.35rem',
                fontWeight: 600,
                letterSpacing: '0.04em',
                lineHeight: 1.1,
                color: 'var(--chai-brown)',
              }}
            >
              CHAI AI
            </span>
            <span
              className="font-mono"
              style={{
                fontSize: '0.62rem',
                letterSpacing: '0.12em',
                textTransform: 'uppercase',
                color: 'var(--chai-muted-brown)',
              }}
            >
              Authenticity & Forensics
            </span>
          </div>
        </a>

        {/* Download Action */}
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
              boxShadow: '0 2px 6px rgba(169, 87, 61, 0.25)',
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
            Download App
          </a>
        </div>
      </div>
    </header>
  );
};
