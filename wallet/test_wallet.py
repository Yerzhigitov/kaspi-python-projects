import threading
import unittest
from decimal import Decimal

from wallet import Bank, InsufficientFunds, WalletError


class WalletTest(unittest.TestCase):
    def setUp(self):
        self.bank = Bank()
        self.a, self.b = self.bank.open_account(), self.bank.open_account()
        self.bank.deposit(self.a, "100.00")

    def test_transfer(self):
        self.bank.transfer(self.a, self.b, "30.555")
        self.assertEqual(self.bank.balance(self.a), Decimal("69.44"))
        self.assertEqual(self.bank.balance(self.b), Decimal("30.56"))

    def test_insufficient(self):
        with self.assertRaises(InsufficientFunds):
            self.bank.transfer(self.a, self.b, 1000)

    def test_bad_amount(self):
        with self.assertRaises(WalletError):
            self.bank.transfer(self.a, self.b, -5)

    def test_idempotency(self):
        t1 = self.bank.transfer(self.a, self.b, 10, key="req-1")
        t2 = self.bank.transfer(self.a, self.b, 10, key="req-1")
        self.assertIs(t1, t2)
        self.assertEqual(self.bank.balance(self.b), Decimal("10.00"))

    def test_concurrency(self):
        threads = [threading.Thread(target=self.bank.transfer, args=(self.a, self.b, 1)) for _ in range(100)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(self.bank.balance(self.a), Decimal("0.00"))
        self.assertEqual(self.bank.balance(self.b), Decimal("100.00"))


if __name__ == "__main__":
    unittest.main()
