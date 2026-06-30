type OutputPanelProps = {
  title: string;
  summary: string;
  body: string;
  details: string[];
};

export default function OutputPanel({ title, summary, body, details }: OutputPanelProps) {
  return (
    <aside className="panel output-panel" aria-live="polite">
      <div className="panel-head">
        <p>Output</p>
        <span>Results appear below.</span>
      </div>

      <div className="result-summary">
        <p>{title}</p>
        <span>{summary}</span>
      </div>

      <pre>{body}</pre>

      <ul className="result-details">
        {details.map((detail) => (
          <li key={detail}>{detail}</li>
        ))}
      </ul>
    </aside>
  );
}

export function OutputEmpty() {
  return (
    <aside className="panel output-panel" aria-live="polite">
      <div className="panel-head">
        <p>Output</p>
        <span>Results appear below.</span>
      </div>
      <div className="empty-state">
        <p>Ready</p>
        <span>Submit text or a file to see results here.</span>
      </div>
    </aside>
  );
}
