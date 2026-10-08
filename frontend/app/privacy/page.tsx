import Link from "next/link";
import { PageHeader } from "@/components/page-header";

export default function PrivacyPage() {
  return (
    <div className="space-y-5">
      <PageHeader eyebrow="Trust · Data use" title="Privacy" description="What GSOS stores to run your organization and how store administrators can manage access." />
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-2xl border border-[var(--border)] bg-white p-5 sm:p-6">
          <h2 className="text-base font-semibold">Information in GSOS</h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-[var(--muted)]">
            <li>Account email, password hash, role, permissions, session and passkey records.</li>
            <li>Organization, store, branch, staff, supplier and customer details entered by the team.</li>
            <li>Products, stock, purchases, sales, payments, expenses, returns and reports.</li>
            <li>Device identifiers such as IMEI, serial number, model, color, source and receiving details.</li>
            <li>Attendance and audit history for business and security actions.</li>
            <li>Browser storage may hold authentication tokens and saved offline drafts on that device.</li>
          </ul>
        </section>
        <section className="rounded-2xl border border-[var(--border)] bg-white p-5 sm:p-6">
          <h2 className="text-base font-semibold">Use and access</h2>
          <p className="mt-3 text-sm leading-6 text-[var(--muted)]">GSOS uses these records to authenticate staff, enforce organization permissions, operate store workflows, calculate reports and retain an audit trail. Access depends on the user’s organization, role and assigned permissions. Organization owners should create accounts only for authorized personnel and remove access when it is no longer needed.</p>
          <p className="mt-3 text-sm leading-6 text-[var(--muted)]">The camera is requested only when a user opens the scanner. GSOS uses the camera stream to read a barcode or device identifier; it does not request geolocation. If camera access is denied or unavailable, identifiers can be entered manually.</p>
        </section>
        <section className="rounded-2xl border border-[var(--border)] bg-white p-5 sm:p-6">
          <h2 className="text-base font-semibold">Retention and control</h2>
          <p className="mt-3 text-sm leading-6 text-[var(--muted)]">Business records remain available in the organization according to the configured hosting and retention practices. Owners should follow their legal and business retention obligations. Ask the GSOS service operator about hosting, backup, export or deletion requests; do not enter payment-card secrets or unrelated personal data into notes.</p>
          <p className="mt-3 text-sm leading-6 text-[var(--muted)]">This page describes application behavior and is not a statement of compliance or legal advice. The organization operating GSOS remains responsible for its staff and customer notices.</p>
        </section>
        <section className="rounded-2xl border border-[var(--border)] bg-white p-5 sm:p-6">
          <h2 className="text-base font-semibold">Need help?</h2>
          <p className="mt-3 text-sm leading-6 text-[var(--muted)]">For access or data questions, contact your organization owner or the person who operates your GSOS deployment. See the <Link href="/guide" className="font-semibold text-emerald-800 underline underline-offset-2">role guide</Link> for everyday account and store workflows.</p>
        </section>
      </div>
    </div>
  );
}
