from abc import ABC, abstractmethod
from typing import List

from sqlalchemy.orm.session import Session

from model import Batch, OrderLine, BatchReference


class AbstractRepository(ABC):
    
    @abstractmethod
    def add(self, batch: Batch) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, reference) -> Batch:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, batch: Batch):
        self.session.add(batch)

    def get(self, reference) -> Batch:
        return self.session.query(Batch).filter_by(reference=reference).one()

    def list(self):
        return self.session.query(Batch).all()
        

class RawSqlRepository(AbstractRepository):

    def __init__(self, session) -> None:
        self.session = session

    def add(self, batch: Batch) -> None:
        self.session.execute(
            "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
            ' VALUES (:reference, :sku , :_purchased_quantity, :eta)',
            dict(
                reference=batch.reference,
                sku=batch.sku,
                _purchased_quantity=batch._purchased_quantity,
                eta=batch.eta
            )
        )

    def get(self, reference) -> Batch:
        [[id, reference, sku, _purchased_quantity, eta]] = self.session.execute(
        "SELECT id, reference, sku, _purchased_quantity, eta FROM batches WHERE reference=:reference",
        dict(reference=reference),)

        batch = Batch(reference, sku, _purchased_quantity, eta)

        orderlines_ids_query_from_allocations = self.session.execute(
        "SELECT orderline_id FROM allocations WHERE batch_id=:batch_id",
        dict(batch_id=id),)

        orderlines_ids = [dict(orderline_id=id) for [id] in orderlines_ids_query_from_allocations]

        orderlines_query = self.session.execute(
        "SELECT orderid, sku, qty FROM order_lines WHERE id=:orderline_id",
        *orderlines_ids)
    
        for orderid, sku, qty in orderlines_query:
            orderline = OrderLine(orderid, sku, qty)
            batch.allocate(orderline)
 
        return batch
    

class FakeRepository(AbstractRepository):

    def __init__(self, batches: List[Batch]):
        self._batches = set(batches)

    def add(self, batch: Batch):
        self._batches.add(batch)

    def get(self, reference: BatchReference):
        return next(b for b in self._batches if b.reference == reference)
    
    def list(self):
        return list(self._batches)
        