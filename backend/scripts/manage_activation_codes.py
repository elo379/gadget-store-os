"""Generate or revoke organization activation codes without logging code values."""
import argparse
import getpass
import os
import re
from pathlib import Path

from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.activation.models import ActivationCode
from app.activation.service import CODE_ALPHABET, CODE_LENGTH, digest_code, generate_code, normalize_code
from app.db.mixins import utc_now

PRODUCTION_DIGESTS_ENV = "GSOS_PRODUCTION_ACTIVATION_DIGESTS"
PRODUCTION_ADVISORY_LOCK = 7319428162041


def generate_batch(count: int, output: Path, expires_in_days: int | None = None) -> None:
    if not 1 <= count <= 40:
        raise SystemExit("count must be between 1 and 40")
    if expires_in_days is not None:
        raise SystemExit("local inventory generation does not set expiry; seeded codes have no expiry")
    codes = [generate_code() for _ in range(count)]
    validate_batch(codes, count)
    output = output.expanduser().resolve()
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
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
    except Exception:
        if descriptor is not None:
            os.close(descriptor)
        if output_created:
            output.unlink(missing_ok=True)
        raise
    print(f"Generated {count} unique activation codes in a private file (mode 0600). No database was contacted.")


def validate_batch(codes: list[str], count: int) -> None:
    if len(codes) != count or len(set(codes)) != count:
        raise ValueError("activation-code batch has an invalid count or duplicates")
    for code in codes:
        normalized = normalize_code(code)
        if normalized != code or len(code) != CODE_LENGTH or any(char not in CODE_ALPHABET for char in code):
            raise ValueError("activation-code batch contains an invalid code")


def validate_digest_batch(digests: list[str]) -> list[str]:
    if len(digests) != 40:
        raise ValueError("exactly 40 activation-code digests are required")
    normalized = [digest.lower() for digest in digests]
    if len(set(normalized)) != 40:
        raise ValueError("activation-code digests must be unique")
    if any(re.fullmatch(r"[0-9a-f]{64}", digest) is None for digest in normalized):
        raise ValueError("activation-code digests must be 64-character hexadecimal SHA-256 values")
    return normalized


def seed_digest_batch(db, digests: list[str]) -> str:
    """Insert one operator-supplied digest batch, or safely verify its prior insert."""
    digests = validate_digest_batch(digests)
    if db.bind.dialect.name == "postgresql":
        db.execute(text(f"SELECT pg_advisory_xact_lock({PRODUCTION_ADVISORY_LOCK})"))

    issued = db.scalars(select(ActivationCode).where(ActivationCode.status == "issued")).all()
    digest_set = set(digests)
    if any(row.code_digest not in digest_set for row in issued):
        raise ValueError("production contains unrelated issued activation codes")

    rows_with_digest = db.scalars(
        select(ActivationCode).where(ActivationCode.code_digest.in_(digests))
    ).all()
    if len(rows_with_digest) == 40 and {row.code_digest for row in rows_with_digest} == digest_set:
        if any(row.status not in {"issued", "redeemed", "revoked", "expired"} for row in rows_with_digest):
            raise ValueError("existing activation batch failed verification")
        if any(
            row.status == "issued" and (
                row.organization_id is not None or row.redeemed_at is not None or row.expires_at is not None
            )
            for row in rows_with_digest
        ):
            raise ValueError("existing issued activation batch failed verification")
        return "verified"
    if issued or rows_with_digest:
        raise ValueError("production contains a partial or unrelated activation-code batch")

    now = utc_now()
    db.add_all([
        ActivationCode(
            code_digest=digest,
            status="issued",
            created_at=now,
            expires_at=None,
            redeemed_at=None,
            organization_id=None,
        )
        for digest in digests
    ])
    db.flush()
    inserted = db.scalars(select(ActivationCode).where(ActivationCode.code_digest.in_(digests))).all()
    if len(inserted) != 40 or any(
        row.status != "issued" or row.organization_id is not None or
        row.redeemed_at is not None or row.expires_at is not None
        for row in inserted
    ):
        raise RuntimeError("activation digest batch verification failed")
    return "inserted"


