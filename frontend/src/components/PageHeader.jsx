export function PageHeader({ label, title, description, actions }) {
  return (
    <div className="mb-8 flex flex-col justify-between gap-4 border-b border-border pb-6 sm:flex-row sm:items-end">
      <div>
        {label && (
          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground">
            {label}
          </p>
        )}
        <h1 className="mt-1 font-heading text-3xl font-light tracking-tight">{title}</h1>
        {description && <p className="mt-2 max-w-2xl text-sm text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  );
}
