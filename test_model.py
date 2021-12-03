from datetime import date, timedelta
import pytest

from model import Batch, OrderLine, allocate, OutOfStockException

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)

def make_batch_and_line(sku, batch_qty, line_qty):
    return (
        Batch("batch-001", sku, batch_qty, date.today()),
        OrderLine("order-123", sku, line_qty)
    )

def test_allocating_to_a_batch_reduces_the_available_quantity():
    batch, line = make_batch_and_line("sofa",10,2)
    batch.allocate(line)
    assert batch.available_quantity == 8


def test_can_allocate_if_available_greater_than_required():
    large_batch, line = make_batch_and_line("sofa",10,2)
    assert large_batch.can_allocate(line)


def test_cannot_allocate_if_available_smaller_than_required():
    small_batch, line = make_batch_and_line("sofa",2,10)
    assert small_batch.can_allocate(line) is False


def test_can_allocate_if_available_equal_to_required():
    batch, line = make_batch_and_line("sofa",10,10)
    assert batch.can_allocate(line) is True


def test_cannot_allocate_if_skus_do_not_match():
    batch = Batch("batch-001", "sofa legal", 10, date.today())
    different_sku_line = OrderLine("order-123", "cama chata", 2)
    assert batch.can_allocate(different_sku_line) is False


def test_can_only_deallocate_allocated_lines():
    batch, unallocated_line = make_batch_and_line("QUADRO-DECORATIVO", 20, 2)
    batch.dealocate(unallocated_line)
    assert batch.available_quantity == 20

def test_allocation_is_idempotent():
    batch, line = make_batch_and_line("VUE_DESK", 20, 2)
    batch.allocate(line)
    batch.allocate(line)
    assert batch.available_quantity == 18


def test_can_dealocate_line():
    batch, line = make_batch_and_line("VUE_DESK", 20, 2)
    batch.allocate(line)
    batch.dealocate(line)
    assert batch.available_quantity == 20


def test_batch_equality_by_reference():
    batch1 = Batch("batch-001", "sofa legal", 10, date.today())
    batch2 = Batch("batch-001", "sofa chato", 10, date.today())
    assert batch1 == batch2


def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = Batch("in-stock-batch", "ABAJUR-AZUL", 100, None)
    tomorrow_shipment_batch = Batch("in-stock-batch", "ABAJUR-AZUL", 100, tomorrow)
    line = OrderLine("orderref", "ABAJUR-AZUL", 10)

    allocate(line, [tomorrow_shipment_batch, in_stock_batch])

    assert in_stock_batch.available_quantity == 90
    assert tomorrow_shipment_batch.available_quantity == 100


def test_prefers_earlier_batches():
    today_shipment_batch = Batch("in-stock-batch", "ABAJUR-AZUL", 100, today)
    tomorrow_shipment_batch = Batch("in-stock-batch", "ABAJUR-AZUL", 100, tomorrow)
    line = OrderLine("orderref", "ABAJUR-AZUL", 10)

    allocate(line, [tomorrow_shipment_batch, today_shipment_batch])

    assert today_shipment_batch.available_quantity == 90
    assert tomorrow_shipment_batch.available_quantity == 100

def test_raises_out_of_stock_exception_if_cannot_allocate():
    batch = Batch("batch1", "SMALL-SPON", 10, eta=today)
    line = OrderLine("orderref", "SMALL-SPON", 10)
    
    allocate(line, [batch])

    with pytest.raises(OutOfStockException, match="SMALL-SPON"):
        allocate(line, [batch])

