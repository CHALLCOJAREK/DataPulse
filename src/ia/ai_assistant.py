import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import tkinter as tk
from tkinter import scrolledtext, ttk
from src.ia.natural_query import generate_sql, run_sql, natural_answer
from src.core.logger import log


class DataPulseAIChat(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("💬 DataPulse – Asistente Financiero IA")
        self.geometry("760x620")
        self.configure(bg="#ffffff")

        self._build_ui()

    def _build_ui(self):
        # === FRAME PRINCIPAL ===
        self.main_frame = ttk.Frame(self, padding=20)
        self.main_frame.pack(fill="both", expand=True)

        # === TÍTULO ===
        title = ttk.Label(
            self.main_frame,
            text="Asistente Financiero DataPulse",
            font=("Segoe UI", 18, "bold"),
            foreground="#0A2342"
        )
        title.pack(anchor="center", pady=(0, 15))

        # === CHAT BOX ===
        self.chat_box = scrolledtext.ScrolledText(
            self.main_frame,
            wrap=tk.WORD,
            state="disabled",
            font=("Segoe UI", 11),
            bg="#f9f9f9",
            fg="#222",
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=10
        )
        self.chat_box.pack(fill="both", expand=True, padx=10, pady=(0, 15))
        self.chat_box.tag_configure("user", foreground="#ffffff", background="#0A2342", spacing3=5, justify="right", lmargin1=40, rmargin=10, spacing1=5, spacing2=5)
        self.chat_box.tag_configure("ai", foreground="#000000", background="#EDEDED", spacing3=5, justify="left", lmargin1=10, rmargin=40, spacing1=5, spacing2=5)

        # === FRAME INPUT ===
        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(fill="x", pady=(10, 0))

        self.entry = ttk.Entry(
            input_frame,
            font=("Segoe UI", 11),
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", self._on_enter)

        self.send_btn = ttk.Button(
            input_frame,
            text="Enviar",
            command=self._on_enter
        )
        self.send_btn.pack(side="right")

        # === ESTILO MODERNO ===
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#ffffff")
        style.configure("TButton", font=("Segoe UI", 10, "bold"), background="#0A2342", foreground="white", padding=8)
        style.map("TButton", background=[("active", "#173D7A")])
        style.configure("TEntry", padding=8, relief="flat")

        # Mensaje inicial
        self._insert_ai("Hola 👋 Soy el asistente financiero de DataPulse.\nHazme cualquier pregunta sobre tus cuentas o movimientos.")

    # === CHAT LOGIC ===
    def _insert_user(self, message: str):
        self.chat_box.configure(state="normal")
        self.chat_box.insert(tk.END, f"Tú: {message}\n", "user")
        self.chat_box.configure(state="disabled")
        self.chat_box.see(tk.END)

    def _insert_ai(self, message: str):
        self.chat_box.configure(state="normal")
        self.chat_box.insert(tk.END, f"IA: {message}\n", "ai")
        self.chat_box.configure(state="disabled")
        self.chat_box.see(tk.END)

    def _on_enter(self, event=None):
        user_input = self.entry.get().strip()
        if not user_input:
            return

        self._insert_user(user_input)
        self.entry.delete(0, tk.END)
        self.after(100, lambda: self._process_query(user_input))

    def _process_query(self, question: str):
        try:
            sql = generate_sql(question)
            if not sql:
                self._insert_ai("No pude entender tu consulta. Intenta con otra frase.")
                return

            result = run_sql(sql)
            if result is None:
                self._insert_ai("No se encontraron resultados para esa consulta.")
                return

            answer = natural_answer(question, sql, result)
            self._insert_ai(answer)
            log(f"🧾 Consulta respondida correctamente: {question}")
        except Exception as e:
            log(f"💥 Error procesando consulta: {e}")
            self._insert_ai("Ocurrió un error procesando tu consulta.")


if __name__ == "__main__":
    app = DataPulseAIChat()
    app.mainloop()
