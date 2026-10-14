from datetime import datetime
from uuid import uuid4

from models import Product, Electronic, Food, product_from_dict
from storage import (
    PRODUCTS_FILE,
    ORDERS_FILE,
    read_json,
    write_json,
)


def input_text(message):
    value = input(message).strip()

    if not value:
        raise ValueError("Thông tin không được để trống.")

    return value


def input_integer(message, minimum=0):
    try:
        value = int(input(message))
    except ValueError:
        raise ValueError("Bạn phải nhập số nguyên.")

    if value < minimum:
        raise ValueError(f"Giá trị phải từ {minimum} trở lên.")

    return value


def input_price(message):
    # Bài này dùng giá nguyên theo đơn vị đồng.
    return input_integer(message, minimum=0)


class Store:
    def __init__(self):
        self.products = [
            product_from_dict(item)
            for item in read_json(PRODUCTS_FILE)
        ]
        self.orders = read_json(ORDERS_FILE)

        ids = [product.id.casefold() for product in self.products]

        if len(ids) != len(set(ids)):
            raise ValueError("File sản phẩm chứa mã bị trùng.")

        # Kiểm tra các trường dùng cho báo cáo doanh thu.
        for order in self.orders:
            if not isinstance(order, dict):
                raise ValueError("Dữ liệu đơn hàng không hợp lệ.")

            revenue = order.get("actual_revenue")

            if (
                isinstance(revenue, bool)
                or not isinstance(revenue, (int, float))
                or revenue < 0
            ):
                raise ValueError("Doanh thu trong đơn hàng không hợp lệ.")

    def save_products(self):
        write_json(
            PRODUCTS_FILE,
            [product.to_dict() for product in self.products],
        )

    def find_by_id(self, product_id):
        product_id = product_id.strip().casefold()

        for product in self.products:
            if product.id.casefold() == product_id:
                return product

        return None

    def require_product(self):
        product_id = input_text("Nhập mã sản phẩm: ")
        product = self.find_by_id(product_id)

        if product is None:
            raise ValueError("Mã sản phẩm không tồn tại.")

        return product

    def display_products(self):
        if not self.products:
            print("Chưa có sản phẩm.")
            return

        print("\n--- DANH SÁCH SẢN PHẨM ---")

        # Đa hình: mỗi đối tượng tự gọi phiên bản display_info của nó.
        for product in self.products:
            product.display_info()

    def add_product(self):
        print("\n1. Thông thường")
        print("2. Điện tử")
        print("3. Thực phẩm")

        choice = input_text("Chọn loại sản phẩm: ")

        if choice not in {"1", "2", "3"}:
            raise ValueError("Loại sản phẩm không hợp lệ.")

        product_id = input_text("Mã sản phẩm: ")

        if self.find_by_id(product_id):
            raise ValueError("Mã sản phẩm đã tồn tại.")

        name = input_text("Tên sản phẩm: ")
        price = input_price("Giá bán (đồng): ")
        quantity = input_integer("Số lượng tồn kho: ")

        if choice == "2":
            warranty = input_integer("Bảo hành (tháng): ")
            product = Electronic(
                product_id, name, price, quantity, warranty
            )
        elif choice == "3":
            expiry = input_text("Hạn sử dụng (YYYY-MM-DD): ")
            product = Food(
                product_id, name, price, quantity, expiry
            )
        else:
            product = Product(product_id, name, price, quantity)

        self.products.append(product)

        try:
            self.save_products()
        except (OSError, ValueError):
            self.products.pop()
            raise

        print("Đã thêm sản phẩm.")

    def search_products(self):
        keyword = input_text("Nhập mã hoặc tên cần tìm: ").casefold()

        results = [
            product
            for product in self.products
            if keyword in product.id.casefold()
            or keyword in product.name.casefold()
        ]

        if not results:
            print("Không tìm thấy sản phẩm.")
            return

        for product in results:
            product.display_info()

    def update_product(self):
        product = self.require_product()
        product.display_info()

        print("\nĐể trống nếu muốn giữ nguyên thông tin.")

        # Tạo bản sao để dữ liệu sai không làm thay đổi đối tượng gốc.
        updated = product_from_dict(product.to_dict())

        name = input("Tên mới: ").strip()
        price = input("Giá mới (đồng): ").strip()
        quantity = input("Tồn kho mới: ").strip()

        if name:
            updated.name = name

        if price:
            updated.price = int(price)

        if quantity:
            updated.quantity = int(quantity)

        if isinstance(updated, Electronic):
            warranty = input("Bảo hành mới (tháng): ").strip()

            if warranty:
                updated.warranty_months = int(warranty)

        elif isinstance(updated, Food):
            expiry = input("Hạn sử dụng mới (YYYY-MM-DD): ").strip()

            if expiry:
                updated.expiry_date = expiry

        index = self.products.index(product)
        self.products[index] = updated

        try:
            self.save_products()
        except (OSError, ValueError):
            self.products[index] = product
            raise

        print("Đã cập nhật sản phẩm.")

    def delete_product(self):
        product = self.require_product()
        product.display_info()

        if input("Xác nhận xóa? (y/n): ").strip().lower() != "y":
            print("Đã hủy xóa.")
            return

        index = self.products.index(product)
        self.products.pop(index)

        try:
            self.save_products()
        except (OSError, ValueError):
            self.products.insert(index, product)
            raise

        print("Đã xóa sản phẩm.")

    @staticmethod
    def calculate_discount(total):
        if total >= 1_000_000:
            return 0.10

        if total >= 500_000:
            return 0.05

        return 0

    def sell(self):
        self.display_products()

        if not self.products:
            return

        cart = {}

        print("\nNhập mã sản phẩm; để trống để kết thúc chọn hàng.")

        while True:
            product_id = input("Mã sản phẩm: ").strip()

            if not product_id:
                break

            product = self.find_by_id(product_id)

            if product is None:
                print("Mã sản phẩm không tồn tại.")
                continue

            try:
                quantity = input_integer("Số lượng mua: ", minimum=1)
            except ValueError as error:
                print(f"Lỗi: {error}")
                continue

            already_selected = cart.get(product.id, 0)

            if already_selected + quantity > product.quantity:
                print(
                    f"Không đủ hàng. Tồn kho: {product.quantity}; "
                    f"đã chọn: {already_selected}."
                )
                continue

            cart[product.id] = already_selected + quantity

        if not cart:
            print("Giỏ hàng trống.")
            return

        items = []
        total = 0

        print("\n--- ĐƠN HÀNG ---")

        for product_id, quantity in cart.items():
            product = self.find_by_id(product_id)
            subtotal = product.price * quantity
            total += subtotal

            items.append({
                "product_id": product.id,
                "name": product.name,
                "unit_price": product.price,
                "quantity": quantity,
                "subtotal": subtotal,
            })

            print(
                f"{product.name}: {quantity} × "
                f"{product.price:,.0f} = {subtotal:,.0f} đồng"
            )

        discount_rate = self.calculate_discount(total)
        discount_amount = round(total * discount_rate)
        actual_revenue = total - discount_amount

        print(f"\nTổng trước khuyến mại: {total:,.0f} đồng")
        print(f"Tỷ lệ khuyến mại: {discount_rate:.0%}")
        print(f"Tiền giảm: {discount_amount:,.0f} đồng")
        print(f"Phải thanh toán: {actual_revenue:,.0f} đồng")

        confirmation = input(
            "Xác nhận đã thanh toán? (y/n): "
        ).strip().lower()

        if confirmation != "y":
            print("Đã hủy đơn. Tồn kho chưa thay đổi.")
            return

        order = {
            "order_id": uuid4().hex,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "items": items,
            "total_before_discount": total,
            "discount_rate": discount_rate,
            "discount_amount": discount_amount,
            "actual_revenue": actual_revenue,
        }

        old_quantities = {
            product_id: self.find_by_id(product_id).quantity
            for product_id in cart
        }

        for product_id, quantity in cart.items():
            self.find_by_id(product_id).quantity -= quantity

        self.orders.append(order)

        try:
            self.save_products()

            try:
                write_json(ORDERS_FILE, self.orders)
            except (OSError, ValueError):
                # Nếu ghi đơn hàng thất bại, khôi phục tồn kho.
                for product_id, quantity in old_quantities.items():
                    self.find_by_id(product_id).quantity = quantity

                try:
                    self.save_products()
                except (OSError, ValueError) as rollback_error:
                    raise RuntimeError(
                        "Không ghi được đơn hàng và không khôi phục "
                        "được file tồn kho. Hãy kiểm tra hai file JSON."
                    ) from rollback_error

                raise

        except (OSError, ValueError, RuntimeError):
            self.orders.pop()

            for product_id, quantity in old_quantities.items():
                self.find_by_id(product_id).quantity = quantity

            raise

        print(f"Đã lưu đơn hàng: {order['order_id']}")

    def inventory_report(self):
        print("\n--- BÁO CÁO TỒN KHO ---")

        if not self.products:
            print("Kho chưa có sản phẩm.")
            return

        low_stock = [
            product for product in self.products
            if product.quantity < 5
        ]

        print("\nSản phẩm có tồn kho dưới 5:")

        if low_stock:
            for product in low_stock:
                product.display_info()
        else:
            print("Không có.")

        total_quantity = sum(
            product.quantity for product in self.products
        )

        total_value = sum(
            product.calculate_value() for product in self.products
        )

        highest_value_product = max(
            self.products,
            key=lambda product: product.calculate_value(),
        )

        print(f"\nTổng số lượng trong kho: {total_quantity}")
        print(f"Tổng giá trị tồn kho: {total_value:,.0f} đồng")

        print("\nSản phẩm có giá trị tồn kho cao nhất:")
        highest_value_product.display_info()

        print(
            f"Giá trị tồn kho: "
            f"{highest_value_product.calculate_value():,.0f} đồng"
        )

    def revenue_report(self):
        print("\n--- BÁO CÁO DOANH THU ---")

        total_orders = len(self.orders)

        total_revenue = sum(
            order["actual_revenue"] for order in self.orders
        )

        average = (
            total_revenue / total_orders
            if total_orders > 0
            else 0
        )

        print(f"Tổng doanh thu thực thu: {total_revenue:,.0f} đồng")
        print(f"Số đơn đã thanh toán: {total_orders}")
        print(f"Giá trị trung bình mỗi đơn: {average:,.0f} đồng")


