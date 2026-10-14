from datetime import date
from math import isfinite


class Product:
    def __init__(self, id, name, price, quantity):
        self.id = str(id).strip()
        self.name = str(name).strip()

        if not self.id:
            raise ValueError("Mã sản phẩm không được để trống.")

        if not self.name:
            raise ValueError("Tên sản phẩm không được để trống.")

        self.price = price
        self.quantity = quantity

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Giá bán phải là số.")

        if not isfinite(value) or value < 0:
            raise ValueError("Giá bán phải hữu hạn và không được âm.")

        self._price = value

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, value):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("Số lượng phải là số nguyên.")

        if value < 0:
            raise ValueError("Số lượng tồn kho không được âm.")

        self._quantity = value

    def display_info(self):
        print(
            f"{self.id} | {self.name} | "
            f"Giá: {self.price:,.0f} đồng | Tồn: {self.quantity}"
        )

    def calculate_value(self):
        return self.price * self.quantity

    def to_dict(self):
        return {
            "type": "product",
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "quantity": self.quantity,
        }


class Electronic(Product):
    def __init__(self, id, name, price, quantity, warranty_months):
        super().__init__(id, name, price, quantity)
        self.warranty_months = warranty_months

    @property
    def warranty_months(self):
        return self._warranty_months

    @warranty_months.setter
    def warranty_months(self, value):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("Thời gian bảo hành phải là số nguyên.")

        if value < 0:
            raise ValueError("Thời gian bảo hành không được âm.")

        self._warranty_months = value

    def display_info(self):
        super().display_info()
        print(f"  Bảo hành: {self.warranty_months} tháng")

    def to_dict(self):
        data = super().to_dict()
        data["type"] = "electronic"
        data["warranty_months"] = self.warranty_months
        return data


class Food(Product):
    def __init__(self, id, name, price, quantity, expiry_date):
        super().__init__(id, name, price, quantity)
        self.expiry_date = expiry_date

    @property
    def expiry_date(self):
        return self._expiry_date

    @expiry_date.setter
    def expiry_date(self, value):
        try:
            parsed = date.fromisoformat(value)
        except (ValueError, TypeError):
            raise ValueError("Ngày hết hạn phải có dạng YYYY-MM-DD.")

        if parsed.isoformat() != value:
            raise ValueError("Ngày hết hạn phải có dạng YYYY-MM-DD.")

        self._expiry_date = value

    def display_info(self):
        super().display_info()
        print(f"  Hạn sử dụng: {self.expiry_date}")

    def to_dict(self):
        data = super().to_dict()
        data["type"] = "food"
        data["expiry_date"] = self.expiry_date
        return data


def product_from_dict(data):
    fields = {
        "id": data["id"],
        "name": data["name"],
        "price": data["price"],
        "quantity": data["quantity"],
    }

    product_type = data["type"]

    if product_type == "electronic":
        return Electronic(
            **fields,
            warranty_months=data["warranty_months"],
        )

    if product_type == "food":
        return Food(
            **fields,
            expiry_date=data["expiry_date"],
        )

    if product_type == "product":
        return Product(**fields)

    raise ValueError(f"Loại sản phẩm không hợp lệ: {product_type}")