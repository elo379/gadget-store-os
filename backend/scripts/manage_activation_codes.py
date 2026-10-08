"""Generate or revoke organization activation codes without logging code values."""
import argparse
import getpass
import os
from datetime import timedelta
from pathlib import Path

from sqlalchemy import select

from app.activation.models import ActivationCode
from app.activation.service import digest_code, generate_code
from app.db.mixins import utc_now
from app.db.session import SessionLocal


def generate_batch(count: int, output: Path, expires_in_days: int | None) -> None:
    if not 1 <= count <= 40:
        raise SystemExit("count must be between 1 and 40")
    codes = [generate_code() for _ in range(count)]
    now = utc_now()
    expiry = now + timedelta(days=expires_in_days) if expires_in_days else None
    output = output.expanduser().resolve()
    descriptor = None
    output_created = False
    try:
        descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        output_created = True
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = None
            handle.write("\n".join(codes) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        with SessionLocal.begin() as db:
            db.add_all([
                ActivationCode(
                    code_digest=digest_code(code),
                    status="issued",
                    created_at=now,
                    expires_at=expiry,
                )
                for code in codes
            ])
    except Exception:
        if descriptor is not None:
            os.close(descriptor)
        if output_created:
            output.unlink(missing_ok=True)
        raise
    print(f"Created {count} activation codes in {output} (file mode 0600). Store the file securely.")


def revoke_code() -> None:
    code = getpass.getpass("Activation code to revoke: ")
    try:
        digest = digest_code(code)
    except ValueError as exc:
        raise SystemExit("Malformed activation code") from exc
    with SessionLocal.begin() as db:
        row = db.scalar(select(ActivationCode).where(ActivationCode.code_digest == digest))
        if row is None or row.status != "issued":
            raise SystemExit("No issued activation code matched; no change made.")
        row.status = "revoked"
    print("Activation code revoked.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    generate = subparsers.add_parser("generate")
    generate.add_argument("--count", type=int, default=40)
    generate.add_argument("--output", type=Path, required=True)
    generate.add_argument("--expires-in-days", type=int)
    subparsers.add_parser("revoke")
    args = parser.parse_args()
    if args.action == "generate":
        if args.expires_in_days is not None and args.expires_in_days < 1:
            parser.error("--expires-in-days must be positive")
        generate_batch(args.count, args.output, args.expires_in_days)
    else:
        revoke_code()


if __name__ == "__main__":
    main()