def main():
    try:
        store = Store()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Không thể đọc dữ liệu: {error}")
        print("Hãy kiểm tra products.json và orders.json.")
        return

    actions = {
        "1": store.display_products,
        "2": store.add_product,
        "3": store.search_products,
        "4": store.update_product,
        "5": store.delete_product,
        "6": store.sell,
        "7": store.inventory_report,
        "8": store.revenue_report,
    }

    while True:
        print(
            "\n========== QUẢN LÝ CỬA HÀNG ==========\n"
            "1. Hiển thị danh sách sản phẩm\n"
            "2. Thêm sản phẩm mới\n"
            "3. Tìm kiếm theo mã hoặc tên\n"
            "4. Cập nhật sản phẩm\n"
            "5. Xóa sản phẩm\n"
            "6. Bán hàng\n"
            "7. Báo cáo tồn kho\n"
            "8. Báo cáo doanh thu\n"
            "9. Thoát"
        )

        choice = input("Lựa chọn: ").strip()

        if choice == "9":
            print("Đã thoát chương trình.")
            break

        action = actions.get(choice)

        if action is None:
            print("Hãy chọn một số từ 1 đến 9.")
            continue

        try:
            action()
        except ValueError as error:
            print(f"Dữ liệu không hợp lệ: {error}")
        except OSError as error:
            print(f"Lỗi đọc/ghi file: {error}")
        except RuntimeError as error:
            print(f"Lỗi lưu đơn hàng: {error}")
            break


if __name__ == "__main__":
    main()