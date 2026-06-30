export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer__inner">
        <span className="footer__text">
          &copy; {new Date().getFullYear()} DocGuard
        </span>
        <span className="footer__text footer__text--faint">
          Processing stays local. Nothing leaves your machine.
        </span>
      </div>
    </footer>
  );
}
