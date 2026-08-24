import React, { useState, useEffect, useRef } from 'react';

interface ScreenshotSlide {
  id: string;
  title: string;
  subtitle: string;
  step: string;
  description: string;
  image: string;
  badge: string;
}

const slides: ScreenshotSlide[] = [
  {
    id: 'front',
    title: 'Mobile Interface',
    subtitle: 'Streamlined Entry',
    step: '01',
    description: 'A focused, forensic-first dark interface with real-time quota tracking and intuitive capture workflows.',
    image: '/proof/Front.jpg',
    badge: 'Home Dashboard',
  },
  {
    id: 'upload',
    title: 'Image Ingestion',
    subtitle: 'Camera & Gallery Selection',
    step: '02',
    description: 'Seamlessly pick or capture photos with client-side resolution optimization for rapid cloud verification.',
    image: '/proof/Image Upload.png',
    badge: 'Smart Ingestion',
  },
  {
    id: 'analysis',
    title: 'Pipeline In Motion',
    subtitle: '6-Stage Real-Time Execution',
    step: '03',
    description: 'Live progress tracking across EXIF extraction, Chai forensics, external verification, and signal synthesis.',
    image: '/proof/Analysis.jpg',
    badge: '6-Stage Engine',
  },
  {
    id: 'results',
    title: 'Authenticity Verdict',
    subtitle: 'Dual-Stream Decision Fusion',
    step: '04',
    description: 'Instant classification (Real or AI Generated) with calibrated confidence percentages and dual-source attribution.',
    image: '/proof/Results.png',
    badge: 'Primary Verdict',
  },
  {
    id: 'forensics',
    title: 'Forensic Evidence',
    subtitle: 'Deep Signal Decomposition',
    step: '05',
    description: 'Granular scores for Spatial Frequency, Noise Residuals, Lighting Coherence, Texture Variance, and Compression Grids.',
    image: '/proof/ForensicsInfo.png',
    badge: 'Signal Breakdown',
  },
  {
    id: 'photo-info',
    title: 'Metadata & EXIF',
    subtitle: 'Provenance Verification',
    step: '06',
    description: 'Comprehensive inspection of image dimensions, color profiles, camera metadata, and file provenance records.',
    image: '/proof/PhotoInfo.png',
    badge: 'EXIF Extraction',
  },
  {
    id: 'about',
    title: 'Transparency & Design',
    subtitle: 'Product Integrity',
    step: '07',
    description: 'Full architectural transparency detailing how Chai AI converges external benchmarks with internal signal models.',
    image: '/proof/About.jpg',
    badge: 'System Design',
  },
];