def export_digest_payload(input_path: Path, output_path: Path) -> None:
    """Write a private comma-separated digest payload without displaying it."""
    input_path = input_path.expanduser().resolve()
    output_path = output_path.expanduser().resolve()
    if input_path.stat().st_mode & 0o777 != 0o600:
        raise SystemExit("Plaintext inventory must have mode 0600")
    codes = input_path.read_text(encoding="utf-8").splitlines()
    validate_batch(codes, 40)
    digests = validate_digest_batch([digest_code(code) for code in codes])
    output_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(output_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii") as handle:
            handle.write(",".join(digests) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        output_path.unlink(missing_ok=True)
        raise
    print("Wrote a private 40-digest payload (mode 0600). Payload was not displayed.")


def production_engine():
    """Return the explicitly configured production engine; reject ambiguous targets."""
    database_url = os.environ.get("DATABASE_URL", "")
    if os.environ.get("ENVIRONMENT", "").strip().lower() != "production" or not database_url:
        raise SystemExit("Production seeding requires ENVIRONMENT=production and DATABASE_URL")
    try:
        parsed = make_url(database_url)
    except Exception:
        raise SystemExit("DATABASE_URL is invalid") from None
    host = (parsed.host or "").lower()
    database = (parsed.database or "").lower()
    if parsed.get_backend_name() != "postgresql" or not any(
        marker in database for marker in ("production", "prod")
    ) or any(marker in host or marker in database for marker in ("test", "staging")):
        raise SystemExit("DATABASE_URL does not identify a production PostgreSQL database")
    from app.db.url import database_url_for_environment

    try:
        return create_engine(database_url_for_environment(database_url, "production"), pool_pre_ping=True)
    except Exception:
        raise SystemExit("Production database engine could not be configured") from None


def seed_production_digests() -> None:
    if os.environ.get("ENVIRONMENT", "").strip().lower() != "production":
        raise SystemExit("Digest seeding requires ENVIRONMENT=production")
    payload = os.environ.get(PRODUCTION_DIGESTS_ENV)
    if not payload:
        raise SystemExit("Production activation digest variable is not configured")
    digests = payload.replace(",", " ").split()
    try:
        validate_digest_batch(digests)
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    engine = production_engine()
    try:
        factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        with factory.begin() as db:
            outcome = seed_digest_batch(db, digests)
        if outcome == "verified":
            print("Verified existing 40-code production digest batch; no changes made.")
        else:
            print("Inserted and verified 40 issued production activation-code digests.")
    except (SystemExit, ValueError):
        raise
    except Exception:
        raise SystemExit("Production activation digest seeding failed; no digest values were logged") from None
    finally:
        engine.dispose()


def seed_production(output: Path) -> None:
    """Safely seed one batch using an explicitly configured production URL."""
    engine = production_engine()
    output = output.expanduser().resolve()
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        with factory() as db:
            # Serialize operators so simultaneous runs cannot each observe an empty table.
            db.execute(text(f"SELECT pg_advisory_xact_lock({PRODUCTION_ADVISORY_LOCK})"))
            issued = db.scalars(select(ActivationCode).where(ActivationCode.status == "issued")).all()
            codes = None
            if output.exists():
                mode = output.stat().st_mode & 0o777
                existing_codes = output.read_text(encoding="utf-8").splitlines()
                validate_batch(existing_codes, 40)
                expected = {digest_code(code) for code in existing_codes}
                if mode != 0o600:
                    raise SystemExit("Existing plaintext inventory must have mode 0600")
                if len(issued) == 40 and {row.code_digest for row in issued} == expected:
                    print("Verified existing 40-code production batch; no changes made.")
                    return
                if issued:
                    raise SystemExit("Plaintext inventory does not match issued production codes")
                # Recover safely if the process stopped after writing the private file.
                codes = existing_codes
            elif issued:
                raise SystemExit("Production already has issued activation codes; refusing to create duplicates")

            if codes is None:
                codes = [generate_code() for _ in range(40)]
                validate_batch(codes, 40)
                descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                try:
                    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                        handle.write("\n".join(codes) + "\n")
                        handle.flush()
                        os.fsync(handle.fileno())
                except Exception:
                    output.unlink(missing_ok=True)
                    raise
            try:
                now = utc_now()
                db.add_all([
                    ActivationCode(code_digest=digest_code(code), status="issued", created_at=now)
                    for code in codes
                ])
                db.flush()
                rows = db.scalars(select(ActivationCode).where(
                    ActivationCode.code_digest.in_([digest_code(code) for code in codes])
                )).all()
                if len(rows) != 40 or any(
                    row.status != "issued" or row.organization_id is not None or
                    row.redeemed_at is not None or row.expires_at is not None
                    for row in rows
                ):
                    raise RuntimeError("production activation batch verification failed")
                db.commit()
            except Exception:
                db.rollback()
                output.unlink(missing_ok=True)
                raise
            print("Generated 40 unique activation codes.")
            print("Inserted 40 activation-code digests.")
            print("Verified 40 issued production codes.")
    finally:
        engine.dispose()


def revoke_code() -> None:
    from app.db.session import SessionLocal

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
    export = subparsers.add_parser("export-digests")
    export.add_argument("--input", type=Path, required=True)
    export.add_argument("--output", type=Path, required=True)
    production = subparsers.add_parser("seed-production")
    production.add_argument(
        "--output", type=Path,
        default=Path(__file__).resolve().parents[2] / "private" / "gsos-production-activation-codes.txt",
    )
    subparsers.add_parser("seed-production-digests")
    subparsers.add_parser("revoke")
    args = parser.parse_args()
    if args.action == "generate":
        generate_batch(args.count, args.output)
    elif args.action == "export-digests":
        export_digest_payload(args.input, args.output)
    elif args.action == "seed-production":
        seed_production(args.output)
    elif args.action == "seed-production-digests":
        seed_production_digests()
    else:
        revoke_code()


if __name__ == "__main__":
    main()
