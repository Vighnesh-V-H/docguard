import Link from "next/link";

const sampleText = `From: Alex Morgan <alex@example.com>
To: finance@docguard.com
Re: Vendor payment #INV-4421

Please charge card <em class="scanner__entity scanner__entity--warm">4242 4242 4242 4242</em>
and reach me at <em class="scanner__entity">(555) 010-2044</em>.
My SSN is <em class="scanner__entity scanner__entity--warm">***-**-2911</em>.`;

const features = [
  {
    title: "Entity Detection",
    desc: "Identifies names, emails, phone numbers, financial data, and dozens of other PII types using a local AI engine.",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
    ),
  },
  {
    title: "File Support",
    desc: "Upload PDFs, emails (.eml), and plain text files. Text is extracted automatically and analyzed in seconds.",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <polyline points="10 9 9 9 8 9" />
      </svg>
    ),
  },
  {
    title: "Local Processing",
    desc: "All analysis runs on your machine. No data is sent to external servers — documents never leave your control.",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
        <path d="M7 11V7a5 5 0 0 1 10 0v4" />
      </svg>
    ),
  },
];

const steps = [
  { title: "Paste or upload", desc: "Start with any text or document containing sensitive information." },
  { title: "Analyze for PII", desc: "The local engine scans for names, emails, financial data, and more." },
  { title: "Review & redact", desc: "Inspect findings, then redact with a single click." },
];

export default function LandingPage() {
  return (
    <div className="landing">
      <div className="landing__bg" aria-hidden="true">
        <div className="landing__glow" />
      </div>

      <section className="landing__hero">
        <div className="landing__eyebrow">
          <span className="landing__dot" />
          Local-first document security
        </div>
        <h1 className="landing__title">
          Protect <span>sensitive data</span> before it leaves your hands.
        </h1>
        <p className="landing__subtitle">
          Detect and redact personally identifiable information — names, emails,
          phone numbers, financial data — in any document. Processing stays local.
          Nothing leaves your machine.
        </p>
        <div className="landing__actions">
          <Link href="/analyze" className="landing__btn landing__btn--primary">
            Start Analyzing
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </Link>
          <Link href="/redact" className="landing__btn landing__btn--secondary">
            Go to Redaction
          </Link>
        </div>
      </section>

      <section className="landing__scanner" aria-label="Live preview">
        <div className="scanner__beam" aria-hidden="true" />
        <p className="scanner__text" dangerouslySetInnerHTML={{ __html: sampleText }} />
        <div className="scanner__tag">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          Live scan — entities highlighted
        </div>
      </section>

      <section className="landing__features">
        <h2 className="landing__section-title">Everything you need</h2>
        <div className="features__grid">
          {features.map((f) => (
            <div key={f.title} className="feature-card">
              <div className="feature-card__icon">{f.icon}</div>
              <h3 className="feature-card__title">{f.title}</h3>
              <p className="feature-card__desc">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="landing__how">
        <h2 className="landing__section-title">How it works</h2>
        <div className="how__steps">
          {steps.map((s, i) => (
            <div key={s.title} className="how__step">
              <div className="how__number">{String(i + 1).padStart(2, "0")}</div>
              <h3 className="how__title">{s.title}</h3>
              <p className="how__desc">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="landing__cta">
        <h2 className="landing__cta-title">Ready to secure your documents?</h2>
        <p className="landing__cta-desc">
          No sign-ups, no data leaves your machine. Start analyzing instantly.
        </p>
        <div className="landing__actions">
          <Link href="/analyze" className="landing__btn landing__btn--primary">
            Get Started
          </Link>
          <Link href="/analyze/file" className="landing__btn landing__btn--secondary">
            Upload a File
          </Link>
        </div>
      </section>
    </div>
  );
}
