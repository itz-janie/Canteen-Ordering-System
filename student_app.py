from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

from sheets_backend import get_sheet

class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        
        # Back button
        back_btn = Button(text="← Back to Order", size_hint_y=None, height=50)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'order'))
        layout.add_widget(back_btn)
        
        # Scrollable menu list
        scroll = ScrollView()
        self.menu_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=10)
        self.menu_layout.bind(minimum_height=self.menu_layout.setter('height'))
        scroll.add_widget(self.menu_layout)
        layout.add_widget(scroll)
        
        self.add_widget(layout)
        self.refresh_menus()

    def refresh_menus(self):
        self.menu_layout.clear_widgets()
        sheet = get_sheet("Menus")
        menus = sheet.get_all_records()  # header already removed

        store_menus = {}

        for menu in menus:  # ✅ NO slicing
            store = menu.get("store", "")
            if store not in store_menus:
                store_menus[store] = []
            store_menus[store].append(menu)

        for store_name, items in store_menus.items():
            store_label = Label(
                text=f"🍽️ {store_name.upper()}",
                size_hint_y=None,
                height=50,
                bold=True,
                font_size=20
            )
            self.menu_layout.add_widget(store_label)

            for item in items:
                row = BoxLayout(size_hint_y=None, height=60, spacing=10)

                item_label = Label(
                    text=f"{item['item']} - ${item['price']}",
                    size_hint_x=0.7,
                    halign="left"
                )

                available = str(item.get("available", "")).strip()
                status_label = Label(
                    text="✅ Available" if available == "YES" else "❌ Unavailable",
                    size_hint_x=0.3,
                    color=(0.3,1,0.3,1) if available == "YES" else (1,0.3,0.3,1)
                )

                row.add_widget(item_label)
                row.add_widget(status_label)
                self.menu_layout.add_widget(row)


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=50, spacing=20)

        self.email = TextInput(hint_text="Email")
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
            if (u["email"].replace("\n", "").strip() == self.email.text.strip()
                and u["password"].strip() == self.password.text.strip()
                and u["role"].strip() == "student"):
                self.manager.current = "order"
                self.manager.student_email = self.email.text
                return
        Popup(title="Error", content=Label(text="Invalid login"), size_hint=(0.6, 0.4)).open()

class OrderScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)

        self.student_name = TextInput(hint_text="Your Name")
        self.item = TextInput(hint_text="Item")
        self.time = TextInput(hint_text="Pickup Time")
        self.comment = TextInput(hint_text="Comment", multiline=True)

        menu_btn = Button(text="📋 Browse Menus", size_hint_y=None, height=50)
        menu_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))

        submit_btn = Button(text="Submit Order")
        submit_btn.bind(on_press=self.submit)

        status_btn = Button(text="Check My Orders")
        status_btn.bind(on_press=self.check_status)

        for w in [self.student_name, self.item, self.time, self.comment, 
                  menu_btn, submit_btn, status_btn]:
            layout.add_widget(w)

        self.add_widget(layout)

    def submit(self, instance):
        sheet = get_sheet("Orders")
        rows = sheet.get_all_values()
        order_id = len(rows)
        sheet.append_row([            order_id, self.student_name.text, self.manager.student_email,
            self.item.text, self.time.text, self.comment.text,
            "Preparing", "store1"  # Default store - could be selected from menu
        ])
        Popup(title="Success", content=Label(text="Order submitted!"), size_hint=(0.6, 0.4)).open()

    def check_status(self, instance):
        sheet = get_sheet("Orders")
        orders = sheet.get_all_records()
        text = ""
        for o in orders:
            if o["student_email"] == self.manager.student_email:
                text += f'{o["item"]}: {o["status"]}\n'
        Popup(title="My Orders", content=Label(text=text or "No orders"), size_hint=(0.7, 0.5)).open()

class StudentApp(App):
    def build(self):
        sm = ScreenManager()
        sm.student_email = ""
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(OrderScreen(name="order"))
        sm.add_widget(MenuScreen(name="menu"))
        return sm

if __name__ == "__main__":
    StudentApp().run()

