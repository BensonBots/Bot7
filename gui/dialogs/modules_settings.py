tk.Spinbox(
            retry_frame,
            from_=5, to=60,
            textvariable=self.retry_delay_var,
            bg="#0a0e16", fg="#ffffff",
            width=10, font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(5, 0))
    
    def _create_march_queues_tab(self):
        """March queues management (for gathering and rallies only)"""
        tab = self._create_scrollable_tab("🚶 March Queues")
        
        self._create_section_header(tab, "🚶 March Queue Management")
        
        # Important note about march queues
        info_frame = self._create_setting_frame(tab, "March Queue Information")
        tk.Label(
            info_frame,
            text="March queues are used for:",
            bg="#161b22", fg="#00d4ff",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w")
        
        uses = [
            "• 🌾 Resource gathering expeditions",
            "• ⚔️ Rally participation", 
            "• 🎯 Manual gathering/attacking"
        ]
        for use in uses:
            tk.Label(
                info_frame,
                text=use,
                bg="#161b22", fg="#ffffff",
                font=("Segoe UI", 10)
            ).pack(anchor="w", padx=(20, 0))
        
        tk.Label(
            info_frame,
            text="Note: Training happens at buildings and doesn't use march queues",
            bg="#161b22", fg="#ff9800",
            font=("Segoe UI", 10, "italic")
        ).pack(anchor="w", pady=(10, 0))
        
        # Queue unlock status
        unlock_frame = self._create_setting_frame(tab, "Unlocked March Queues")
        tk.Label(
            unlock_frame,
            text="Select which march queues you have unlocked:",
            bg="#161b22", fg="#ffffff",
            font=("Segoe UI", 10)
        ).pack(anchor="w")
        
        self.queue_unlock_vars = {}
        queue_info = [
            (1, "Queue 1", "Usually unlocked by default"),
            (2, "Queue 2", "Usually unlocked by default"), 
            (3, "Queue 3", "Requires VIP level or research"),
            (4, "Queue 4", "Requires higher VIP or research"),
            (5, "Queue 5", "Requires high VIP level"),
            (6, "Queue 6", "Requires maximum VIP level")
        ]
        
        for queue_num, queue_name, description in queue_info:
            queue_frame = tk.Frame(unlock_frame, bg="#161b22")
            queue_frame.pack(fill="x", pady=2)
            
            var = tk.BooleanVar()
            self.queue_unlock_vars[queue_num] = var
            
            cb = tk.Checkbutton(
                queue_frame,
                text=queue_name,
                variable=var,
                bg="#161b22", fg="#00d4ff",
                selectcolor="#161b22",
                font=("Segoe UI", 10, "bold")
            )
            cb.pack(side="left")
            
            tk.Label(
                queue_frame,
                text=f"- {description}",
                bg="#161b22", fg="#8b949e",
                font=("Segoe UI", 9)
            ).pack(side="left", padx=(10, 0))
        
        # Queue assignments
        assignment_frame = self._create_setting_frame(tab, "Queue Assignment")
        tk.Label(
            assignment_frame,
            text="Assign unlocked queues to different purposes:",
            bg="#161b22", fg="#ffffff",
            font=("Segoe UI", 10)
        ).pack(anchor="w")
        
        # Assignment table
        self._create_queue_assignment_table(assignment_frame)
        
        # Quick presets
        preset_frame = self._create_setting_frame(tab, "Quick Assignment Presets")
        
        presets = [
            ("🌾 Gathering Focus", {"gather": 4, "rally": 1, "manual": 1}),
            ("⚔️ Rally Ready", {"gather": 3, "rally": 2, "manual": 1}),
            ("🎯 Balanced", {"gather": 3, "rally": 1, "manual": 2}),
            ("🔓 All Manual", {"gather": 0, "rally": 0, "manual": 6})
        ]
        
        for preset_name, preset_config in presets:
            btn = tk.Button(
                preset_frame,
                text=preset_name,
                bg="#2196f3", fg="#ffffff",
                font=("Segoe UI", 9, "bold"),
                relief="flat", bd=0,
                padx=12, pady=6,
                cursor="hand2",
                command=lambda config=preset_config: self._apply_queue_preset(config)
            )
            btn.pack(side="left", padx=(0, 10), pady=5)
    
    def _create_queue_assignment_table(self, parent):
        """Create queue assignment table"""
        table_frame = tk.Frame(parent, bg="#0a0e16", relief="solid", bd=1)
        table_frame.pack(fill="x", pady=(10, 0))
        
        # Headers
        header_frame = tk.Frame(table_frame, bg="#343a46")
        header_frame.pack(fill="x")
        
        headers = ["Queue", "Assignment", "Description"]
        for i, header in enumerate(headers):
            tk.Label(
                header_frame,
                text=header,
                bg="#343a46", fg="#ffffff",
                font=("Segoe UI", 10, "bold"),
                width=15 if i < 2 else 35
            ).grid(row=0, column=i, padx=8, pady=8, sticky="w")
        
        # Assignment options
        self.queue_assignment_vars = {}
        assignment_options = [
            ("AutoGather", "Used by AutoGather module for resource collection"),
            ("Rally/Manual", "Reserved for rally participation and manual use"),
            ("Manual Only", "Completely manual control - automation won't use")
        ]
        
        for queue_num in range(1, 7):
            row_frame = tk.Frame(table_frame, bg="#1e2329")
            row_frame.pack(fill="x", pady=1)
            
            # Queue number
            tk.Label(
                row_frame,
                text=f"Queue {queue_num}",
                bg="#1e2329", fg="#00d4ff",
                font=("Segoe UI", 10, "bold"),
                width=15
            ).grid(row=0, column=0, padx=8, pady=5, sticky="w")
            
            # Assignment dropdown
            var = tk.StringVar()
            self.queue_assignment_vars[queue_num] = var
            
            combo = ttk.Combobox(
                row_frame,
                textvariable=var,
                values=[opt[0] for opt in assignment_options],
                state="readonly",
                width=18
            )
            combo.grid(row=0, column=1, padx=8, pady=5, sticky="w")
            
            # Description label
            desc_label = tk.Label(
                row_frame,
                text="",
                bg="#1e2329", fg="#8b949e",
                font=("Segoe UI", 9),
                anchor="w", width=40
            )
            desc_label.grid(row=0, column=2, padx=8, pady=5, sticky="w")
            
            # Update description when selection changes
            def update_desc(event, desc_label=desc_label, var=var):
                selection = var.get()
                for option, description in assignment_options:
                    if option == selection:
                        desc_label.configure(text=description)
                        break
            
            combo.bind('<<ComboboxSelected>>', update_desc)
    
    def _apply_queue_preset(self, preset_config):
        """Apply queue assignment preset"""
        assignments = {
            "gather": "AutoGather",
            "rally": "Rally/Manual",
            "manual": "Manual Only"
        }
        
        queue_num = 1
        for assignment_type, count in preset_config.items():
            assignment_name = assignments[assignment_type]
            for _ in range(count):
                if queue_num <= 6:
                    self.queue_assignment_vars[queue_num].set(assignment_name)
                    queue_num += 1
    
    def _create_gathering_tab(self):
        """AutoGather settings"""
        tab = self._create_scrollable_tab("🌾 Gathering")
        
        self._create_section_header(tab, "🌾 AutoGather Configuration")
        
        # Enable/disable
        enable_frame = self._create_setting_frame(tab, "Module Control")
        self.gather_enabled_var = tk.BooleanVar()
        tk.Checkbutton(
            enable_frame,
            text="Enable AutoGather module",
            variable=self.gather_enabled_var,
            bg="#161b22", fg="#ffffff",
            selectcolor="#161b22",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w")
        
        # Resource selection
        resource_frame = self._create_setting_frame(tab, "Resource Types")
        tk.Label(
            resource_frame,
            text="Select which resources to gather:",
            bg="#161b22", fg="#ffffff",
            font=("Segoe UI", 10)
        ).pack(anchor="w")
        
        self.resource_vars = {}
        resources = [
            ("food", "🍞 Food", "#ffeb3b"),
            ("wood", "🌳 Wood", "#4caf50"),
            ("iron", "⚒️ Iron", "#9e9e9e"), 
            ("stone", "🗿 Stone", "#795548")
        ]
        
        for resource_id, resource_name, color in resources:
            var = tk.BooleanVar()
            self.resource_vars[resource_id] = var
            
            tk.Checkbutton(
                resource_frame,
                text=resource_name,
                variable=var,
                bg="#161b22", fg=color,
                selectcolor="#161b22",
                font=("Segoe UI", 10, "bold")
            ).pack(anchor="w", pady=2)
        
        # Resource priorities
        priority_frame = self._create_setting_frame(tab, "Gathering Priority Order")
        tk.Label(
            priority_frame,
            text="Priority order (highest to lowest):",
            bg="#161b22", fg="#ffffff",
            font=("Segoe UI", 10)
        ).pack(anchor="w")
        
        self._create_priority_list(priority_frame)
        
        # Gathering parameters
        params_frame = self._create_setting_frame(tab, "Gathering Settings")
        
        tk.Label(params_frame, text="Check interval (seconds):",
                bg="#161b22", fg="#ffffff", font=("Segoe UI", 10)).pack(anchor="w")
        self.gather_interval_var = tk.StringVar()
        tk.Spinbox(
            params_frame,
            from_=15, to=300,
            textvariable=self.gather_interval_var,
            bg="#0a0e16", fg="#ffffff",
            width=10, font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(5, 10))
        
        tk.Label(params_frame, text="Minimum march capacity:",
                bg="#161b22", fg="#ffffff", font=("Segoe UI", 10)).pack(anchor="w")
        self.min_capacity_var = tk.StringVar()
        tk.Entry(
            params_frame,
            textvariable=self.min_capacity_var,
            bg="#0a0e16", fg="#ffffff",
            width=15, font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(5, 0))
        
        # Note about queue usage
        note_frame = self._create_setting_frame(tab, "Queue Usage")
        tk.Label(
            note_frame,
            text="AutoGather will use march queues assigned as 'AutoGather'",
            bg="#161b22", fg="#ff9800",
            font=("Segoe UI", 10, "italic")
        ).pack(anchor="w")
        tk.Label(
            note_frame,
            text="Configure queue assignments in the 'March Queues' tab",
            bg="#161b22", fg="#8b949e",
            font=("Segoe UI", 9)
        ).pack(anchor="w")
    
    def _create_priority_list(self, parent):
        """Create priority ordering list"""
        list_frame = tk.Frame(parent, bg="#0a0e16", relief="solid", bd=1)
        list_frame.pack(fill="x", pady=(5, 0))
        
        self.priority_listbox = tk.Listbox(
            list_frame,
            bg="#0a0e16", fg="#ffffff",
            font=("Segoe UI", 10),
            height=4,
            selectbackground="#00d4ff",
            selectforeground="#000000",
            relief="flat", bd=0
        )
        self.priority_listbox.pack(fill="x", padx=5, pady=5)
        
        # Default priorities
        priorities = ["🌟 Iron (Highest)", "🍞 Food", "🌳 Wood", "🗿 Stone (Lowest)"]
        for priority in priorities:
            self.priority_listbox.insert(tk.END, priority)
        
        # Move buttons
        btn_frame = tk.Frame(list_frame, bg="#0a0e16")
        btn_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        tk.Button(
            btn_frame,
            text="▲ Up",
            bg="#2196f3", fg="#ffffff",
            font=("Segoe UI", 8, "bold"),
            relief="flat", bd=0,
            padx=8, pady=3,
            command=self._move_priority_up
        ).pack(side="left", padx=(0, 5))
        
        tk.Button(
            btn_frame,
            text="▼ Down",
            bg="#ff9800", fg="#ffffff", 
            font=("Segoe UI", 8, "bold"),
            relief="flat", bd=0,
            padx=8, pady=3,
            command=self._move_priority_down
        ).pack(side="left")
    
    def _move_priority_up(self):
        """Move selected priority up"""
        selection = self.priority_listbox.curselection()
        if selection and selection[0] > 0:
            index = selection[0]
            item = self.priority_listbox.get(index)
            self.priority_listbox.delete(index)
            self.priority_listbox.insert(index - 1, item)
            self.priority_listbox.selection_set(index - 1)
    
    def _move_priority_down(self):
        """Move selected priority down"""
        selection = self.priority_listbox.curselection()
        if selection and selection[0] < self.priority_listbox.size() - 1:
            index = selection[0]
            item = self.priority_listbox.get(index)
            self.priority_listbox.delete(index)
            self.priority_listbox.insert(index + 1, item)
            self.priority_listbox.selection_set(index + 1)
    
    def _create_training_tab(self):
        """AutoTrain settings (building-based, not march queues)"""
        tab = self._create_scrollable_tab("⚔️ Training")
        
        self._create_section_header(tab, "⚔️ AutoTrain Configuration")
        
        # Important note
        info_frame = self._create_setting_frame(tab, "Training System")
        tk.Label(
            info_frame,
            text="Training happens at buildings (Barracks, Range, Stable, Workshop)",
            bg="#161b22", fg="#00d4ff",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w")
        tk.Label(
            info_frame,
            text="Training does NOT use march queues - it uses building queues",
            bg="#161b22", fg="#ff9800",
            font=("Segoe UI", 10, "italic")
        ).pack(anchor="w", pady=(5, 0))
        
        # Enable/disable
        enable_frame = self._create_setting_frame(tab, "Module Control")
        self.train_enabled_var = tk.BooleanVar()
        tk.Checkbutton(
            enable_frame,
            text="Enable AutoTrain module",
            variable=self.train_enabled_var,
            bg="#161b22", fg="#ffffff",
            selectcolor="#161b22",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w")
        
        # Troop priorities
        priority_frame = self._create_setting_frame(tab, "Training Priorities")
        tk.Label(
            priority_frame,
            text="Select troop types to train (in priority order):",
            bg="#161b22", fg="#ffffff",
            font=("Segoe UI", 10)
        ).pack(anchor="w")
        
        self.troop_vars = {}
        troops = [
            ("infantry", "⚔️ Infantry", "#ff6b6b"),
            ("ranged", "🏹 Ranged", "#4caf50"),
            ("cavalry", "🐎 Cavalry", "#2196f3"),
            ("siege", "🏛️ Siege", "#9c27b0")
        ]
        
        for troop_id, troop_name, color in troops:
            var = tk.BooleanVar()
            self.troop_vars[troop_id] = var
            
            tk.Checkbutton(
                priority_frame,
                text=troop_name,
                variable=var,
                bg="#161b22", fg=color,
                selectcolor="#161b22",
                font=("Segoe UI", 10, "bold")
            ).pack(anchor="w", pady=2)
        
        # Training parameters
        params_frame = self._create_setting_frame(tab, "Training Settings")
        
        tk.Label(params_frame, text="Check interval (seconds):",
                bg="#161b22", fg="#ffffff", font=("Segoe UI", 10)).pack(anchor="w")
        self.train_interval_var = tk.StringVar()
        tk.Spinbox(
            params_frame,
            from_=30, to=600,
            textvariable=self.train_interval_var,
            bg="#0a0e16", fg="#ffffff",
            width=10, font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(5, 10))
        
        tk.Label(params_frame, text="Minimum resource threshold:",
                bg="#161b22", fg="#ffffff", font=("Segoe UI", 10)).pack(anchor="w")
        self.resource_threshold_var = tk.StringVar()
        tk.Entry(
            params_frame,
            textvariable=self.resource_threshold_var,
            bg="#0a0e16", fg="#ffffff",
            width=15, font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(5, 0))
    
    def _create_mail_tab(self):
        """AutoMail settings"""
        tab = self._create_scrollable_tab("📬 Mail")
        
        self._create_section_header(tab, "📬 AutoMail Configuration")
        
        # Enable/disable
        enable_frame = self._create_setting_frame(tab, "Module Control")
        self.mail_enabled_var = tk.BooleanVar()
        tk.Checkbutton(
            enable_frame,
            text="Enable AutoMail module",
            variable=self.mail_enabled_var,
            bg="#161b22", fg="#ffffff",
            selectcolor="#161b22",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w")
        
        # Claim settings
        claim_frame = self._create_setting_frame(tab, "Auto-Claim Settings")
        tk.Label(
            claim_frame,
            text="Automatically claim these reward types:",
            bg="#161b22", fg="#ffffff",
            font=("Segoe UI", 10)
        ).pack(anchor="w")
        
        self.mail_claim_vars = {}
        claim_types = [
            ("resources", "💰 Resources (food, wood, iron, stone)", "#ffeb3b"),
            ("items", "⚔️ Items and equipment", "#9c27b0"),
            ("speedups", "⏰ Speed-ups and boosts", "#00bcd4"),
            ("gems", "💎 Gems and premium currency", "#e91e63")
        ]
        
        for claim_id, claim_name, color in claim_types:
            var = tk.BooleanVar()
            self.mail_claim_vars[claim_id] = var
            
            tk.Checkbutton(
                claim_frame,
                text=claim_name,
                variable=var,
                bg="#161b22", fg=color,
                selectcolor="#161b22",
                font=("Segoe UI", 10, "bold")
            ).pack(anchor="w", pady=2)
        
        # Mail management
        manage_frame = self._create_setting_frame(tab, "Mail Management")
        self.delete_read_var = tk.BooleanVar()
        tk.Checkbutton(
            manage_frame,
            text="🗑️ Auto-delete read mails (be careful!)",
            variable=self.delete_read_var,
            bg="#161b22", fg="#ff6b6b",
            selectcolor="#161b22",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")
        
        # Check interval
        interval_frame = self._create_setting_frame(tab, "Check Settings")
        tk.Label(interval_frame, text="Check mail interval (seconds):",
                bg="#161b22", fg="#ffffff", font=("Segoe UI", 10)).pack(anchor="w")
        self.mail_interval_var = tk.StringVar()
        tk.Spinbox(
            interval_frame,
            from_=60, to=600,
            textvariable=self.mail_interval_var,
            bg="#0a0e16", fg="#ffffff",
            width=10, font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(5, 0))
    
    def _create_scrollable_tab(self, tab_name):
        """Create a scrollable tab"""
        tab = tk.Frame(self.notebook, bg="#1e2329")
        self.notebook.add(tab, text=tab_name)
        
        # Create scrollable frame
        canvas = tk.Canvas(tab, bg="#1e2329", highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1e2329")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return scrollable_frame
    
    def _create_section_header(self, parent, title):
        """Create section header"""
        header = tk.Frame(parent, bg="#343a46", height=45)
        header.pack(fill="x", pady=(0, 15))
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text=title,
            bg="#343a46", fg="#ffffff",
            font=("Segoe UI", 14, "bold")
        ).pack(side="left", padx=20, pady=12)
    
    def _create_setting_frame(self, parent, title):
        """Create setting frame"""
        tk.Label(
            parent,
            text=title,
            bg="#1e2329", fg="#00d4ff",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(15, 8))
        
        frame = tk.Frame(parent, bg="#161b22", relief="solid", bd=1)
        frame.pack(fill="x", pady=(0, 10))
        
        content = tk.Frame(frame, bg="#161b22")
        content.pack(fill="x", padx=20, pady=15)
        
        return content
    
    def _setup_footer(self):
        """Setup footer with save/cancel buttons"""
        footer = tk.Frame(self.main_frame, bg="#1e2329")
        footer.pack(fill="x", pady=(15, 0))
        
        # Status
        self.status_label = tk.Label(
            footer,
            text="",
            bg="#1e2329", fg="#8b949e",
            font=("Segoe UI", 10)
        )
        self.status_label.pack(side="left")
        
        # Buttons
        btn_frame = tk.Frame(footer, bg="#1e2329")
        btn_frame.pack(side="right")
        
        tk.Button(
            btn_frame,
            text="❌ Cancel",
            bg="#ff6b6b", fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
            relief="flat", bd=0,
            padx=20, pady=10,
            cursor="hand2",
            command=self._cancel
        ).pack(side="left", padx=(0, 15))
        
        tk.Button(
            btn_frame,
            text="💾 Save Settings",
            bg="#00ff88", fg="#000000", 
            font=("Segoe UI", 11, "bold"),
            relief="flat", bd=0,
            padx=20, pady=10,
            cursor="hand2",
            command=self._save_settings
        ).pack(side="left")
    
    def _load_settings(self):
        """Load settings from file"""
        default_settings = {
            "autostart_game": {
                "auto_startup": False,
                "max_retries": 3,
                "retry_delay": 10,
                "enabled": True
            },
            "march_queues": {
                "unlocked_queues": [1, 2],
                "queue_assignments": {
                    "1": "AutoGather",
                    "2": "AutoGather",
                    "3": "Rally/Manual",
                    "4": "Rally/Manual",
                    "5": "Manual Only",
                    "6": "Manual Only"
                }
            },
            "auto_gather": {
                "enabled": True,
                "check_interval": 30,
                "resource_types": ["iron", "food", "wood", "stone"],
                "resource_priorities": ["iron", "food", "wood", "stone"],
                "min_march_capacity": 100000
            },
            "auto_train": {
                "enabled": True,
                "check_interval": 60,
                "troop_types": ["infantry", "ranged", "cavalry"],
                "min_resource_threshold": 50000
            },
            "auto_mail": {
                "enabled": True,
                "check_interval": 120,
                "claim_resources": True,
                "claim_items": True,
                "claim_speedups": True,
                "claim_gems": True,
                "delete_read_mail": False
            }
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                
                # Merge with defaults
                for key, value in default_settings.items():
                    if key not in settings:
                        settings[key] = value
                    elif isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if subkey not in settings[key]:
                                settings[key][subkey] = subvalue
                
                return settings
        except Exception as e:
            print(f"Error loading settings: {e}")
        
        return default_settings
    
    def _load_current_values(self):
        """Load current settings into UI"""
        try:
            # AutoStart
            autostart = self.settings.get("autostart_game", {})
            self.autostart_var.set(autostart.get("auto_startup", False))
            self.max_retries_var.set(str(autostart.get("max_retries", 3)))
            self.retry_delay_var.set(str(autostart.get("retry_delay", 10)))
            
            # March queues
            march_config = self.settings.get("march_queues", {})
            unlocked = march_config.get("unlocked_queues", [1, 2])
            assignments = march_config.get("queue_assignments", {})
            
            for queue_num in range(1, 7):
                if queue_num in self.queue_unlock_vars:
                    self.queue_unlock_vars[queue_num].set(queue_num in unlocked)
                if queue_num in self.queue_assignment_vars:
                    self.queue_assignment_vars[queue_num].set(
                        assignments.get(str(queue_num), "AutoGather")
                    )
            
            # Gathering
            gather = self.settings.get("auto_gather", {})
            self.gather_enabled_var.set(gather.get("enabled", True))
            self.gather_interval_var.set(str(gather.get("check_interval", 30)))
            self.min_capacity_var.set(str(gather.get("min_march_capacity", 100000)))
            
            resource_types = gather.get("resource_types", ["iron", "food", "wood", "stone"])
            for resource_id, var in self.resource_vars.items():
                var.set(resource_id in resource_types)
            
            # Training
            train = self.settings.get("auto_train", {})
            self.train_enabled_var.set(train.get("enabled", True))
            self.train_interval_var.set(str(train.get("check_interval", 60)))
            self.resource_threshold_var.set(str(train.get("min_resource_threshold", 50000)))
            
            troop_types = train.get("troop_types", ["infantry", "ranged", "cavalry"])
            for troop_id, var in self.troop_vars.items():
                var.set(troop_id in troop_types)
            
            # Mail
            mail = self.settings.get("auto_mail", {})
            self.mail_enabled_var.set(mail.get("enabled", True))
            self.mail_interval_var.set(str(mail.get("check_interval", 120)))
            self.delete_read_var.set(mail.get("delete_read_mail", False))
            
            claim_settings = ["resources", "items", "speedups", "gems"]
            for claim_type in claim_settings:
                if claim_type in self.mail_claim_vars:
                    self.mail_claim_vars[claim_type].set(
                        mail.get(f"claim_{claim_type}", True)
                    )
            
        except Exception as e:
            print(f"Error loading current values: {e}")
    
    def _save_settings(self):
        """Save all settings"""
        try:
            # Collect AutoStart settings
            self.settings["autostart_game"] = {
                "auto_startup": self.autostart_var.get(),
                "max_retries": int(self.max_retries_var.get()),
                "retry_delay": int(self.retry_delay_var.get()),
                "enabled": True
            }
            
            # Collect march queue settings
            unlocked_queues = [
                queue_num for queue_num, var in self.queue_unlock_vars.items()
                if var.get()
            ]
            
            queue_assignments = {}
            for queue_num, var in self.queue_assignment_vars.items():
                assignment = var.get()
                if assignment:  # Only save if assignment is selected
                    queue_assignments[str(queue_num)] = assignment
            
            self.settings["march_queues"] = {
                "unlocked_queues": unlocked_queues,
                "queue_assignments": queue_assignments
            }
            
            # Collect gathering settings
            selected_resources = [
                res_id for res_id, var in self.resource_vars.items() if var.get()
            ]
            
            # Get priorities from listbox
            priority_mapping = {
                "🌟 Iron": "iron", "🍞 Food": "food", 
                "🌳 Wood": "wood", "🗿 Stone": "stone"
            }
            priorities = []
            for i in range(self.priority_listbox.size()):
                item = self.priority_listbox.get(i)
                for display, resource_id in priority_mapping.items():
                    if display in item:
                        priorities.append(resource_id)
                        break
            
            self.settings["auto_gather"] = {
                "enabled": self.gather_enabled_var.get(),
                "check_interval": int(self.gather_interval_var.get()),
                "resource_types": selected_resources,
                "resource_priorities": priorities,
                "min_march_capacity": int(self.min_capacity_var.get())
            }
            
            # Collect training settings
            selected_troops = [
                troop_id for troop_id, var in self.troop_vars.items() if var.get()
            ]
            
            self.settings["auto_train"] = {
                "enabled": self.train_enabled_var.get(),
                "check_interval": int(self.train_interval_var.get()),
                "troop_types": selected_troops,
                "min_resource_threshold": int(self.resource_threshold_var.get())
            }
            
            # Collect mail settings
            mail_settings = {
                "enabled": self.mail_enabled_var.get(),
                "check_interval": int(self.mail_interval_var.get()),
                "delete_read_mail": self.delete_read_var.get()
            }
            
            # Add claim settings
            for claim_type, var in self.mail_claim_vars.items():
                mail_settings[f"claim_{claim_type}"] = var.get()
            
            self.settings["auto_mail"] = mail_settings
            
            # Save to file
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            
            # Notify app
            if self.app_ref:
                self.app_ref.add_console_message(f"✅ Saved module settings for {self.instance_name}")
                
                # Reload settings in module manager
                if hasattr(self.app_ref, 'module_manager'):
                    self.app_ref.module_manager.reload_instance_settings(self.instance_name)
            
            self.status_label.configure(text="✅ Settings saved successfully", fg="#00ff88")
            self.window.after(3000, lambda: self.status_label.configure(text=""))
            
        except Exception as e:
            error_msg = f"❌ Error saving: {str(e)}"
            self.status_label.configure(text=error_msg, fg="#ff6b6b")
            print(error_msg)
    
    def _cancel(self):
        """Cancel and close"""
        self.window.destroy()


def show_corrected_module_settings(parent, instance_name, app_ref=None):
    """Show the corrected module settings window"""
    try:
        window = CorrectedModuleSettingsWindow(parent, instance_name, app_ref)
        return window
    except Exception as e:
        messagebox.showerror("Error", f"Could not open settings: {str(e)}")
        return None"""
BENSON v2.0 - Corrected Advanced Settings GUI
March queues are for gathering and rallies only, training is separate
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os


class CorrectedModuleSettingsWindow:
    """Corrected settings window with proper march queue understanding"""
    
    def __init__(self, parent, instance_name, app_ref=None):
        self.parent = parent
        self.instance_name = instance_name
        self.app_ref = app_ref
        
        # Load current settings
        self.settings_file = f"settings_{instance_name}.json"
        self.settings = self._load_settings()
        
        # Create window
        self._create_window()
        
        # Setup tabbed interface
        self._setup_tabs()
        
        # Load current values
        self._load_current_values()
    
    def _create_window(self):
        """Create the main settings window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"Module Settings - {self.instance_name}")
        self.window.geometry("900x800")
        self.window.configure(bg="#1e2329")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (450)
        y = (self.window.winfo_screenheight() // 2) - (400)
        self.window.geometry(f"900x800+{x}+{y}")
        
        # Main container
        self.main_frame = tk.Frame(self.window, bg="#1e2329")
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Header
        self._setup_header()
        
        # Footer
        self._setup_footer()
    
    def _setup_header(self):
        """Setup header section"""
        header = tk.Frame(self.main_frame, bg="#1e2329")
        header.pack(fill="x", pady=(0, 20))
        
        tk.Label(
            header,
            text=f"⚙️ Module Configuration: {self.instance_name}",
            bg="#1e2329",
            fg="#00d4ff",
            font=("Segoe UI", 18, "bold")
        ).pack(side="left")
        
        # Instance status
        if self.app_ref:
            instance = self.app_ref.instance_manager.get_instance(self.instance_name)
            status = instance["status"] if instance else "Unknown"
            status_color = "#00ff88" if status == "Running" else "#8b949e"
            
            tk.Label(
                header,
                text=f"Status: {status}",
                bg="#1e2329",
                fg=status_color,
                font=("Segoe UI", 12, "bold")
            ).pack(side="right")
    
    def _setup_tabs(self):
        """Setup tabbed interface"""
        # Create notebook
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background='#1e2329', borderwidth=0)
        style.configure('TNotebook.Tab', background='#343a46', foreground='#ffffff', 
                       padding=[15, 10], focuscolor='none')
        style.map('TNotebook.Tab', background=[('selected', '#00d4ff')], 
                 foreground=[('selected', '#000000')])
        
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True, pady=(0, 20))
        
        # Create tabs
        self._create_autostart_tab()
        self._create_march_queues_tab()
        self._create_gathering_tab()
        self._create_training_tab()
        self._create_mail_tab()
    
    def _create_autostart_tab(self):
        """AutoStartGame settings"""
        tab = self._create_scrollable_tab("🎮 AutoStart")
        
        self._create_section_header(tab, "🎮 AutoStartGame Configuration")
        
        # Auto startup
        frame = self._create_setting_frame(tab, "Auto-Startup Settings")
        self.autostart_var = tk.BooleanVar()
        tk.Checkbutton(
            frame,
            text="Automatically start game when instance becomes running",
            variable=self.autostart_var,
            bg="#161b22",
            fg="#ffffff",
            selectcolor="#161b22",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=5)
        
        # Max retries
        retry_frame = self._create_setting_frame(tab, "Retry Configuration")
        tk.Label(retry_frame, text="Maximum start attempts:", 
                bg="#161b22", fg="#ffffff", font=("Segoe UI", 10)).pack(anchor="w")
        self.max_retries_var = tk.StringVar()
        tk.Spinbox(
            retry_frame,
            from_=1, to=10,
            textvariable=self.max_retries_var,
            bg="#0a0e16", fg="#ffffff",
            width=10, font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(5, 0))
        
        tk.Label(retry_frame, text="Delay between retries (seconds):", 
                bg="#161b22", fg="#ffffff", font=("Segoe UI", 10)).pack(anchor="w", pady=(10, 0))
        self.retry_delay_var = tk.StringVar()
        tk.Spinbox(