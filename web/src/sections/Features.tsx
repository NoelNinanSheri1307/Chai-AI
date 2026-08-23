import React from 'react';

export const Features: React.FC = () => {
  return (
    <section id="features" style={{ paddingTop: '6rem', paddingBottom: '6rem' }}>
      <div className="chai-container">
        <div style={{ textAlign: 'center', maxWidth: '700px', margin: '0 auto 4rem auto' }}>
          <span className="forensic-badge" style={{ marginBottom: '1rem' }}>
            Section 02 // Core Capabilities
          </span>
          <h2
            className="font-display"
            style={{
              fontSize: 'clamp(2.2rem, 4vw, 3.25rem)',
              color: 'var(--chai-brown)',
              lineHeight: 1.18,
              marginBottom: '1rem',
            }}
          >
            Two primary features.
            <br />
            Zero superficial filler.
          </h2>
          <p style={{ fontSize: '1.1rem', color: 'var(--chai-muted-brown)' }}>
            The application is built around two dedicated forensic dimensions: identifying provenance and extracting structural image telemetry.
          </p>
        </div>

        {/* Two Feature Blocks */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '3.5rem' }}>
          {/* Feature 1: Authenticity Detection */}
          <div
            className="specimen-card"
            style={{
              borderRadius: '8px',
              padding: 'clamp(1.5rem, 3vw, 2.75rem)',
              border: '1px solid var(--chai-border)',
            }}
          >
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(12, 1fr)',
                gap: '2.5rem',
                alignItems: 'center',
              }}
            >
              <div style={{ gridColumn: 'span 12' }} className="feature-text-1">
                <div
                  className="font-mono"
                  style={{
                    fontSize: '0.75rem',
                    color: 'var(--chai-terracotta)',
                    fontWeight: 600,
                    letterSpacing: '0.08em',
                    marginBottom: '0.5rem',
                  }}
                >
                  FEATURE 01 // PRIMARY VERDICT
                </div>
                <h3
                  className="font-display"
                  style={{
                    fontSize: 'clamp(1.85rem, 2.8vw, 2.5rem)',
                    color: 'var(--chai-brown)',
                    lineHeight: 1.2,
                    marginBottom: '1rem',
                  }}
                >
                  Authenticity Detection
                </h3>
                <p style={{ fontSize: '1.05rem', color: 'var(--chai-coffee)', lineHeight: 1.65, marginBottom: '1.5rem' }}>
                  An objective assessment of whether an uploaded photograph appears real or synthetically generated.
                </p>

                {/* Only 2 Verdict Classes: Real vs AI Generated */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
                  <div
                    style={{
                      flex: '1 1 180px',
                      padding: '0.85rem 1.25rem',
                      borderRadius: '4px',
                      backgroundColor: 'rgba(119, 112, 79, 0.14)',
                      border: '1px solid rgba(119, 112, 79, 0.3)',
                    }}
                  >
                    <span className="font-mono" style={{ fontSize: '0.7rem', color: 'var(--chai-olive)', display: 'block', fontWeight: 600 }}>
                      CLASS A
                    </span>
                    <span style={{ fontWeight: 600, color: 'var(--chai-brown)', fontSize: '1rem' }}>
                      Original / Real
                    </span>
                  </div>

                  <div
                    style={{
                      flex: '1 1 180px',
                      padding: '0.85rem 1.25rem',
                      borderRadius: '4px',
                      backgroundColor: 'rgba(169, 87, 61, 0.12)',
                      border: '1px solid rgba(169, 87, 61, 0.3)',
                    }}
                  >
                    <span className="font-mono" style={{ fontSize: '0.7rem', color: 'var(--chai-terracotta)', display: 'block', fontWeight: 600 }}>
                      CLASS B
                    </span>
                    <span style={{ fontWeight: 600, color: 'var(--chai-terracotta)', fontSize: '1rem' }}>
                      AI Generated
                    </span>
                  </div>
                </div>

                <div
                  className="font-mono"
                  style={{
                    fontSize: '0.78rem',
                    color: 'var(--chai-muted-brown)',
                    backgroundColor: 'rgba(43, 33, 27, 0.04)',
                    padding: '0.75rem 1rem',
                    borderRadius: '4px',
                    borderLeft: '3px solid var(--chai-terracotta)',
                  }}
                >
                  ENGINE NOTE: Sightengine provides external verification anchor; Chai forensics validates signal concordance.
                </div>
              </div>

              {/* Visual Path Diagram */}
              <div style={{ gridColumn: 'span 12' }} className="feature-visual-1">
                <div
                  style={{
                    backgroundColor: '#201A16',
                    color: '#F8F3E8',
                    borderRadius: '6px',
                    padding: '1.5rem',
                    boxShadow: 'inset 0 2px 8px rgba(0,0,0,0.4)',
                  }}
                >
                  <div
                    className="font-mono"
                    style={{
                      fontSize: '0.7rem',
                      color: 'var(--chai-clay)',
                      borderBottom: '1px solid rgba(248, 243, 232, 0.1)',
                      paddingBottom: '0.5rem',
                      marginBottom: '1rem',
                    }}
                  >
                    DECISION PIPELINE MATRIX
                  </div>

                  {/* Flow items */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0.65rem 0.85rem',
                        backgroundColor: 'rgba(248, 243, 232, 0.05)',
                        borderRadius: '4px',
                        border: '1px solid rgba(248, 243, 232, 0.08)',
                      }}
                    >
                      <span className="font-mono" style={{ fontSize: '0.8rem' }}>1. Image Ingestion & EXIF Extraction</span>
                      <span className="font-mono" style={{ fontSize: '0.7rem', color: '#A66A4F' }}>RAW RGB</span>
                    </div>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0.65rem 0.85rem',
                        backgroundColor: 'rgba(248, 243, 232, 0.05)',
                        borderRadius: '4px',
                        border: '1px solid rgba(248, 243, 232, 0.08)',
                      }}
                    >
                      <span className="font-mono" style={{ fontSize: '0.8rem' }}>2. Dual-Engine Verification</span>
                      <span className="font-mono" style={{ fontSize: '0.7rem', color: 'var(--chai-olive)' }}>70 / 30 FUSION</span>
                    </div>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0.65rem 0.85rem',
                        backgroundColor: 'rgba(169, 87, 61, 0.15)',
                        borderRadius: '4px',
                        border: '1px solid rgba(169, 87, 61, 0.35)',
                      }}
                    >
                      <span className="font-mono" style={{ fontSize: '0.8rem', color: '#F8F3E8', fontWeight: 600 }}>
                        3. Authenticity Verdict Output
                      </span>
                      <span className="font-mono" style={{ fontSize: '0.7rem', color: 'var(--chai-terracotta)', fontWeight: 600 }}>
                        EVALUATED
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Feature 2: Image Insights */}
          <div
            className="specimen-card"
            style={{
              borderRadius: '8px',
              padding: 'clamp(1.5rem, 3vw, 2.75rem)',
              border: '1px solid var(--chai-border)',
            }}
          >
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(12, 1fr)',
                gap: '2.5rem',
                alignItems: 'center',
              }}
            >
              <div style={{ gridColumn: 'span 12' }} className="feature-visual-2">
                {/* Real Forensic Metric Categories Used in Chai AI */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
                    gap: '0.75rem',
                  }}
                >
                  {[
                    { label: 'SPATIAL FREQUENCY', val: 'FFT Radial Spectrum' },
                    { label: 'ERROR-LEVEL ANALYSIS', val: 'Quantization Variance' },
                    { label: 'NOISE RESIDUALS', val: 'Sensor Noise Pattern' },
                    { label: 'LIGHTING COHERENCE', val: 'Normal Vector Map' },
                    { label: 'TEXTURE / GRADIENT', val: 'Laplacian Variance' },
                    { label: 'COMPRESSION', val: 'JPEG Grid Structures' },
                    { label: 'METADATA & EXIF', val: 'Header Provenance' },
                    { label: 'EDGE CONSISTENCY', val: 'Gradient Discontinuity' },
                  ].map((item, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '0.85rem',
                        backgroundColor: 'var(--chai-bg)',
                        border: '1px solid var(--chai-border)',
                        borderRadius: '4px',
                      }}
                    >
                      <span className="font-mono" style={{ fontSize: '0.65rem', color: 'var(--chai-terracotta)', display: 'block', fontWeight: 600 }}>
                        {item.label}
                      </span>
                      <span style={{ fontSize: '0.82rem', fontWeight: 500, color: 'var(--chai-brown)' }}>
                        {item.val}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ gridColumn: 'span 12' }} className="feature-text-2">
                <div
                  className="font-mono"
                  style={{
                    fontSize: '0.75rem',
                    color: 'var(--chai-terracotta)',
                    fontWeight: 600,
                    letterSpacing: '0.08em',
                    marginBottom: '0.5rem',
                  }}
                >
                  FEATURE 02 // FORENSIC METRICS
                </div>
                <h3
                  className="font-display"
                  style={{
                    fontSize: 'clamp(1.85rem, 2.8vw, 2.5rem)',
                    color: 'var(--chai-brown)',
                    lineHeight: 1.2,
                    marginBottom: '1rem',
                  }}
                >
                  Image Insights
                </h3>
                <p style={{ fontSize: '1.05rem', color: 'var(--chai-coffee)', lineHeight: 1.65, marginBottom: '1.25rem' }}>
                  Everything the image reveals beyond its classification. Inspect structural anomalies, spectral signatures, and camera artifacts in granular detail.
                </p>

                <div
                  style={{
                    padding: '0.85rem 1rem',
                    backgroundColor: 'rgba(119, 112, 79, 0.1)',
                    border: '1px solid rgba(119, 112, 79, 0.25)',
                    borderRadius: '4px',
                  }}
                >
                  <p style={{ fontSize: '0.82rem', color: 'var(--chai-brown)', lineHeight: 1.5 }}>
                    <strong>Scientific Disclaimer:</strong> These signals provide supporting context. They are physical and statistical observations, not guaranteed standalone proof of AI generation.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @media (min-width: 992px) {
          .feature-text-1 {
            grid-column: span 7 !important;
          }
          .feature-visual-1 {
            grid-column: span 5 !important;
          }
          .feature-text-2 {
            grid-column: span 6 !important;
          }
          .feature-visual-2 {
            grid-column: span 6 !important;
          }
        }
      `}</style>
    </section>
  );
};
