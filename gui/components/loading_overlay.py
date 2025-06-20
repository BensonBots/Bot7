import tkinter as tk
import time
import math

class IntegratedLoadingOverlay:
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.overlay_frame = None
        self.animation_running = True
        self.angle = 0
        self.animation_id = None

        self._create_overlay()
        self._start_animation()

    def _create_overlay(self):
        try:
            self.overlay_frame = tk.Frame(
                self.parent_app,
                bg="#10131a",
                relief="flat",
                bd=0
            )
            self.overlay_frame.place(x=0, y=0, relwidth=1, relheight=1)

            # Semi-transparent background
            bg = tk.Frame(self.overlay_frame, bg="#0a0e16")
            bg.place(relx=0, rely=0, relwidth=1, relheight=1)

            # Glassy, neon card with shadow
            card = tk.Frame(bg, bg="#1a1e27", bd=0, highlightthickness=0)
            card.place(relx=0.5, rely=0.5, anchor="center", width=370, height=270)

            # Neon glow border
            neon = tk.Canvas(card, width=360, height=260, bg="#1a1e27", highlightthickness=0)
            neon.place(x=5, y=5)
            neon.create_rectangle(8, 8, 352, 252, outline="#00eaff", width=5)
            neon.create_rectangle(14, 14, 346, 246, outline="#2937fd", width=2)

            # Logo
            logo_label = tk.Label(
                card,
                text="🪄",
                bg="#1a1e27",
                fg="#00f2ff",
                font=("Segoe UI", 54, "bold")
            )
            logo_label.place(relx=0.5, y=45, anchor="center")

            # Title with glow
            title_label = tk.Label(
                card,
                text="BENSON v2.0",
                bg="#1a1e27",
                fg="#e9faff",
                font=("Segoe UI", 21, "bold")
            )
            title_label.place(relx=0.5, y=105, anchor="center")
            # Subtle glow
            title_glow = tk.Label(
                card,
                text="BENSON v2.0",
                bg="#1a1e27",
                fg="#00eaff",
                font=("Segoe UI", 21, "bold")
            )
            title_glow.place(relx=0.5, y=108, anchor="center")

            # Subtitle
            subtitle_label = tk.Label(
                card,
                text="Advanced MEmu Instance Manager",
                bg="#1a1e27",
                fg="#66c3ff",
                font=("Segoe UI", 10)
            )
            subtitle_label.place(relx=0.5, y=135, anchor="center")

            # Status
            self.status_label = tk.Label(
                card,
                text="Initializing...",
                bg="#1a1e27",
                fg="#e9faff",
                font=("Segoe UI", 12)
            )
            self.status_label.place(relx=0.5, y=165, anchor="center")

            # Spinner canvas
            self.spinner = tk.Canvas(card, width=44, height=44, bg="#1a1e27", highlightthickness=0)
            self.spinner.place(relx=0.5, y=210, anchor="center")

            print("[LoadingOverlay] Cool overlay created")
        except Exception as e:
            print(f"[LoadingOverlay] Error creating overlay: {e}")

    def _draw_spinner(self, angle):
        self.spinner.delete("all")
        for i in range(12):
            a = math.radians(angle + i * 30)
            x0 = 22 + 14 * math.cos(a)
            y0 = 22 + 14 * math.sin(a)
            x1 = 22 + 19 * math.cos(a)
            y1 = 22 + 19 * math.sin(a)
            alpha = int(70 + 185 * (i / 12))
            color = f'#00eaff{alpha:02x}'
            self.spinner.create_line(x0, y0, x1, y1, fill="#00eaff", width=3, capstyle=tk.ROUND)

    def _start_animation(self):
        if not self.animation_running or not self.overlay_frame:
            return
        try:
            self.angle = (self.angle + 30) % 360
            self._draw_spinner(self.angle)
            self.animation_id = self.parent_app.after(70, self._start_animation)
        except tk.TclError:
            self.animation_running = False
        except Exception as e:
            print(f"[LoadingOverlay] Animation error: {e}")
            self.animation_running = False

    def update_status(self, status_text):
        try:
            if self.status_label and self.status_label.winfo_exists():
                self.status_label.configure(text=status_text)
                self.parent_app.update_idletasks()
                print(f"[LoadingOverlay] Status: {status_text}")
        except tk.TclError:
            pass
        except Exception as e:
            print(f"[LoadingOverlay] Status update error: {e}")

    def close(self):
        try:
            print("[LoadingOverlay] Closing overlay...")
            self.animation_running = False
            if self.animation_id:
                try:
                    self.parent_app.after_cancel(self.animation_id)
                except:
                    pass
            if self.overlay_frame and self.overlay_frame.winfo_exists():
                self.overlay_frame.destroy()
            self.overlay_frame = None
            self.status_label = None
            self.spinner = None
            print("[LoadingOverlay] Overlay closed")
        except Exception as e:
            print(f"[LoadingOverlay] Error closing overlay: {e}")

    def is_visible(self):
        return (self.overlay_frame is not None and
                self.overlay_frame.winfo_exists() and
                self.overlay_frame.winfo_viewable())
