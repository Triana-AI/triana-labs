/** Triana mark: bounded pentagon, dashed path, green terminal node. */
export function Logo({ size = 22 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      aria-hidden="true"
      focusable="false"
    >
      <path
        d="M32 5 L59 25 L48.5 57 H15.5 L5 25 Z"
        stroke="currentColor"
        strokeWidth="5"
        strokeLinejoin="round"
      />
      <path
        d="M17 47 C30 47 45 40 47 22"
        stroke="var(--logo-blue)"
        strokeWidth="4.5"
        strokeLinecap="round"
        strokeDasharray="1 7"
      />
      <circle cx="48" cy="20" r="7.5" fill="var(--accent)" />
    </svg>
  );
}
