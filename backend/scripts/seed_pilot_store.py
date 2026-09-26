import uuid
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.organizations.service import create_organization
from app.products.service import create_product
from app.inventory.service import create_location, create_inventory_item
from app.suppliers.schemas import SupplierCreate
from app.suppliers.service import create_supplier


DATABASE_URL = "sqlite:///./pilot_store.db"

engine = create_engine(DATABASE_URL)


def main():
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        suffix = uuid.uuid4().hex[:8]

        organization = create_organization(
            db=db,
            name="GSOS Pilot Store",
            slug=f"gsos-pilot-{suffix}",
            owner_email=f"owner-{suffix}@pilot.local",
            owner_password="PilotPassword123!",
        )

        location = create_location(
            db=db,
            organization_id=organization.id,
            name="Main Store",
            description="Primary pilot inventory location",
        )

        phone = create_product(
            db=db,
            organization_id=organization.id,
            name="Pilot Smartphone",
            sku=f"PILOT-PHONE-{suffix}",
            brand="Pilot",
            model="P1",
            is_serialized=True,
        )

        accessory = create_product(
            db=db,
            organization_id=organization.id,
            name="Pilot USB-C Cable",
            sku=f"PILOT-CABLE-{suffix}",
            brand="Pilot",
            model="C1",
            is_serialized=False,
        )

        create_inventory_item(
            db=db,
            organization_id=organization.id,
            product_id=phone.id,
            location_id=location.id,
            quantity=5,
        )

        create_inventory_item(
            db=db,
            organization_id=organization.id,
            product_id=accessory.id,
            location_id=location.id,
            quantity=25,
        )

        supplier = create_supplier(
            db=db,
            payload=SupplierCreate(
                organization_id=organization.id,
                name="Pilot Supplier",
                contact_person="Pilot Contact",
                phone="08000000000",
                email=f"supplier-{suffix}@pilot.local",
            ),
        )

        print("PILOT STORE CREATED")
        print(f"Organization: {organization.id}")
        print(f"Owner: {organization.memberships[0].user.email}")
        print(f"Location: {location.id}")
        print(f"Phone: {phone.id}")
        print(f"Accessory: {accessory.id}")
        print(f"Supplier: {supplier.id}")


if __name__ == "__main__":
    main()
