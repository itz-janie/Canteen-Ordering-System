from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

from sheets_backend import get_sheet

class VendorMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        
        # Navigation buttons
        nav_layout = BoxLayout(size_hint_y=None, height=60, spacing=10)
        orders_btn = Button(text="📋 Orders")
        orders_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'orders'))
        menu_btn = Button(text="🍽️ Manage Menus")
        nav_layout.add_widget(orders_btn)
        nav_layout.add_widget(menu_btn)
        layout.add_widget(nav_layout)
        
        # Scrollable menus
        scroll = ScrollView()
        self.menu_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=10)
        self.menu_layout.bind(minimum_height=self.menu_layout.setter('height'))
        scroll.add_widget(self.menu_layout)
        layout.add_widget(scroll)
        
        # Add new menu button
        add_btn = Button(text="➕ Add New Menu Item", size_hint_y=None, height=50)
        add_btn.bind(on_press=self.show_add_menu)
        layout.add_widget(add_btn)
        
        self.add_widget(layout)
        # DON'T call on_enter() or refresh_menus() here!

    def on_enter(self, *args):
        """Called when screen becomes active - NOW self.manager exists"""
        self.refresh_menus()

    def refresh_menus(self):
        self.menu_layout.clear_widgets()
        sheet = get_sheet("Menus")
        menus = sheet.get_all_records()  # header already removed

        for index, menu in enumerate(menus):
            if str(menu.get("store", "")).strip() != self.manager.store:
                continue

            # Correct Google Sheets row number
            sheet_row = index + 2  # row 1 = header

            row = BoxLayout(size_hint_y=None, height=80, spacing=10)

            info_layout = BoxLayout(orientation="vertical", size_hint_x=0.6)
            info_layout.add_widget(
                Label(text=f'{menu["item"]} - ${menu["price"]}', bold=True)
            )

            available = str(menu.get("available", "")).strip()
            status_label = Label(
                text="✅ Available" if available == "YES" else "❌ Unavailable"
            )
            info_layout.add_widget(status_label)
            row.add_widget(info_layout)

            btn_layout = BoxLayout(size_hint_x=0.4, spacing=5)

            toggle_btn = Button(
                text="Toggle Available" if available == "YES" else "Make Available"
            )
            toggle_btn.bind(on_press=lambda x, r=sheet_row: self.toggle_available(r))

            delete_btn = Button(text="🗑️ Delete", size_hint_x=0.3)
            delete_btn.bind(on_press=lambda x, r=sheet_row: self.delete_menu(r))

            btn_layout.add_widget(toggle_btn)
            btn_layout.add_widget(delete_btn)
            row.add_widget(btn_layout)

            self.menu_layout.add_widget(row)


    def show_add_menu(self, instance):
        content = BoxLayout(orientation="vertical", spacing=10, padding=20)
        self.new_item = TextInput(hint_text="Item name")
        self.new_price = TextInput(hint_text="Price (e.g. 4.50)")
        self.new_available = TextInput(hint_text="YES/NO", text="YES")
        
        content.add_widget(self.new_item)
        content.add_widget(self.new_price)
        content.add_widget(self.new_available)
        
        popup = Popup(title="Add New Menu Item", content=content, size_hint=(0.8, 0.6))
        add_btn = Button(text="Add", size_hint_y=None, height=50)
        add_btn.bind(on_press=lambda x: self.add_menu(popup))
        content.add_widget(add_btn)
        popup.open()

    def add_menu(self, popup):
        sheet = get_sheet("Menus")
        sheet.append_row([self.manager.store, self.new_item.text, 
                         self.new_price.text, self.new_available.text])
        popup.dismiss()
        self.refresh_menus()

    def toggle_available(self, row):
        sheet = get_sheet("Menus")
        current = sheet.cell(row, 4).value  # Available column
        new_status = "NO" if current == "YES" else "YES"
        sheet.update_cell(row, 4, new_status)
        self.refresh_menus()

    def delete_menu(self, row):
        sheet = get_sheet("Menus")
        sheet.delete_rows(row, 1)
        self.refresh_menus()

class VendorLogin(Screen):
    # ... (same as your existing code)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=50, spacing=20)

        self.email = TextInput(hint_text="Vendor Email")
        self.password = TextInput(hint_text="Password", password=True)

        btn = Button(text="Login")
        btn.bind(on_press=self.login)

        layout.add_widget(self.email)
        layout.add_widget(self.password)
        layout.add_widget(btn)
        self.add_widget(layout)

    def login(self, instance):
        users = get_sheet("Users").get_all_records()
        for u in users:
            if (u["email"] == self.email.text
                and u["password"] == self.password.text
                and u["role"] == "vendor"):
                self.manager.store = u["store"]
                self.manager.current = "menus"  # Go to menus first
                return
        Popup(title="Error", content=Label(text="Invalid login"), size_hint=(0.6, 0.4)).open()

class OrdersScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        main_layout = BoxLayout(orientation="vertical", padding=20, spacing=10)

        # Back button
        back_btn = Button(text="← Back to Menus", size_hint_y=None, height=50)
        back_btn.bind(on_press=lambda x: setattr(self.manager, "current", "menus"))
        main_layout.add_widget(back_btn)

        # Scrollable orders list
        scroll = ScrollView()
        self.orders_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=10
        )
        self.orders_layout.bind(minimum_height=self.orders_layout.setter("height"))
        scroll.add_widget(self.orders_layout)

        main_layout.add_widget(scroll)
        self.add_widget(main_layout)

    def on_enter(self, *args):
        self.refresh()

    def refresh(self):
        self.orders_layout.clear_widgets()

        sheet = get_sheet("Orders")
        orders = sheet.get_all_records()  # header already removed

        found = False

        for index, order in enumerate(orders):
            if str(order.get("store", "")).strip() != self.manager.store:
                continue

            found = True
            sheet_row = index + 2  # Google Sheets row

            row = BoxLayout(size_hint_y=None, height=90, spacing=10)

            info = Label(
                text=(
                    f"[b]{order['item']}[/b]\n"
                    f"{order['student_name']} | {order['pickup_time']}\n"
                    f"Status: {order['status']}"
                ),
                markup=True,
                halign="left",
                valign="middle"
            )
            info.bind(size=info.setter("text_size"))
            row.add_widget(info)

            btn = Button(text="✔ Complete", size_hint_x=0.3)
            btn.bind(on_press=lambda x, r=sheet_row: self.mark_complete(r))
            row.add_widget(btn)

            self.orders_layout.add_widget(row)

        if not found:
            self.orders_layout.add_widget(
                Label(text="No orders yet", size_hint_y=None, height=50)
            )

    def mark_complete(self, row):
        sheet = get_sheet("Orders")
        sheet.update_cell(row, 7, "Completed")  # status column
        self.refresh()



class VendorApp(App):
    def build(self):
        sm = ScreenManager()
        sm.store = ""
        sm.add_widget(VendorLogin(name="login"))
        sm.add_widget(OrdersScreen(name="orders"))
        sm.add_widget(VendorMenuScreen(name="menus"))
        return sm


if __name__ == "__main__":
    VendorApp().run()



