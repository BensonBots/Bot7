import tkinter as tk
import math
import random

class ModernLoadingOverlay:
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.overlay_frame = None
        self.animation_running = True
        self.animation_step = 0
        self.animation_id = None
        self.status_label = None
        self.logo_label = None
        self.progress_canvas = None
        self.particle_canvas = None
        self.glow_canvas = None
        self.particles = []

        print("[ModernLoadingOverlay] Creating advanced loading interface...")
        self._create_overlay()
        self._init_particles()
        self.parent_app.after(1, self._start_animations)

    def _create_overlay(self):
        """Create modern glassmorphism loading overlay"""
        try:
            # Full screen overlay with animated background
            self.overlay_frame = tk.Frame(self.parent_app, bg="#0a0e16")
            self.overlay_frame.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Animated particle background
            self.particle_canvas = tk.Canvas(
                self.overlay_frame, 
                highlightthickness=0, 
                bg="#0a0e16"
            )
            self.particle_canvas.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Modern glass card with blur effect simulation
            glass_frame = tk.Frame(
                self.overlay_frame, 
                bg="#1a1f2e", 
                relief="flat", 
                bd=0
            )
            glass_frame.place(relx=0.5, rely=0.5, anchor="center", width=550, height=450)
            
            # Glow border canvas
            self.glow_canvas = tk.Canvas(
                glass_frame, 
                width=550, 
                height=450, 
                bg="#1a1f2e", 
                highlightthickness=0, 
                bd=0
            )
            self.glow_canvas.place(x=0, y=0)
            
            # Content container with padding
            content_frame = tk.Frame(glass_frame, bg="#1a1f2e")
            content_frame.place(relx=0.5, rely=0.5, anchor="center", width=500, height=400)
            
            # Logo section with dramatic styling
            logo_section = tk.Frame(content_frame, bg="#1a1f2e")
            logo_section.pack(pady=(40, 20))
            
            # Animated logo with multiple emojis
            self.logo_label = tk.Label(
                logo_section,
                text="⚡",
                bg="#1a1f2e",
                fg="#00d4ff",
                font=("Segoe UI", 96, "bold")
            )
            self.logo_label.pack()
            
            # Title section with text shadow effect
            title_section = tk.Frame(content_frame, bg="#1a1f2e", height=80)
            title_section.pack(pady=(0, 10))
            title_section.pack_propagate(False)
            
            # Shadow title (positioned behind main title)
            shadow_title = tk.Label(
                title_section,
                text="BENSON v2.0",
                bg="#1a1f2e",
                fg="#0f1419",
                font=("Segoe UI", 42, "bold")
            )
            shadow_title.place(relx=0.5, rely=0.5, anchor="center", x=3, y=3)
            
            # Main title
            main_title = tk.Label(
                title_section,
                text="BENSON v2.0",
                bg="#1a1f2e",
                fg="#ffffff",
                font=("Segoe UI", 42, "bold")
            )
            main_title.place(relx=0.5, rely=0.5, anchor="center")
            
            # Subtitle with special characters
            subtitle = tk.Label(
                content_frame,
                text="◆ Benson v2.0 ◆",
                bg="#1a1f2e",
                fg="#00d4ff", 
                font=("Segoe UI", 18, "bold")
            )
            subtitle.pack(pady=(0, 35))
            
            # Progress section
            progress_section = tk.Frame(content_frame, bg="#1a1f2e")
            progress_section.pack(pady=(0, 25))
            
            # Progress bar with modern styling
            progress_bg = tk.Frame(progress_section, bg="#2a2f3e", height=12, width=350)
            progress_bg.pack()
            
            self.progress_canvas = tk.Canvas(
                progress_bg, 
                width=350, 
                height=12, 
                bg="#2a2f3e", 
                highlightthickness=0,
                bd=0
            )
            self.progress_canvas.pack()
            
            # Status section
            status_section = tk.Frame(content_frame, bg="#1a1f2e")
            status_section.pack(pady=(0, 20))
            
            self.status_label = tk.Label(
                status_section,
                text="🚀 Initializing...",
                bg="#1a1f2e",
                fg="#ffffff",
                font=("Segoe UI", 18, "bold")
            )
            self.status_label.pack()
            
            # Animated dots indicator
            self.dots_label = tk.Label(
                status_section,
                text="◉◉◉",
                bg="#1a1f2e",
                fg="#00d4ff",
                font=("Segoe UI", 16, "bold")
            )
            self.dots_label.pack(pady=(10, 0))
            
            # Footer section
            footer_section = tk.Frame(content_frame, bg="#1a1f2e")
            footer_section.pack(side="bottom", pady=(0, 20))
            
            footer_line1 = tk.Label(
                footer_section,
                text="MEmu Instance Manager",
                bg="#1a1f2e",
                fg="#6b7280",
                font=("Segoe UI", 12, "bold")
            )
            footer_line1.pack()
            
            footer_line2 = tk.Label(
                footer_section,
                text="Benson Control Suite",
                bg="#1a1f2e",
                fg="#4b5563",
                font=("Segoe UI", 10)
            )
            footer_line2.pack()
            
            # Force to top
            self.overlay_frame.lift()
            self.overlay_frame.tkraise()
            self.parent_app.update()
            
            print("[ModernLoadingOverlay] ✅ Advanced overlay created successfully")
            
        except Exception as e:
            print(f"[ModernLoadingOverlay] ❌ Error creating overlay: {e}")

    def _init_particles(self):
        """Initialize floating particles for background animation"""
        try:
            self.particles = []
            for _ in range(25):
                particle = {
                    'x': random.randint(0, 1200),
                    'y': random.randint(0, 800),
                    'speed_x': random.uniform(-0.5, 0.5),
                    'speed_y': random.uniform(-0.8, -0.2),
                    'size': random.randint(2, 5),
                    'opacity': random.uniform(0.3, 0.8),
                    'color': random.choice(['#00d4ff', '#00ff88', '#ffdd00', '#ff6b6b', '#8b5cf6'])
                }
                self.particles.append(particle)
        except Exception as e:
            print(f"[ModernLoadingOverlay] ❌ Error initializing particles: {e}")

    def _start_animations(self):
        """Start all animations"""
        if not self.animation_running or not self.overlay_frame:
            return
        
        try:
            # Animate particles
            self._animate_particles()
            
            # Animate logo
            self._animate_logo()
            
            # Animate progress bar
            self._animate_progress()
            
            # Animate dots
            self._animate_dots()
            
            # Animate glow border
            self._animate_glow_border()
            
            self.animation_step += 1
            
            # Force UI updates
            try:
                if self.logo_label:
                    self.logo_label.update_idletasks()
                if self.progress_canvas:
                    self.progress_canvas.update_idletasks()
                if self.particle_canvas:
                    self.particle_canvas.update_idletasks()
                self.parent_app.update_idletasks()
            except:
                pass
            
            # Schedule next frame
            if self.animation_running:
                self.animation_id = self.parent_app.after(80, self._start_animations)
            
            # Debug info
            if self.animation_step % 15 == 0:
                print(f"[ModernLoadingOverlay] 🎬 Animation frame {self.animation_step}")
                
        except Exception as e:
            print(f"[ModernLoadingOverlay] ❌ Animation error: {e}")
            self.animation_running = False

    def _animate_particles(self):
        """Animate floating background particles"""
        try:
            if not (self.particle_canvas and self.particle_canvas.winfo_exists()):
                return
                
            self.particle_canvas.delete("all")
            
            for particle in self.particles:
                # Update position
                particle['x'] += particle['speed_x']
                particle['y'] += particle['speed_y']
                
                # Wrap around screen
                if particle['y'] < 0:
                    particle['y'] = 800
                    particle['x'] = random.randint(0, 1200)
                if particle['x'] < 0:
                    particle['x'] = 1200
                elif particle['x'] > 1200:
                    particle['x'] = 0
                
                # Draw particle with glow effect
                size = particle['size']
                x, y = particle['x'], particle['y']
                
                # Outer glow
                self.particle_canvas.create_oval(
                    x - size - 2, y - size - 2,
                    x + size + 2, y + size + 2,
                    fill=particle['color'], outline="", stipple="gray25"
                )
                
                # Main particle
                self.particle_canvas.create_oval(
                    x - size, y - size,
                    x + size, y + size,
                    fill=particle['color'], outline=""
                )
                
        except Exception as e:
            print(f"[ModernLoadingOverlay] ❌ Particle animation error: {e}")

    def _animate_logo(self):
        """Animate the main logo"""
        try:
            if not (self.logo_label and self.logo_label.winfo_exists()):
                return
            
            # Cycle through different emojis and colors
            logo_sets = [
                {"emoji": "⚡", "color": "#00d4ff"},
                {"emoji": "🚀", "color": "#00ff88"},
                {"emoji": "⭐", "color": "#ffdd00"},
                {"emoji": "💫", "color": "#ff6b6b"},
                {"emoji": "🔥", "color": "#8b5cf6"},
                {"emoji": "💎", "color": "#06d6a0"},
                {"emoji": "🌟", "color": "#ffd166"},
                {"emoji": "✨", "color": "#f72585"}
            ]
            
            logo_index = (self.animation_step // 12) % len(logo_sets)
            current_logo = logo_sets[logo_index]
            
            self.logo_label.configure(
                text=current_logo["emoji"],
                fg=current_logo["color"]
            )
            
        except Exception as e:
            print(f"[ModernLoadingOverlay] ❌ Logo animation error: {e}")

    def _animate_progress(self):
        """Animate the progress bar"""
        try:
            if not (self.progress_canvas and self.progress_canvas.winfo_exists()):
                return
                
            self.progress_canvas.delete("all")
            
            # Background
            self.progress_canvas.create_rectangle(
                0, 0, 350, 12, 
                fill="#2a2f3e", outline=""
            )
            
            # Animated progress with wave effect
            progress_width = (self.animation_step % 80) * 4.375  # 0 to 350
            wave_offset = math.sin(self.animation_step * 0.2) * 10
            
            # Gradient effect simulation
            gradient_colors = ["#00d4ff", "#00ff88", "#ffdd00", "#ff6b6b"]
            color_index = (self.animation_step // 15) % len(gradient_colors)
            main_color = gradient_colors[color_index]
            
            if progress_width > 0:
                # Main progress bar
                self.progress_canvas.create_rectangle(
                    0, 0, progress_width, 12,
                    fill=main_color, outline=""
                )
                
                # Animated wave effect
                if progress_width > 30:
                    wave_x = max(0, progress_width - 30 + wave_offset)
                    wave_width = min(30, progress_width)
                    
                    self.progress_canvas.create_rectangle(
                        wave_x, 2, wave_x + wave_width, 10,
                        fill="#ffffff", outline=""
                    )
                
                # Leading edge glow
                if progress_width < 350:
                    self.progress_canvas.create_rectangle(
                        max(0, progress_width - 5), 1,
                        min(350, progress_width + 5), 11,
                        fill="#ffffff", outline=""
                    )
                    
        except Exception as e:
            print(f"[ModernLoadingOverlay] ❌ Progress animation error: {e}")

    def _animate_dots(self):
        """Animate the dots indicator"""
        try:
            if not (self.dots_label and self.dots_label.winfo_exists()):
                return
            
            # Different dot patterns and styles
            dot_patterns = [
                "◉○○", "○◉○", "○○◉", "◉◉○", "○◉◉", "◉○◉", "◉◉◉",
                "●○○", "○●○", "○○●", "●●○", "○●●", "●○●", "●●●"
            ]
            
            pattern_index = self.animation_step % len(dot_patterns)
            pattern = dot_patterns[pattern_index]
            
            # Color cycling
            dot_colors = ["#00d4ff", "#00ff88", "#ffdd00", "#ff6b6b", "#8b5cf6"]
            color = dot_colors[(self.animation_step // 8) % len(dot_colors)]
            
            self.dots_label.configure(text=pattern, fg=color)
            
        except Exception as e:
            print(f"[ModernLoadingOverlay] ❌ Dots animation error: {e}")

    def _animate_glow_border(self):
        """Animate the glow border around the card"""
        try:
            if not (self.glow_canvas and self.glow_canvas.winfo_exists()):
                return
                
            self.glow_canvas.delete("all")
            
            # Animated rainbow border
            border_colors = ["#00d4ff", "#00ff88", "#ffdd00", "#ff6b6b", "#8b5cf6", "#06d6a0"]
            color_index = (self.animation_step // 10) % len(border_colors)
            glow_color = border_colors[color_index]
            
            # Multiple border layers for glow effect
            for i in range(4):
                opacity = 1.0 - (i * 0.25)
                self.glow_canvas.create_rectangle(
                    i, i, 550 - i, 450 - i,
                    outline=glow_color, width=2
                )
            
            # Corner accents
            corner_size = 20
            for corner in [(0, 0), (530, 0), (0, 430), (530, 430)]:
                x, y = corner
                self.glow_canvas.create_rectangle(
                    x, y, x + corner_size, y + corner_size,
                    fill=glow_color, outline=""
                )
                
        except Exception as e:
            print(f"[ModernLoadingOverlay] ❌ Glow border animation error: {e}")

    def update_status(self, status_text):
        """Update status with modern icons and styling"""
        try:
            if self.status_label and self.status_label.winfo_exists():
                # Enhanced status icons
                status_icons = {
                    "connecting": "🔗",
                    "loading": "📦",
                    "initializing": "⚙️",
                    "setting up": "🛠️",
                    "building": "🏗️",
                    "finalizing": "✨",
                    "optimizing": "⚡",
                    "preparing": "🎯",
                    "processing": "🔄",
                    "creating": "🎯",
                    "cards": "📦",
                    "console": "📝",
                    "interface": "✨",
                    "finishing": "🎉",
                    "ready": "🎉"
                }
                
                # Find appropriate icon
                icon = "🚀"  # Default
                for key, emoji in status_icons.items():
                    if key in status_text.lower():
                        icon = emoji
                        break
                
                formatted_status = f"{icon} {status_text}"
                
                self.status_label.configure(text=formatted_status)
                
                # Force immediate updates
                self.status_label.update_idletasks()
                self.status_label.update()
                self.parent_app.update_idletasks()
                self.parent_app.update()
                
                print(f"[ModernLoadingOverlay] 📝 Status updated: {formatted_status}")
                
        except Exception as e:
            print(f"[ModernLoadingOverlay] ❌ Status update error: {e}")

    def close(self):
        """Close overlay with cleanup"""
        try:
            print("[ModernLoadingOverlay] 🔄 Closing advanced overlay...")
            
            # Stop animations
            self.animation_running = False
            
            # Cancel animation timer
            if self.animation_id:
                try:
                    self.parent_app.after_cancel(self.animation_id)
                except:
                    pass
            
            # Destroy overlay
            if self.overlay_frame and self.overlay_frame.winfo_exists():
                self.overlay_frame.destroy()
            
            # Clear all references
            self.overlay_frame = None
            self.status_label = None
            self.logo_label = None
            self.progress_canvas = None
            self.particle_canvas = None
            self.glow_canvas = None
            self.particles = []
            
            print("[ModernLoadingOverlay] ✅ Advanced overlay closed successfully")
            
        except Exception as e:
            print(f"[ModernLoadingOverlay] ❌ Close error: {e}")


# Legacy compatibility class
class IntegratedLoadingOverlay(ModernLoadingOverlay):
    """Compatibility wrapper for existing code"""
    pass