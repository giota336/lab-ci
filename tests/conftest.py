import pytest

from shop.cart import Cart


@pytest.fixture
def empty_cart() -> Cart:
    """Порожній кошик."""
    return Cart()


@pytest.fixture
def cart() -> Cart:
    """Кошик із трьома товарами на загальну суму 1000 грн."""
    c = Cart()
    c.add("book", 200.0, 2)  # 400
    c.add("pen", 50.0, 4)  # 200
    c.add("lamp", 400.0)  # 400
    return c
