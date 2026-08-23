import React from 'react';
import { Header } from './sections/Header';
import { Hero } from './sections/Hero';
import { ProductIntro } from './sections/ProductIntro';
import { Features } from './sections/Features';
import { Assessment } from './sections/Assessment';
import { Download } from './sections/Download';
import { Footer } from './sections/Footer';

export const App: React.FC = () => {
  return (
    <div className="relative min-h-screen bg-[#F3EBDD] text-[#201A16] selection:bg-[#A9573D]/20 selection:text-[#2B211B]">
      {/* Subtle Paper Grain Noise Overlay */}
      <div className="paper-grain" aria-hidden="true" />

      {/* Structured Core Sections */}
      <Header />
      <main>
        <Hero />
        <ProductIntro />
        <Features />
        <Assessment />
        <Download />
      </main>
      <Footer />
    </div>
  );
};

export default App;
