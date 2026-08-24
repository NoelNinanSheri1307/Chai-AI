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
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 130px), 1fr))',
                    gap: '0.65rem',
                    marginBottom: '1.25rem',
                    width: '100%',
                  }}
                >
                  <div
                    style={{
                      padding: '0.75rem 0.85rem',
                      borderRadius: '4px',
                      backgroundColor: 'rgba(119, 112, 79, 0.14)',
                      border: '1px solid rgba(119, 112, 79, 0.3)',
                      boxSizing: 'border-box',
                    }}
                  >
                    <span className="font-mono" style={{ fontSize: '0.65rem', color: 'var(--chai-olive)', display: 'block', fontWeight: 600 }}>
                      CLASS A
                    </span>
                    <span style={{ fontWeight: 600, color: 'var(--chai-brown)', fontSize: '0.9rem' }}>
                      Original / Real
                    </span>
                  </div>

                  <div
                    style={{
                      padding: '0.75rem 0.85rem',
                      borderRadius: '4px',
                      backgroundColor: 'rgba(169, 87, 61, 0.12)',
                      border: '1px solid rgba(169, 87, 61, 0.3)',
                      boxSizing: 'border-box',
                    }}
                  >
                    <span className="font-mono" style={{ fontSize: '0.65rem', color: 'var(--chai-terracotta)', display: 'block', fontWeight: 600 }}>
                      CLASS B
                    </span>
                    <span style={{ fontWeight: 600, color: 'var(--chai-terracotta)', fontSize: '0.9rem' }}>
                      AI Generated
                    </span>
                  </div>
                </div>

                <div
                  className="font-mono"
                  style={{
                    fontSize: 'clamp(0.68rem, 1.8vw, 0.75rem)',
                    color: 'var(--chai-muted-brown)',
                    backgroundColor: 'rgba(43, 33, 27, 0.04)',
                    padding: '0.65rem 0.85rem',
                    borderRadius: '4px',
                    borderLeft: '3px solid var(--chai-terracotta)',
                    lineHeight: 1.5,
                    wordBreak: 'break-word',
                    width: '100%',
                    boxSizing: 'border-box',
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
                    padding: 'clamp(0.85rem, 3vw, 1.35rem)',
                    boxShadow: 'inset 0 2px 8px rgba(0,0,0,0.4)',
                    width: '100%',
                    boxSizing: 'border-box',
                  }}
                >
                  <div
                    className="font-mono"
                    style={{
                      fontSize: '0.68rem',
                      color: 'var(--chai-clay)',
                      borderBottom: '1px solid rgba(248, 243, 232, 0.1)',
                      paddingBottom: '0.5rem',
                      marginBottom: '0.85rem',
                      letterSpacing: '0.06em',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                    }}
                  >
                    <span>DECISION PIPELINE MATRIX</span>
                    <span style={{ fontSize: '0.6rem', color: '#DFD0B8', opacity: 0.6 }}>3 STAGES</span>
                  </div>

                  {/* Flow items */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
                    {/* Stage 1 */}
                    <div
                      style={{
                        padding: '0.7rem 0.85rem',
                        backgroundColor: 'rgba(248, 243, 232, 0.05)',
                        borderRadius: '4px',
                        border: '1px solid rgba(248, 243, 232, 0.08)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '4px',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
                        <span className="font-mono" style={{ fontSize: '0.78rem', color: '#F8F3E8', fontWeight: 600 }}>
                          1. Image Ingestion
                        </span>
                        <span
                          className="font-mono"
                          style={{
                            fontSize: '0.62rem',
                            color: '#A66A4F',
                            backgroundColor: 'rgba(166, 106, 79, 0.18)',
                            padding: '2px 6px',
                            borderRadius: '3px',
                          }}
                        >
                          RAW RGB
                        </span>
                      </div>
                      <span className="font-mono" style={{ fontSize: '0.68rem', color: 'rgba(248, 243, 232, 0.55)' }}>
                        EXIF extraction & structural normalization
                      </span>
                    </div>

                    {/* Stage 2 */}
                    <div
                      style={{
                        padding: '0.7rem 0.85rem',
                        backgroundColor: 'rgba(248, 243, 232, 0.05)',
                        borderRadius: '4px',
                        border: '1px solid rgba(248, 243, 232, 0.08)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '4px',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
                        <span className="font-mono" style={{ fontSize: '0.78rem', color: '#F8F3E8', fontWeight: 600 }}>
                          2. Dual Verification
                        </span>
                        <span
                          className="font-mono"
                          style={{
                            fontSize: '0.62rem',
                            color: 'var(--chai-olive)',
                            backgroundColor: 'rgba(119, 112, 79, 0.22)',
                            padding: '2px 6px',
                            borderRadius: '3px',
                          }}
                        >
                          70 / 30 FUSION
                        </span>
                      </div>
                      <span className="font-mono" style={{ fontSize: '0.68rem', color: 'rgba(248, 243, 232, 0.55)' }}>
                        Sightengine (70%) + Chai Forensics (30%)
                      </span>
                    </div>

                    {/* Stage 3 */}
                    <div
                      style={{
                        padding: '0.7rem 0.85rem',
                        backgroundColor: 'rgba(169, 87, 61, 0.15)',
                        borderRadius: '4px',
                        border: '1px solid rgba(169, 87, 61, 0.35)',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '4px',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
                        <span className="font-mono" style={{ fontSize: '0.78rem', color: '#F8F3E8', fontWeight: 600 }}>
                          3. Authenticity Verdict
                        </span>
                        <span
                          className="font-mono"
                          style={{
                            fontSize: '0.62rem',
                            color: 'var(--chai-terracotta)',
                            fontWeight: 600,
                            backgroundColor: 'rgba(169, 87, 61, 0.25)',
                            padding: '2px 6px',
                            borderRadius: '3px',
                          }}
                        >
                          EVALUATED
                        </span>
                      </div>
                      <span className="font-mono" style={{ fontSize: '0.68rem', color: '#DFD0B8', opacity: 0.8 }}>
                        Real or AI-Generated classification
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
              padding: 'clamp(1rem, 3.5vw, 2.5rem)',
              border: '1px solid var(--chai-border)',
              width: '100%',
              boxSizing: 'border-box',
            }}
          >
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(12, 1fr)',
                gap: '2rem',
                alignItems: 'center',
              }}
            >
              <div style={{ gridColumn: 'span 12' }} className="feature-visual-2">
                {/* Real Forensic Metric Categories Used in Chai AI */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 120px), 1fr))',
                    gap: '0.6rem',
                    width: '100%',
                  }}
                >
                  {[
                    { label: 'SPATIAL FREQUENCY', val: 'FFT Radial' },
                    { label: 'ERROR-LEVEL ANALYSIS', val: 'Quantization' },
                    { label: 'NOISE RESIDUALS', val: 'Sensor Noise' },
                    { label: 'LIGHTING COHERENCE', val: 'Normal Vector' },
                    { label: 'TEXTURE / GRADIENT', val: 'Laplacian' },
                    { label: 'COMPRESSION', val: 'JPEG Grids' },
                    { label: 'METADATA & EXIF', val: 'Provenance' },
                    { label: 'EDGE CONSISTENCY', val: 'Gradients' },
                  ].map((item, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '0.65rem',
                        backgroundColor: 'var(--chai-bg)',
                        border: '1px solid var(--chai-border)',
                        borderRadius: '4px',
                        boxSizing: 'border-box',
                        minWidth: 0,
                      }}
                    >
                      <span className="font-mono" style={{ fontSize: '0.6rem', color: 'var(--chai-terracotta)', display: 'block', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {item.label}
                      </span>
                      <span style={{ fontSize: '0.78rem', fontWeight: 500, color: 'var(--chai-brown)', display: 'block', overflow: 'hidden', textOverflow: 'ellipsis' }}>
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
                    fontSize: '0.72rem',
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
                    fontSize: 'clamp(1.75rem, 2.8vw, 2.5rem)',
                    color: 'var(--chai-brown)',
                    lineHeight: 1.2,
                    marginBottom: '0.85rem',
                  }}
                >
                  Image Insights
                </h3>
                <p style={{ fontSize: '1rem', color: 'var(--chai-coffee)', lineHeight: 1.6, marginBottom: '1.25rem' }}>
                  Everything the image reveals beyond its classification. Inspect structural anomalies, spectral signatures, and camera artifacts in granular detail.
                </p>

                <div
                  style={{
                    padding: '0.75rem 0.95rem',
                    backgroundColor: 'rgba(119, 112, 79, 0.1)',
                    border: '1px solid rgba(119, 112, 79, 0.25)',
                    borderRadius: '4px',
                    boxSizing: 'border-box',
                    width: '100%',
                  }}
                >
                  <p style={{ fontSize: '0.8rem', color: 'var(--chai-brown)', lineHeight: 1.5 }}>
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
