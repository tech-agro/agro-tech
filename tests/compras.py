"""Manual smoke test for purchases (repository). Usage: python -m tests.compras"""

from app.compras.repository import OrderRepository

repo = OrderRepository()
print(repo.list())
