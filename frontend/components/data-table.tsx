type Column = {
  label: string;
  key: string;
};

export function DataTable({
  columns,
  rows,
}: {
  columns: Column[];
  rows: Record<string, string>[];
}) {
  return (
    <div className="overflow-hidden rounded-2xl border border-[var(--border)] bg-white">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[680px] border-collapse text-left">
          <thead>
            <tr className="border-b border-[var(--border)] bg-[#fafaf8]">
              {columns.map((column) => (
                <th key={column.key}
                  className="px-5 py-3.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-[var(--muted)]">
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={index} className="border-b border-[var(--border)] last:border-0 hover:bg-[#fafaf8]">
                {columns.map((column) => (
                  <td key={column.key} className="px-5 py-4 text-sm">{row[column.key]}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
