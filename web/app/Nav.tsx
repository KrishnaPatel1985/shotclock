"use client";

import { useEffect, useState } from "react";

export default function Nav({ logo, repo }: { logo: React.ReactNode; repo: string }) {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 8);
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);
  return (
    <nav className={`nav ${scrolled ? "scrolled" : ""}`}>
      <div className="wrap">
        <a className="brand" href="#">{logo}<span className="word">Shot<span>clock</span></span></a>
        <div className="navlinks">
          <a className="hide-sm" href="#how">How it works</a>
          <a className="hide-sm" href="#results">Results</a>
          <a className="hide-sm" href="#sources">Sources</a>
          <a href={repo} target="_blank" rel="noopener noreferrer">GitHub</a>
          <a className="btn primary sm" href="#try" style={{ color: "#fff" }}>Try it</a>
        </div>
      </div>
    </nav>
  );
}
