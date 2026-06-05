import type { ReactNode } from "react";

interface PanelProps {
  children: ReactNode;
  title?: string;
  actions?: ReactNode;
}

export function Panel({ actions, children, title }: PanelProps) {
  return (
    <section className="panel">
      {title || actions ? (
        <header className="panel__header">
          {title ? <h2>{title}</h2> : <span />}
          {actions}
        </header>
      ) : null}
      {children}
    </section>
  );
}
