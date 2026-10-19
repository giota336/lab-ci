from unittest.mock import Mock

import pytest

from shop.cart import Cart, Item

# ---------- add / items_count ----------


def test_new_cart_is_empty(empty_cart: Cart) -> None:
    assert empty_cart.items_count() == 0
    assert empty_cart.total() == 0


def test_add_single_item(empty_cart: Cart) -> None:
    empty_cart.add("book", 100.0)
    assert empty_cart.items_count() == 1
    assert empty_cart.total() == 100.0


def test_add_with_quantity(empty_cart: Cart) -> None:
    empty_cart.add("pen", 10.0, 5)
    assert empty_cart.items_count() == 5
    assert empty_cart.total() == 50.0


def test_add_same_item_twice_increases_qty(empty_cart: Cart) -> None:
    empty_cart.add("pen", 10.0, 2)
    empty_cart.add("pen", 10.0, 3)
    assert empty_cart.items_count() == 5


def test_add_same_name_different_price_keeps_first_price(empty_cart: Cart) -> None:
    """Рішення: при повторному додаванні товару з тією ж назвою зберігається
    ціна першого додавання, нова ціна ігнорується (збільшується лише кількість)."""
    empty_cart.add("book", 100.0)
    empty_cart.add("book", 150.0)
    assert empty_cart.items_count() == 2
    assert empty_cart.total() == 200.0


def test_add_free_item_allowed(empty_cart: Cart) -> None:
    empty_cart.add("gift", 0.0)
    assert empty_cart.items_count() == 1
    assert empty_cart.total() == 0


def test_add_negative_price_raises(empty_cart: Cart) -> None:
    with pytest.raises(ValueError, match="price must be non-negative"):
        empty_cart.add("book", -1.0)


@pytest.mark.parametrize("qty", [0, -1])
def test_add_non_positive_qty_raises(empty_cart: Cart, qty: int) -> None:
    with pytest.raises(ValueError, match="qty must be positive"):
        empty_cart.add("book", 10.0, qty)


# ---------- remove ----------


def test_remove_item(cart: Cart) -> None:
    cart.remove("pen")
    assert cart.items_count() == 3
    assert cart.total() == 800.0


def test_remove_missing_item_raises(cart: Cart) -> None:
    with pytest.raises(KeyError):
        cart.remove("phone")


# ---------- total / discount ----------


def test_total_without_discount(cart: Cart) -> None:
    assert cart.total() == 1000.0


@pytest.mark.parametrize(
    ("discount", "expected"),
    [
        (0, 1000.0),  # нижня межа
        (0.5, 995.0),
        (10, 900.0),
        (99.99, 0.1),
        (100, 0.0),  # верхня межа
    ],
)
def test_total_with_discount_boundaries(cart: Cart, discount: float, expected: float) -> None:
    assert cart.total(discount) == pytest.approx(expected)


@pytest.mark.parametrize("discount", [-0.01, 100.01, -50, 150])
def test_total_invalid_discount_raises(cart: Cart, discount: float) -> None:
    with pytest.raises(ValueError, match="discount_percent"):
        cart.total(discount)


def test_total_float_precision(empty_cart: Cart) -> None:
    empty_cart.add("a", 0.1)
    empty_cart.add("b", 0.2)
    assert empty_cart.total() == pytest.approx(0.3)


# ---------- total_in (mock / stub RateProvider) ----------


def test_total_in_uses_rate_provider(cart: Cart) -> None:
    rates = Mock()
    rates.get_rate.return_value = 40.0
    assert cart.total_in("USD", rates) == 25.0
    rates.get_rate.assert_called_once_with("USD")


class FakeRates:
    """Власна заглушка (stub) замість реального API курсів."""

    def __init__(self, rates: dict[str, float]) -> None:
        self._rates = rates

    def get_rate(self, currency: str) -> float:
        return self._rates[currency]


def test_total_in_with_stub(cart: Cart) -> None:
    assert cart.total_in("EUR", FakeRates({"EUR": 50.0})) == 20.0


@pytest.mark.parametrize("rate", [0.0, -1.0])
def test_total_in_invalid_rate_raises(cart: Cart, rate: float) -> None:
    rates = Mock()
    rates.get_rate.return_value = rate
    with pytest.raises(ValueError, match="rate must be positive"):
        cart.total_in("USD", rates)


# ---------- most_expensive (TDD) ----------


def test_most_expensive_empty_cart_returns_none(empty_cart: Cart) -> None:
    assert empty_cart.most_expensive() is None


def test_most_expensive_returns_item_with_max_unit_price(cart: Cart) -> None:
    assert cart.most_expensive() == Item("lamp", 400.0, 1)


def test_most_expensive_uses_unit_price_not_sum(empty_cart: Cart) -> None:
    empty_cart.add("pen", 10.0, 100)  # сума 1000, але ціна одиниці лише 10
    empty_cart.add("book", 200.0, 1)
    result = empty_cart.most_expensive()
    assert result is not None
    assert result.name == "book"


# ---------- format_total ----------


def test_format_total(cart: Cart) -> None:
    assert cart.format_total() == "1000.00 UAH"
