from sqlalchemy.orm.session import Session

from model import Batch, BatchReference, OrderLine
from repository import RawSqlRepository

def test_repository_can_save_a_batch(session: Session):
    batch = Batch("batch1", 'FOGÃO ENFERRUJADO', 100, eta=None)

    repo = RawSqlRepository(session)
    repo.add(batch)
    session.commit()

    rows = session.execute(
        'SELECT reference, sku, _purchased_quantity, eta FROM "batches"'
    )
    assert list(rows) == [("batch1", 'FOGÃO ENFERRUJADO', 100, None)]

def insert_order_line(session: Session) -> int:
    session.execute(
        "INSERT INTO order_lines (orderid, sku, qty)"
        ' VALUES ("order1", "FOGÃO-ENFERRUJADO", 12)'
    )
    [[orderline_id]] = session.execute(
        "SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku",
        dict(orderid="order1", sku="FOGÃO-ENFERRUJADO"),
    )
    return orderline_id

def insert_batch(session: Session, batch_reference: BatchReference) -> int:
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
        ' VALUES (:batch_reference, "FOGÃO-ENFERRUJADO", 100, null)',
        dict(batch_reference=batch_reference),
    )
    [[batch_id]] = session.execute(
        'SELECT id from batches WHERE reference=:batch_reference AND sku="FOGÃO-ENFERRUJADO"',
        dict(batch_reference=batch_reference)
    )
    return batch_id

def insert_allocation(session: Session, orderline_id: int, batch_id: int):
    session.execute(
        "INSERT INTO allocations (orderline_id, batch_id)"
        ' VALUES (:orderline_id, :batch_id)',
        dict(orderline_id=orderline_id, batch_id=batch_id)
    )

def test_repository_can_retrieve_a_batch_with_allocations(session: Session):
    orderline_id = insert_order_line(session)
    batch1_id = insert_batch(session, "batch1")
    insert_batch(session, "batch2")
    insert_allocation(session, orderline_id, batch1_id)

    repo = RawSqlRepository(session)
    retrieved_batch = repo.get("batch1")

    expected = Batch("batch1", "FOGÃO-ENFERRUJADO", 100, eta=None)
    assert retrieved_batch == expected #Batch.__eq__ only compares reference
    assert retrieved_batch.sku == expected.sku
    assert retrieved_batch._purchased_quantity == expected._purchased_quantity
    assert retrieved_batch._allocations == {
        OrderLine("order1", "FOGÃO-ENFERRUJADO", 12)
    }
    