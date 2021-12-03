from dataclasses import dataclass
from datetime import date
from typing import List, Optional, NewType

Quantity = NewType("Quantity", int)
Sku = NewType("Sku", str)
Reference = NewType("Reference", str)


@dataclass(frozen=True)
class OrderLine:
    orderid: str
    sku: Sku
    qty: Quantity


class Batch:
    def __init__(self, ref: Reference, sku: Sku, qty: Quantity, eta: Optional[date]):
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations = set()

    def __eq__(self, other):
        if isinstance(other, Batch):
            return self.reference == other.reference
        return NotImplemented

    def __hash__(self):
        return hash(self.reference)

    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def __repr__(self):
        return f'Batch(reference={self.reference}, sku={self.sku}, allocated_quantity={self.allocated_quantity}, available_quantity={self.available_quantity}, eta={self.eta}'

    @property
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        return self.available_quantity >= line.qty and self.sku == line.sku

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def dealocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)

class OutOfStockException(Exception):
    def __init__(self, sku: Sku, message: str = "out of stock"):
        self.sku = sku
        self.message = message
        super().__init__(self.message)
    
    def __str__(self):
        return f'{self.sku} -> {self.message}'


def allocate(line: OrderLine, batches: List[Batch]):
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
        batch.allocate(line)
        return batch.reference
    except StopIteration:
        raise OutOfStockException(line.sku)