export const PhoneShowcase: React.FC = () => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    if (isPaused) return;

    timerRef.current = window.setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % slides.length);
    }, 3600);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPaused]);

  const goToSlide = (index: number) => {
    setCurrentIndex(index);
  };

  const nextSlide = () => {
    setCurrentIndex((prev) => (prev + 1) % slides.length);
  };

  const prevSlide = () => {
    setCurrentIndex((prev) => (prev - 1 + slides.length) % slides.length);
  };

  const activeSlide = slides[currentIndex];

  return (
    <section
      id="app-demo"
      style={{
        paddingTop: '6rem',
        paddingBottom: '6rem',
        borderTop: '1px solid var(--chai-border-subtle)',
        borderBottom: '1px solid var(--chai-border-subtle)',
        backgroundColor: '#EFE6D6',
        position: 'relative',
        overflow: 'hidden',
      }}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div className="chai-container">
        {/* Section Header */}
        <div style={{ textAlign: 'center', maxWidth: '720px', margin: '0 auto 3.5rem auto' }}>
          <span className="forensic-badge" style={{ marginBottom: '1rem' }}>
            Interactive Demonstration // Live App Flow
          </span>
          <h2
            className="font-display"
            style={{
              fontSize: 'clamp(2.2rem, 4vw, 3.2rem)',
              color: 'var(--chai-brown)',
              lineHeight: 1.18,
              marginBottom: '1rem',
            }}
          >
            The Mobile Experience in Action.
          </h2>
          <p
            style={{
              fontSize: '1.05rem',
              color: 'var(--chai-coffee)',
              lineHeight: 1.6,
            }}
          >
            Explore actual walkthrough captures of Chai AI analyzing, verifying, and breaking down image forensic signals.
          </p>
        </div>

        {/* Main Showcase Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 300px), 1fr))',
            gap: 'clamp(2rem, 4vw, 3.5rem)',
            alignItems: 'center',
            maxWidth: '1040px',
            margin: '0 auto',
          }}
        >
          {/* Left Column: Phone Mockup Frame */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              position: 'relative',
              width: '100%',
            }}
          >
            {/* Phone Outer Chassis */}
            <div
              style={{
                width: 'min(300px, 88vw)',
                height: 'clamp(490px, 120vw, 615px)',
                backgroundColor: '#1E1916',
                borderRadius: 'clamp(32px, 8vw, 44px)',
                padding: 'clamp(8px, 2vw, 12px)',
                boxShadow:
                  '0 25px 60px -15px rgba(43, 33, 27, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.1) inset, 0 10px 25px rgba(0, 0, 0, 0.25)',
                position: 'relative',
                border: '3px solid #382C25',
              }}
            >
              {/* Phone Speaker & Dynamic Island Punch-hole */}
              <div
                style={{
                  position: 'absolute',
                  top: '16px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  width: 'clamp(70px, 22vw, 90px)',
                  height: '18px',
                  backgroundColor: '#0F0C0A',
                  borderRadius: '10px',
                  zIndex: 20,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                }}
              >
                <div style={{ width: '7px', height: '7px', borderRadius: '50%', backgroundColor: '#1A233A' }} />
                <div style={{ width: '32px', height: '3px', borderRadius: '2px', backgroundColor: '#261F1A' }} />
              </div>

              {/* Phone Screen Viewport */}
              <div
                style={{
                  width: '100%',
                  height: '100%',
                  backgroundColor: '#0B0C0E',
                  borderRadius: 'clamp(24px, 6vw, 34px)',
                  overflow: 'hidden',
                  position: 'relative',
                }}
              >

                {/* Horizontal Sliding Track */}
                <div
                  style={{
                    display: 'flex',
                    width: `${slides.length * 100}%`,
                    height: '100%',
                    transform: `translateX(-${currentIndex * (100 / slides.length)}%)`,
                    transition: 'transform 0.65s cubic-bezier(0.2, 0.9, 0.3, 1)',
                  }}
                >
                  {slides.map((slide, idx) => (
                    <div
                      key={slide.id}
                      style={{
                        width: `${100 / slides.length}%`,
                        height: '100%',
                        position: 'relative',
                        flexShrink: 0,
                        backgroundColor: '#0B0C0E',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <img
                        src={slide.image}
                        alt={slide.title}
                        loading={idx === 0 ? 'eager' : 'lazy'}
                        style={{
                          width: '100%',
                          height: '100%',
                          objectFit: 'contain',
                          objectPosition: 'center',
                          display: 'block',
                        }}
                      />
                    </div>
                  ))}
                </div>

                {/* Top Subtle Status Bar Overlay */}
                <div
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    height: '34px',
                    background: 'linear-gradient(to bottom, rgba(11,12,14,0.7), transparent)',
                    pointerEvents: 'none',
                    zIndex: 15,
                  }}
                />

                {/* Bottom Subtle Gradient Overlay */}
                <div
                  style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    height: '40px',
                    background: 'linear-gradient(to top, rgba(11,12,14,0.6), transparent)',
                    pointerEvents: 'none',
                    zIndex: 15,
                  }}
                />
              </div>

              {/* Gloss Reflection Accent */}
              <div
                style={{
                  position: 'absolute',
                  top: '12px',
                  right: '12px',
                  width: '45%',
                  height: '65%',
                  background: 'linear-gradient(135deg, rgba(255,255,255,0.06) 0%, transparent 60%)',
                  borderRadius: '34px 34px 0 0',
                  pointerEvents: 'none',
                  zIndex: 22,
                }}
              />
            </div>

            {/* Carousel Arrow Controls */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '1rem',
                marginTop: '1.5rem',
              }}
            >
              <button
                type="button"
                onClick={prevSlide}
                aria-label="Previous screenshot"
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  border: '1px solid var(--chai-border)',
                  backgroundColor: '#F8F3E8',
                  color: 'var(--chai-brown)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  boxShadow: '0 2px 6px rgba(43, 33, 27, 0.08)',
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--chai-terracotta)';
                  e.currentTarget.style.color = '#F8F3E8';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = '#F8F3E8';
                  e.currentTarget.style.color = 'var(--chai-brown)';
                }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="15 18 9 12 15 6" />
                </svg>
              </button>

              {/* Progress Dots */}
              <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                {slides.map((_, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => goToSlide(idx)}
                    aria-label={`Go to slide ${idx + 1}`}
                    style={{
                      width: idx === currentIndex ? '24px' : '8px',
                      height: '8px',
                      borderRadius: '4px',
                      backgroundColor: idx === currentIndex ? 'var(--chai-terracotta)' : 'rgba(43, 33, 27, 0.25)',
                      border: 'none',
                      cursor: 'pointer',
                      transition: 'all 0.3s ease',
                      padding: 0,
                    }}
                  />
                ))}
              </div>

              <button
                type="button"
                onClick={nextSlide}
                aria-label="Next screenshot"
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  border: '1px solid var(--chai-border)',
                  backgroundColor: '#F8F3E8',
                  color: 'var(--chai-brown)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  boxShadow: '0 2px 6px rgba(43, 33, 27, 0.08)',
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--chai-terracotta)';
                  e.currentTarget.style.color = '#F8F3E8';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = '#F8F3E8';
                  e.currentTarget.style.color = 'var(--chai-brown)';
                }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </button>
            </div>
          </div>

          {/* Right Column: Live Context & Step Navigation */}
          <div>
            {/* Step Badge */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
              <span
                className="font-mono"
                style={{
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  backgroundColor: 'var(--chai-terracotta)',
                  color: '#F8F3E8',
                  padding: '4px 10px',
                  borderRadius: '4px',
                  letterSpacing: '0.05em',
                }}
              >
                STEP {activeSlide.step}
              </span>
              <span
                className="font-mono"
                style={{
                  fontSize: '0.82rem',
                  color: 'var(--chai-muted-brown)',
                  letterSpacing: '0.04em',
                }}
              >
                // {activeSlide.badge.toUpperCase()}
              </span>
            </div>

            {/* Active Slide Title */}
            <h3
              className="font-display"
              style={{
                fontSize: 'clamp(2rem, 3.2vw, 2.7rem)',
                color: 'var(--chai-brown)',
                lineHeight: 1.18,
                marginBottom: '0.5rem',
              }}
            >
              {activeSlide.title}
            </h3>

            <div
              className="font-mono"
              style={{
                fontSize: '0.9rem',
                color: 'var(--chai-terracotta)',
                fontWeight: 600,
                marginBottom: '1.25rem',
              }}
            >
              {activeSlide.subtitle}
            </div>

            <p
              style={{
                fontSize: '1.1rem',
                color: 'var(--chai-coffee)',
                lineHeight: 1.68,
                marginBottom: '2.5rem',
              }}
            >
              {activeSlide.description}
            </p>

            {/* Step Selection List */}
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.65rem',
              }}
            >
              {slides.map((slide, idx) => {
                const isActive = idx === currentIndex;
                return (
                  <button
                    key={slide.id}
                    type="button"
                    onClick={() => goToSlide(idx)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0.75rem 1.15rem',
                      borderRadius: '6px',
                      border: isActive ? '1px solid var(--chai-terracotta)' : '1px solid var(--chai-border)',
                      backgroundColor: isActive ? '#F8F3E8' : 'transparent',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.2s ease',
                    }}
                    onMouseOver={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.backgroundColor = 'rgba(248, 243, 232, 0.6)';
                      }
                    }}
                    onMouseOut={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                      <span
                        className="font-mono"
                        style={{
                          fontSize: '0.75rem',
                          color: isActive ? 'var(--chai-terracotta)' : 'var(--chai-muted-brown)',
                          fontWeight: 600,
                        }}
                      >
                        {slide.step}
                      </span>
                      <span
                        style={{
                          fontSize: '0.92rem',
                          fontWeight: isActive ? 600 : 500,
                          color: isActive ? 'var(--chai-brown)' : 'var(--chai-coffee)',
                        }}
                      >
                        {slide.title}
                      </span>
                    </div>

                    <span
                      className="font-mono"
                      style={{
                        fontSize: '0.75rem',
                        color: isActive ? 'var(--chai-terracotta)' : 'var(--chai-muted-brown)',
                      }}
                    >
                      {isActive ? '● VIEWING' : 'VIEW →'}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
