interface StatusBadgeProps {
  tone: "success" | "warning" | "danger" | "neutral";
  children: string;
}

export function StatusBadge({ children, tone }: StatusBadgeProps) {
  return <span className={`status-badge status-badge--${tone}`}>{children}</span>;
}
