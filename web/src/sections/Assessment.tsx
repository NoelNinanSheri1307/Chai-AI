import React from 'react';

export const Assessment: React.FC = () => {
  return (
    <section
      id="architecture"
      style={{
        paddingTop: '6rem',
        paddingBottom: '6rem',
        backgroundColor: 'rgba(233, 221, 200, 0.45)',
        borderTop: '1px solid var(--chai-border)',
        borderBottom: '1px solid var(--chai-border)',
      }}
    >
      <div className="chai-container">
        <div style={{ textAlign: 'center', maxWidth: '760px', margin: '0 auto 4rem auto' }}>
          <span className="forensic-badge" style={{ marginBottom: '1rem' }}>
            Section 03 // Architecture & Decision Weighting
          </span>
          <h2
            className="font-display"
            style={{
              fontSize: 'clamp(2.2rem, 4vw, 3.25rem)',
              color: 'var(--chai-brown)',
              lineHeight: 1.18,
              marginBottom: '1.25rem',
            }}
          >
            How the assessment works.
          </h2>
          <p style={{ fontSize: '1.1rem', color: 'var(--chai-coffee)', lineHeight: 1.65 }}>
            Rather than relying on a single black-box algorithm, Chai AI fuses external verification with internal forensic decomposition to reach a balanced, defensible verdict.
          </p>
        </div>

        {/* Converging Evidence Stream Diagram */}
        <div
          className="specimen-card"
          style={{
            borderRadius: '8px',
            padding: 'clamp(1.5rem, 4vw, 3rem)',
            border: '1px solid var(--chai-border)',
            position: 'relative',
          }}
        >
          {/* Top Step: Image Input */}
          <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.6rem',
                backgroundColor: 'var(--chai-brown)',
                color: '#F8F3E8',
                padding: '0.65rem 1.5rem',
                borderRadius: '4px',
                boxShadow: '0 2px 8px rgba(43, 33, 27, 0.2)',
              }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <polyline points="21 15 16 10 5 21" />
              </svg>
              <span className="font-mono" style={{ fontSize: '0.85rem', fontWeight: 600 }}>
                INPUT SPECIMEN (PNG / JPEG / WEBP)
              </span>
            </div>
          </div>

          {/* Dual Stream Columns */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(290px, 1fr))',
              gap: '2rem',
              position: 'relative',
            }}
          >
            {/* Stream 1: Sightengine External */}
            <div
              style={{
                backgroundColor: 'var(--chai-ivory)',
                border: '1px solid rgba(169, 87, 61, 0.3)',
                borderRadius: '6px',
                padding: '1.75rem',
                position: 'relative',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '1rem',
                  borderBottom: '1px solid var(--chai-border)',
                  paddingBottom: '0.75rem',
                }}
              >
                <span className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--chai-terracotta)', fontWeight: 600 }}>
                  STREAM A // PRIMARY VERIFICATION
                </span>
                <span
                  className="font-mono"
                  style={{
                    fontSize: '0.75rem',
                    backgroundColor: 'rgba(169, 87, 61, 0.15)',
                    color: 'var(--chai-terracotta)',
                    padding: '2px 8px',
                    borderRadius: '3px',
                    fontWeight: 600,
                  }}
                >
                  70% Weight
                </span>
              </div>

              <h3 className="font-display" style={{ fontSize: '1.35rem', color: 'var(--chai-brown)', marginBottom: '0.75rem' }}>
                Sightengine External Detection
              </h3>

              <p style={{ fontSize: '0.9rem', color: 'var(--chai-coffee)', lineHeight: 1.6, marginBottom: '1rem' }}>
                Leverages industry-leading generative AI artifact detection models. Evaluates cross-model synthetic signatures across diffusion and GAN architectures.
              </p>

              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <li style={{ fontSize: '0.82rem', color: 'var(--chai-muted-brown)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span style={{ color: 'var(--chai-terracotta)' }}>✓</span> Synthetic Probability Scoring
                </li>
                <li style={{ fontSize: '0.82rem', color: 'var(--chai-muted-brown)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span style={{ color: 'var(--chai-terracotta)' }}>✓</span> Model Generator Classification
                </li>
                <li style={{ fontSize: '0.82rem', color: 'var(--chai-muted-brown)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span style={{ color: 'var(--chai-terracotta)' }}>✓</span> Robust Zero-Day AI Inpainting Detection
                </li>
              </ul>
            </div>

            {/* Stream 2: Chai Forensics */}
            <div
              style={{
                backgroundColor: 'var(--chai-ivory)',
                border: '1px solid rgba(119, 112, 79, 0.3)',
                borderRadius: '6px',
                padding: '1.75rem',
                position: 'relative',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '1rem',
                  borderBottom: '1px solid var(--chai-border)',
                  paddingBottom: '0.75rem',
                }}
              >
                <span className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--chai-olive)', fontWeight: 600 }}>
                  STREAM B // SUPPORTING FORENSICS
                </span>
                <span
                  className="font-mono"
                  style={{
                    fontSize: '0.75rem',
                    backgroundColor: 'rgba(119, 112, 79, 0.15)',
                    color: 'var(--chai-olive)',
                    padding: '2px 8px',
                    borderRadius: '3px',
                    fontWeight: 600,
                  }}
                >
                  30% Weight
                </span>
              </div>

              <h3 className="font-display" style={{ fontSize: '1.35rem', color: 'var(--chai-brown)', marginBottom: '0.75rem' }}>
                Chai Internal Forensics
              </h3>

              <p style={{ fontSize: '0.9rem', color: 'var(--chai-coffee)', lineHeight: 1.6, marginBottom: '1rem' }}>
                Decomposes the image across 7 distinct forensic categories, searching for physics discrepancies, compression mismatches, and EXIF irregularities.
              </p>

              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                <li style={{ fontSize: '0.82rem', color: 'var(--chai-muted-brown)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span style={{ color: 'var(--chai-olive)' }}>✓</span> Error-Level Analysis (ELA)
                </li>
                <li style={{ fontSize: '0.82rem', color: 'var(--chai-muted-brown)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span style={{ color: 'var(--chai-olive)' }}>✓</span> Spatial Frequency & Noise Residuals
                </li>
                <li style={{ fontSize: '0.82rem', color: 'var(--chai-olive)' }}>
                  <span style={{ color: 'var(--chai-olive)' }}>✓</span> Fallback Engine if External API is Offline
                </li>
              </ul>
            </div>
          </div>

          {/* Convergence Node */}
          <div
            style={{
              marginTop: '2.5rem',
              paddingTop: '2rem',
              borderTop: '1px dashed var(--chai-border)',
              textAlign: 'center',
            }}
          >
            <div
              style={{
                display: 'inline-block',
                backgroundColor: 'var(--chai-ink)',
                color: '#F8F3E8',
                borderRadius: '6px',
                padding: '1.25rem 2rem',
                maxWidth: '620px',
                textAlign: 'left',
              }}
            >
              <div
                className="font-mono"
                style={{
                  fontSize: '0.72rem',
                  color: 'var(--chai-clay)',
                  letterSpacing: '0.08em',
                  marginBottom: '0.4rem',
                }}
              >
                CONVERGENCE OUTPUT // FUSED DECISION MATRIX
              </div>
              <h4 className="font-display" style={{ fontSize: '1.25rem', color: '#F8F3E8', marginBottom: '0.5rem' }}>
                Weighted Assessment + Transparent Evidence Log
              </h4>
              <p style={{ fontSize: '0.85rem', color: '#DFD0B8', lineHeight: 1.55 }}>
                The user receives the final classification (Real, AI Generated, or AI Edited) accompanied by the exact observation signals that contributed to the evaluation.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
