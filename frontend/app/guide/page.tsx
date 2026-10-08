import { PageHeader } from "@/components/page-header";

const guides = [
  {
    role: "Owner",
    intro: "You control the organization, its people and store setup.",
    steps: ["Sign in and review the dashboard.", "Open Settings → Organization to set up stores, branches, staff and manager permissions.", "Create product definitions, then add suppliers and purchase orders.", "Receive stock into the right branch. Record each phone’s IMEI or serial; use quantities for accessories.", "Use Stock Counts to open a count, scan devices or count quantities, review differences and complete reconciliation.", "Use Point of Sale to select products, customer and payment; check the receipt and sale history.", "Review customers, supplier activity, finance, reports, attendance and Audit Log regularly."],
  },
  {
    role: "Manager",
    intro: "Work in the store or branch assigned to you. Your owner controls which actions are available.",
    steps: ["Sign in and confirm the active organization and store context.", "Use the dashboard to review sales, stock and operational alerts.", "Receive and move stock, scan device identifiers, and run stock counts when your permissions allow.", "Record sales and customer details at checkout; report returns through the returns workflow.", "Use purchasing, staff, attendance and reports only when those permissions appear in your account.", "Ask the owner to grant or remove permissions; do not share accounts or work around an access denial."],
  },
  {
    role: "Staff",
    intro: "Use your assigned workspace and record each action under your own account.",
    steps: ["Sign in with your account and check the selected store or branch.", "Use Inventory or Device Registry to find stock. Scan a barcode or IMEI when the scanner is available, or type it manually.", "Use Point of Sale to add items, select the customer and record the payment accurately.", "Clock in and out in Attendance if enabled for your role.", "Tell your manager about damaged, missing or unexpected stock; do not adjust counts unless authorized.", "Owner settings, staff permissions and other restricted areas are hidden or denied by your role."],
  },
];

export default function GuidePage() {
  return (
    <div className="space-y-5">
      <PageHeader eyebrow="Help · Daily workflows" title="Store role guide" description="A quick walk-through for owners, managers and staff. Your available screens depend on your permissions." />
      <div className="grid gap-4 xl:grid-cols-3">
        {guides.map((guide) => (
          <section key={guide.role} className="rounded-2xl border border-[var(--border)] bg-white p-5 sm:p-6">
            <h2 className="text-lg font-semibold">{guide.role}</h2>
            <p className="mt-1 text-sm leading-6 text-[var(--muted)]">{guide.intro}</p>
            <ol className="mt-4 list-decimal space-y-3 pl-5 text-sm leading-6 text-neutral-700">
              {guide.steps.map((step) => <li key={step}>{step}</li>)}
            </ol>
          </section>
        ))}
      </div>
      <p className="text-sm text-[var(--muted)]">A printable staff copy is available in <code>docs/store-guides.md</code>.</p>
    </div>
  );
}
