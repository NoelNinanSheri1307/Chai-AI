import React from 'react';

export const ProductIntro: React.FC = () => {
  return (
    <section
      id="about"
      style={{
        paddingTop: '5rem',
        paddingBottom: '5rem',
        borderTop: '1px solid var(--chai-border)',
        borderBottom: '1px solid var(--chai-border)',
        backgroundColor: 'rgba(233, 221, 200, 0.35)',
      }}
    >
      <div className="chai-container">
        <div style={{ maxWidth: '840px', margin: '0 auto', textAlign: 'center' }}>
          <span className="forensic-badge" style={{ marginBottom: '1.25rem' }}>
            Section 01 // Product Philosophy
          </span>

          <h2
            className="font-display"
            style={{
              fontSize: 'clamp(2rem, 3.5vw, 3.1rem)',
              lineHeight: 1.2,
              color: 'var(--chai-brown)',
              marginBottom: '1.75rem',
            }}
          >
            An image can be examined without being taken at face value.
          </h2>

          <p
            style={{
              fontSize: '1.15rem',
              lineHeight: 1.75,
              color: 'var(--chai-coffee)',
              marginBottom: '2rem',
            }}
          >
            Chai AI was created to provide a measured, transparent lens into digital imagery. Rather than rendering opaque, binary assertions, Chai couples external verification with multi-signal forensic decomposition — exposing the pixel structures, compression characteristics, and metadata anomalies that accompany modern digital media.
          </p>
        </div>

        {/* 3 Pillars of Transparent Forensics */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '1.5rem',
            marginTop: '3rem',
          }}
        >
          <div
            className="specimen-card"
            style={{
              padding: '1.75rem',
              borderRadius: '6px',
              border: '1px solid var(--chai-border)',
            }}
          >
            <div
              className="font-mono"
              style={{
                fontSize: '0.72rem',
                color: 'var(--chai-terracotta)',
                fontWeight: 600,
                marginBottom: '0.75rem',
              }}
            >
              01 // EXTERNAL VERIFICATION
            </div>
            <h3
              className="font-display"
              style={{ fontSize: '1.35rem', color: 'var(--chai-brown)', marginBottom: '0.65rem' }}
            >
              Sightengine Reference
            </h3>
            <p style={{ fontSize: '0.92rem', color: 'var(--chai-muted-brown)', lineHeight: 1.6 }}>
              The system anchors its top-level classification on external verification engines, cross-referencing generative models trained on millions of contemporary image artifacts.
            </p>
          </div>

          <div
            className="specimen-card"
            style={{
              padding: '1.75rem',
              borderRadius: '6px',
              border: '1px solid var(--chai-border)',
            }}
          >
            <div
              className="font-mono"
              style={{
                fontSize: '0.72rem',
                color: 'var(--chai-terracotta)',
                fontWeight: 600,
                marginBottom: '0.75rem',
              }}
            >
              02 // INTERNAL FORENSICS
            </div>
            <h3
              className="font-display"
              style={{ fontSize: '1.35rem', color: 'var(--chai-brown)', marginBottom: '0.65rem' }}
            >
              Multi-Signal Inspection
            </h3>
            <p style={{ fontSize: '0.92rem', color: 'var(--chai-muted-brown)', lineHeight: 1.6 }}>
              Chai performs independent Error Level Analysis (ELA), frequency domain decomposition, lighting vector checking, and noise residue analysis to corroborate findings.
            </p>
          </div>

          <div
            className="specimen-card"
            style={{
              padding: '1.75rem',
              borderRadius: '6px',
              border: '1px solid var(--chai-border)',
            }}
          >
            <div
              className="font-mono"
              style={{
                fontSize: '0.72rem',
                color: 'var(--chai-terracotta)',
                fontWeight: 600,
                marginBottom: '0.75rem',
              }}
            >
              03 // ETHICAL INTEGRITY
            </div>
            <h3
              className="font-display"
              style={{ fontSize: '1.35rem', color: 'var(--chai-brown)', marginBottom: '0.65rem' }}
            >
              Context, Not Absolute Proof
            </h3>
            <p style={{ fontSize: '0.92rem', color: 'var(--chai-muted-brown)', lineHeight: 1.6 }}>
              No forensic tool is infallible. Chai explicitly frames internal signals, heatmaps, and frequency peaks as supporting context to inform human judgment.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};
