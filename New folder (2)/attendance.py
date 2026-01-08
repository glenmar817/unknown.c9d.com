import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import sqlite3
from datetime import datetime
import pandas as pd
from tkinter import filedialog
import threading
import time
import os
import shutil

class ModernAttendanceSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("RFID Attendance Monitoring System")
        self.root.geometry("1100x750")
        self.root.configure(bg='#1a1a2e')
        
        # Colors
        self.colors = {
            'bg': '#1a1a2e',
            'sidebar': '#16213e',
            'accent': '#0f3460',
            'primary': '#e94560',
            'secondary': '#533483',
            'success': '#06d6a0',
            'warning': '#ffd166',
            'danger': '#ef476f',
            'info': '#118ab2',
            'text': '#ffffff',
            'text_dark': '#a0a0a0',
            'card_bg': '#1f4068'
        }
        
        # Database setup
        self.setup_database()
        
        # Serial connection
        self.serial_port = None
        self.is_monitoring = False
        self.scanning_for_register = False
        self.connected_port = None
        
        # Create modern GUI
        self.create_modern_gui()
        
        # Auto-detect ports on startup
        self.root.after(1000, self.auto_detect_ports)
        
    def setup_database(self):
        self.conn = sqlite3.connect('attendance.db')
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rfid_uid TEXT UNIQUE,
                name TEXT,
                department TEXT,
                position TEXT,
                registered_date TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rfid_uid TEXT,
                name TEXT,
                time_in TEXT,
                time_out TEXT,
                date TEXT,
                status TEXT DEFAULT 'Present'
            )
        ''')
        self.conn.commit()
    
    def create_modern_gui(self):
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True)
        
        self.create_sidebar(main_container)
        
        self.content_frame = tk.Frame(main_container, bg=self.colors['bg'])
        self.content_frame.pack(side='left', fill='both', expand=True, padx=20, pady=20)
        
        self.show_dashboard()
    
    def create_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=self.colors['sidebar'], width=250)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        
        # Logo/Title
        logo_frame = tk.Frame(sidebar, bg=self.colors['sidebar'])
        logo_frame.pack(pady=20, padx=10, fill='x')
        
        tk.Label(logo_frame, text="🔐", font=('Arial', 36),
                bg=self.colors['sidebar'], fg=self.colors['primary']).pack(pady=(10, 5))
        
        tk.Label(logo_frame, text="RFID ATTENDANCE", font=('Arial', 14, 'bold'),
                bg=self.colors['sidebar'], fg=self.colors['text']).pack()
        tk.Label(logo_frame, text="MONITORING SYSTEM", font=('Arial', 9),
                bg=self.colors['sidebar'], fg=self.colors['text_dark']).pack(pady=(0, 20))
        
        # Navigation
        nav_frame = tk.Frame(sidebar, bg=self.colors['sidebar'])
        nav_frame.pack(fill='x', padx=10)
        
        self.create_menu_button(nav_frame, "📊 Dashboard", self.show_dashboard)
        self.create_menu_button(nav_frame, "👁️ Live Monitor", self.show_monitor)
        self.create_menu_button(nav_frame, "👤 Register User", self.show_register)
        self.create_menu_button(nav_frame, "📋 Attendance Log", self.show_records)
        self.create_menu_button(nav_frame, "📈 Reports", self.show_reports)
        self.create_menu_button(nav_frame, "⚙️ Settings", self.show_settings)
        
        # Status Bar
        status_frame = tk.Frame(sidebar, bg=self.colors['sidebar'])
        status_frame.pack(side='bottom', fill='x', pady=20, padx=10)
        
        tk.Label(status_frame, text="System Status", font=('Arial', 9, 'bold'),
                bg=self.colors['sidebar'], fg=self.colors['text_dark']).pack(anchor='w')
        
        self.connection_status = tk.Label(status_frame, text="⚫ Disconnected", 
                                         font=('Arial', 9), bg=self.colors['sidebar'], 
                                         fg=self.colors['text_dark'])
        self.connection_status.pack(anchor='w', pady=(5, 0))
        
        self.port_status = tk.Label(status_frame, text="Port: Not Detected", 
                                   font=('Arial', 8), bg=self.colors['sidebar'], 
                                   fg=self.colors['text_dark'])
        self.port_status.pack(anchor='w')
        
        # Auto-refresh button
        refresh_btn = tk.Button(status_frame, text="🔄 Refresh Ports", 
                               font=('Arial', 8), bg=self.colors['accent'],
                               fg=self.colors['text'], bd=0, cursor='hand2',
                               command=self.auto_detect_ports, padx=10, pady=2)
        refresh_btn.pack(anchor='w', pady=(10, 0))
    
    def create_menu_button(self, parent, text, command):
        btn = tk.Button(parent, text=text, font=('Arial', 11), 
                       bg=self.colors['sidebar'], fg=self.colors['text'],
                       activebackground=self.colors['primary'], 
                       activeforeground=self.colors['text'],
                       bd=0, pady=12, anchor='w', padx=20,
                       cursor='hand2', command=command)
        btn.pack(fill='x', pady=2)
        
        btn.bind('<Enter>', lambda e: btn.config(bg=self.colors['accent']))
        btn.bind('<Leave>', lambda e: btn.config(bg=self.colors['sidebar']))
    
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def auto_detect_ports(self):
        """Automatically detect and list available COM ports"""
        ports = serial.tools.list_ports.comports()
        available_ports = []
        
        for port in ports:
            try:
                available_ports.append({
                    'port': port.device,
                    'description': port.description,
                    'manufacturer': port.manufacturer if port.manufacturer else "Unknown"
                })
            except:
                continue
        
        # Update status
        if available_ports:
            port_text = f"📡 {available_ports[0]['port']} - {available_ports[0]['description'][:20]}..."
            self.port_status.config(text=port_text, fg=self.colors['success'])
        else:
            self.port_status.config(text="⚠️ No ports detected", fg=self.colors['warning'])
        
        # Update settings dropdown if on settings page
        if hasattr(self, 'port_combo'):
            self.port_combo['values'] = [f"{p['port']} - {p['description']}" for p in available_ports]
            if available_ports:
                self.port_combo.set(available_ports[0]['port'])
        
        return available_ports
    
    def show_dashboard(self):
        self.clear_content()
        
        # Header
        header_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        header_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(header_frame, text="📊 Dashboard", font=('Arial', 28, 'bold'),
                bg=self.colors['bg'], fg=self.colors['text']).pack(side='left')
        
        date_label = tk.Label(header_frame, text=datetime.now().strftime("%B %d, %Y %H:%M"),
                             font=('Arial', 11), bg=self.colors['bg'], fg=self.colors['text_dark'])
        date_label.pack(side='right')
        
        # Stats Cards
        stats_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        stats_frame.pack(fill='x', pady=10)
        
        self.cursor.execute("SELECT COUNT(*) FROM users")
        total_users = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute("SELECT COUNT(*) FROM attendance WHERE date=?", 
                          (datetime.now().strftime("%Y-%m-%d"),))
        today_attendance = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute("SELECT COUNT(*) FROM attendance WHERE time_out IS NULL AND date=?",
                          (datetime.now().strftime("%Y-%m-%d"),))
        currently_in = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute("SELECT COUNT(DISTINCT name) FROM attendance WHERE date=?",
                          (datetime.now().strftime("%Y-%m-%d"),))
        present_today = self.cursor.fetchone()[0] or 0
        
        self.create_stat_card(stats_frame, "👥 TOTAL USERS", str(total_users), 
                             f"{total_users} Registered", self.colors['primary'])
        self.create_stat_card(stats_frame, "📊 TODAY'S LOGS", str(today_attendance), 
                             f"{present_today} Present Today", self.colors['success'])
        self.create_stat_card(stats_frame, "🟢 CURRENTLY IN", str(currently_in), 
                             "In Office", self.colors['warning'])
        
        # Calculate monthly average
        try:
            self.cursor.execute("""
                SELECT COUNT(DISTINCT date) as days, 
                       COUNT(*) as total_logs,
                       COUNT(DISTINCT name) as avg_per_day
                FROM attendance 
                WHERE date >= date('now', '-30 days')
            """)
            stats = self.cursor.fetchone()
            if stats[0] > 0:
                monthly_avg = round((stats[2] / stats[0]) / total_users * 100 if total_users > 0 else 0)
                monthly_avg = min(monthly_avg, 100)  # Cap at 100%
            else:
                monthly_avg = 0
        except:
            monthly_avg = 0
            
        self.create_stat_card(stats_frame, "📅 MONTHLY AVG", f"{monthly_avg}%", 
                             "Attendance Rate", self.colors['info'])
        
        # Recent Activity & Quick Actions
        bottom_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        bottom_frame.pack(fill='both', expand=True, pady=20)
        
        # Left - Recent Activity
        activity_frame = tk.LabelFrame(bottom_frame, text="  Recent Activity  ", 
                                      font=('Arial', 12, 'bold'), bg=self.colors['card_bg'],
                                      fg=self.colors['text'], bd=1, relief='flat')
        activity_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Activity list with scrollbar
        activity_container = tk.Frame(activity_frame, bg=self.colors['card_bg'])
        activity_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.activity_text = tk.Text(activity_container, font=('Consolas', 10), 
                                    bg=self.colors['sidebar'], fg=self.colors['text'],
                                    bd=0, height=12, state='disabled')
        self.activity_text.pack(side='left', fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(activity_container, command=self.activity_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.activity_text.config(yscrollcommand=scrollbar.set)
        
        self.load_recent_activity()
        
        # Right - Quick Actions
        action_frame = tk.LabelFrame(bottom_frame, text="  Quick Actions  ", 
                                    font=('Arial', 12, 'bold'), bg=self.colors['card_bg'],
                                    fg=self.colors['text'], bd=1, relief='flat')
        action_frame.pack(side='right', fill='both', padx=(10, 0), ipady=10)
        
        actions = [
            ("🔗 Connect Scanner", self.connect_arduino),
            ("📝 Manual Entry", self.show_monitor),
            ("👤 Add New User", self.show_register),
            ("📤 Export Data", self.export_to_excel)
        ]
        
        for text, command in actions:
            btn = tk.Button(action_frame, text=text, font=('Arial', 11), 
                           bg=self.colors['accent'], fg=self.colors['text'],
                           bd=0, pady=12, cursor='hand2', command=command)
            btn.pack(fill='x', padx=20, pady=5)
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=self.colors['primary']))
            btn.bind('<Leave>', lambda e, b=btn: b.config(bg=self.colors['accent']))
    
    def create_stat_card(self, parent, title, value, subtitle, color):
        card = tk.Frame(parent, bg=color, bd=0, relief='raised')
        card.pack(side='left', fill='both', expand=True, padx=5)
        
        inner = tk.Frame(card, bg=color)
        inner.pack(padx=20, pady=15)
        
        tk.Label(inner, text=title, font=('Arial', 10, 'bold'), bg=color, 
                fg=self.colors['text']).pack(anchor='w')
        tk.Label(inner, text=value, font=('Arial', 32, 'bold'), bg=color,
                fg=self.colors['text']).pack(anchor='w', pady=(5, 2))
        tk.Label(inner, text=subtitle, font=('Arial', 9), bg=color,
                fg=self.colors['text'], anchor='w').pack(anchor='w')
    
    def load_recent_activity(self):
        self.activity_text.config(state='normal')
        self.activity_text.delete(1.0, 'end')
        
        self.cursor.execute("""
            SELECT name, time_in, time_out, date 
            FROM attendance 
            ORDER BY date DESC, time_in DESC LIMIT 15
        """)
        
        for row in self.cursor.fetchall():
            name, time_in, time_out, date = row
            if time_out:
                status = "OUT"
                time = time_out
                emoji = "🔴"
            else:
                status = "IN"
                time = time_in
                emoji = "🟢"
            
            self.activity_text.insert('end', 
                f"{emoji} {name:<20} {status:>5} {time:>10} {date}\n")
        
        self.activity_text.config(state='disabled')
    
    def show_monitor(self):
        self.clear_content()
        
        # Header
        header_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        header_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(header_frame, text="👁️ Live Monitor", font=('Arial', 28, 'bold'),
                bg=self.colors['bg'], fg=self.colors['text']).pack(side='left')
        
        # Connection Status
        conn_status = "🟢 Connected" if self.is_monitoring else "🔴 Disconnected"
        status_color = self.colors['success'] if self.is_monitoring else self.colors['danger']
        tk.Label(header_frame, text=conn_status, font=('Arial', 11),
                bg=self.colors['bg'], fg=status_color).pack(side='right', padx=10)
        
        # Main Content
        main_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        main_frame.pack(fill='both', expand=True)
        
        # Left Panel - Manual Entry
        left_frame = tk.LabelFrame(main_frame, text="  Manual Entry  ", 
                                  font=('Arial', 12, 'bold'), bg=self.colors['card_bg'],
                                  fg=self.colors['text'], bd=1, relief='flat')
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        manual_content = tk.Frame(left_frame, bg=self.colors['card_bg'])
        manual_content.pack(padx=20, pady=20, fill='both')
        
        tk.Label(manual_content, text="Enter RFID UID:", font=('Arial', 11),
                bg=self.colors['card_bg'], fg=self.colors['text']).pack(anchor='w', pady=(0, 5))
        
        entry_frame = tk.Frame(manual_content, bg=self.colors['card_bg'])
        entry_frame.pack(fill='x', pady=(0, 15))
        
        self.manual_rfid_entry = tk.Entry(entry_frame, font=('Arial', 14), bd=0,
                                          bg=self.colors['sidebar'], fg=self.colors['text'],
                                          insertbackground=self.colors['text'])
        self.manual_rfid_entry.pack(side='left', fill='x', expand=True, ipady=8, padx=(0, 10))
        
        process_btn = tk.Button(entry_frame, text="Process", font=('Arial', 11, 'bold'),
                               bg=self.colors['primary'], fg=self.colors['text'], bd=0,
                               cursor='hand2', command=self.manual_process, padx=25, pady=8)
        process_btn.pack(side='right')
        
        # Quick Stats
        stats_frame = tk.Frame(manual_content, bg=self.colors['card_bg'])
        stats_frame.pack(fill='x', pady=20)
        
        # Get today's stats
        today = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute("SELECT COUNT(*) FROM attendance WHERE date=?", (today,))
        today_total = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute("SELECT COUNT(*) FROM attendance WHERE time_out IS NULL AND date=?", (today,))
        today_in = self.cursor.fetchone()[0] or 0
        
        stat_text = f"Today: {today_total} logs • {today_in} currently in"
        tk.Label(stats_frame, text=stat_text, font=('Arial', 10),
                bg=self.colors['card_bg'], fg=self.colors['text_dark']).pack()
        
        # Right Panel - Live Log
        right_frame = tk.LabelFrame(main_frame, text="  Live Activity Log  ", 
                                   font=('Arial', 12, 'bold'), bg=self.colors['card_bg'],
                                   fg=self.colors['text'], bd=1, relief='flat')
        right_frame.pack(side='right', fill='both', expand=True)
        
        log_container = tk.Frame(right_frame, bg=self.colors['card_bg'])
        log_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create text widget with scrollbar
        self.monitor_text = tk.Text(log_container, font=('Consolas', 10), 
                                   bg=self.colors['sidebar'], fg=self.colors['text'],
                                   bd=0, state='disabled')
        self.monitor_text.pack(side='left', fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(log_container, command=self.monitor_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.monitor_text.config(yscrollcommand=scrollbar.set)
        
        # Initial log message
        self.log_monitor("=== RFID Attendance System ===")
        self.log_monitor(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if self.is_monitoring:
            self.log_monitor(f"Scanner connected on {self.connected_port}")
        else:
            self.log_monitor("Scanner disconnected - Go to Settings to connect")
        self.log_monitor("-" * 40)
    
    def show_register(self):
        self.clear_content()
        
        tk.Label(self.content_frame, text="👤 Register User", font=('Arial', 28, 'bold'),
                bg=self.colors['bg'], fg=self.colors['text']).pack(anchor='w', pady=(0,20))
        
        # Main form frame
        form_frame = tk.Frame(self.content_frame, bg=self.colors['card_bg'], bd=0)
        form_frame.pack(fill='both', expand=True, pady=10)
        
        # Left side - Registration Form
        left_form = tk.Frame(form_frame, bg=self.colors['card_bg'])
        left_form.pack(side='left', fill='both', expand=True, padx=20, pady=20)
        
        # RFID Field
        tk.Label(left_form, text="RFID Card UID:", font=('Arial', 11, 'bold'),
                bg=self.colors['card_bg'], fg=self.colors['text']).pack(anchor='w', pady=(10,5))
        
        rfid_frame = tk.Frame(left_form, bg=self.colors['card_bg'])
        rfid_frame.pack(fill='x', pady=(0,15))
        
        self.rfid_entry = tk.Entry(rfid_frame, font=('Arial', 13), bd=0,
                                   bg=self.colors['sidebar'], fg=self.colors['text'],
                                   insertbackground=self.colors['text'])
        self.rfid_entry.pack(side='left', fill='x', expand=True, ipady=10, padx=(0,10))
        
        scan_btn = tk.Button(rfid_frame, text="🔍 Scan Card", font=('Arial', 11, 'bold'),
                            bg=self.colors['secondary'], fg=self.colors['text'], bd=0,
                            cursor='hand2', command=self.start_scan_for_register, padx=20, pady=10)
        scan_btn.pack(side='right')
        
        # Name Field
        tk.Label(left_form, text="Full Name:", font=('Arial', 11, 'bold'),
                bg=self.colors['card_bg'], fg=self.colors['text']).pack(anchor='w', pady=(10,5))
        
        self.name_entry = tk.Entry(left_form, font=('Arial', 13), bd=0,
                                   bg=self.colors['sidebar'], fg=self.colors['text'],
                                   insertbackground=self.colors['text'])
        self.name_entry.pack(fill='x', ipady=10, pady=(0,15))
        
        # Department and Position
        dept_frame = tk.Frame(left_form, bg=self.colors['card_bg'])
        dept_frame.pack(fill='x', pady=(10,0))
        
        tk.Label(dept_frame, text="Department:", font=('Arial', 11, 'bold'),
                bg=self.colors['card_bg'], fg=self.colors['text']).pack(side='left', padx=(0,20))
        
        tk.Label(dept_frame, text="Position:", font=('Arial', 11, 'bold'),
                bg=self.colors['card_bg'], fg=self.colors['text']).pack(side='left')
        
        entry_frame = tk.Frame(left_form, bg=self.colors['card_bg'])
        entry_frame.pack(fill='x', pady=(5,15))
        
        self.dept_entry = tk.Entry(entry_frame, font=('Arial', 12), bd=0,
                                   bg=self.colors['sidebar'], fg=self.colors['text'],
                                   insertbackground=self.colors['text'])
        self.dept_entry.pack(side='left', fill='x', expand=True, ipady=8, padx=(0,10))
        
        self.position_entry = tk.Entry(entry_frame, font=('Arial', 12), bd=0,
                                       bg=self.colors['sidebar'], fg=self.colors['text'],
                                       insertbackground=self.colors['text'])
        self.position_entry.pack(side='right', fill='x', expand=True, ipady=8)
        
        # Buttons
        btn_frame = tk.Frame(left_form, bg=self.colors['card_bg'])
        btn_frame.pack(fill='x', pady=20)
        
        register_btn = tk.Button(btn_frame, text="✅ Register User", font=('Arial', 12, 'bold'),
                                bg=self.colors['success'], fg=self.colors['text'], bd=0,
                                cursor='hand2', command=self.register_user, padx=30, pady=12)
        register_btn.pack(side='left', padx=(0,10))
        
        clear_btn = tk.Button(btn_frame, text="🔄 Clear Form", font=('Arial', 12),
                             bg=self.colors['warning'], fg='#000', bd=0,
                             cursor='hand2', command=self.clear_register_form, padx=30, pady=12)
        clear_btn.pack(side='left')
        
        # Right side - Users List
        right_list = tk.Frame(form_frame, bg=self.colors['card_bg'])
        right_list.pack(side='right', fill='both', expand=True, padx=20, pady=20)
        
        tk.Label(right_list, text="Registered Users", font=('Arial', 14, 'bold'),
                bg=self.colors['card_bg'], fg=self.colors['text']).pack(anchor='w', pady=(0,10))
        
        # Treeview with scrollbar
        tree_container = tk.Frame(right_list, bg=self.colors['card_bg'])
        tree_container.pack(fill='both', expand=True)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Custom.Treeview", background=self.colors['sidebar'],
                       foreground=self.colors['text'], fieldbackground=self.colors['sidebar'],
                       borderwidth=0, font=('Arial', 10))
        style.configure("Custom.Treeview.Heading", background=self.colors['accent'],
                       foreground=self.colors['text'], borderwidth=0, font=('Arial', 10, 'bold'))
        
        self.users_tree = ttk.Treeview(tree_container, columns=('ID', 'Name', 'Department'), 
                                      show='headings', height=15, style="Custom.Treeview")
        
        self.users_tree.heading('ID', text='RFID UID')
        self.users_tree.heading('Name', text='Name')
        self.users_tree.heading('Department', text='Department')
        
        self.users_tree.column('ID', width=120)
        self.users_tree.column('Name', width=200)
        self.users_tree.column('Department', width=150)
        
        scrollbar = tk.Scrollbar(tree_container, command=self.users_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.users_tree.config(yscrollcommand=scrollbar.set)
        
        self.users_tree.pack(fill='both', expand=True)
        
        # Action buttons for user list
        action_frame = tk.Frame(right_list, bg=self.colors['card_bg'])
        action_frame.pack(fill='x', pady=(10,0))
        
        refresh_btn = tk.Button(action_frame, text="🔄 Refresh", font=('Arial', 10),
                               bg=self.colors['accent'], fg=self.colors['text'], bd=0,
                               cursor='hand2', command=self.refresh_users_list, padx=15, pady=8)
        refresh_btn.pack(side='left', padx=2)
        
        edit_btn = tk.Button(action_frame, text="✏️ Edit", font=('Arial', 10),
                            bg=self.colors['info'], fg=self.colors['text'], bd=0,
                            cursor='hand2', command=self.edit_user, padx=15, pady=8)
        edit_btn.pack(side='left', padx=2)
        
        delete_btn = tk.Button(action_frame, text="🗑️ Delete", font=('Arial', 10),
                              bg=self.colors['danger'], fg=self.colors['text'], bd=0,
                              cursor='hand2', command=self.delete_user, padx=15, pady=8)
        delete_btn.pack(side='left', padx=2)
        
        self.refresh_users_list()
    
    def show_records(self):
        self.clear_content()
        
        tk.Label(self.content_frame, text="📋 Attendance Log", font=('Arial', 28, 'bold'),
                bg=self.colors['bg'], fg=self.colors['text']).pack(anchor='w', pady=(0,20))
        
        # Filter controls
        filter_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        filter_frame.pack(fill='x', pady=(0,15))
        
        tk.Label(filter_frame, text="Filter by Date:", font=('Arial', 11),
                bg=self.colors['bg'], fg=self.colors['text']).pack(side='left', padx=(0,10))
        
        self.filter_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_entry = tk.Entry(filter_frame, textvariable=self.filter_date_var, font=('Arial', 11),
                             bg=self.colors['sidebar'], fg=self.colors['text'], bd=0, width=12)
        date_entry.pack(side='left', padx=(0,10))
        
        filter_btn = tk.Button(filter_frame, text="🔍 Apply Filter", font=('Arial', 10),
                              bg=self.colors['accent'], fg=self.colors['text'], bd=0,
                              cursor='hand2', command=self.filter_records, padx=15, pady=6)
        filter_btn.pack(side='left', padx=(0,10))
        
        show_all_btn = tk.Button(filter_frame, text="📋 Show All", font=('Arial', 10),
                                bg=self.colors['info'], fg=self.colors['text'], bd=0,
                                cursor='hand2', command=self.refresh_records, padx=15, pady=6)
        show_all_btn.pack(side='left', padx=(0,10))
        
        # Main records frame
        records_frame = tk.Frame(self.content_frame, bg=self.colors['card_bg'], bd=0)
        records_frame.pack(fill='both', expand=True, pady=10)
        
        # Toolbar
        toolbar = tk.Frame(records_frame, bg=self.colors['card_bg'])
        toolbar.pack(fill='x', padx=20, pady=(15,10))
        
        export_btn = tk.Button(toolbar, text="📊 Export to Excel", font=('Arial', 11, 'bold'),
                              bg=self.colors['success'], fg=self.colors['text'], bd=0,
                              cursor='hand2', command=self.export_to_excel, padx=20, pady=8)
        export_btn.pack(side='left', padx=(0,10))
        
        print_btn = tk.Button(toolbar, text="🖨️ Print Report", font=('Arial', 11),
                             bg=self.colors['warning'], fg='#000', bd=0,
                             cursor='hand2', command=self.print_report, padx=20, pady=8)
        print_btn.pack(side='left')
        
        # Treeview for records
        tree_container = tk.Frame(records_frame, bg=self.colors['card_bg'])
        tree_container.pack(fill='both', expand=True, padx=20, pady=(0,20))
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Records.Treeview", background=self.colors['sidebar'],
                       foreground=self.colors['text'], fieldbackground=self.colors['sidebar'],
                       borderwidth=0, font=('Arial', 10))
        style.configure("Records.Treeview.Heading", background=self.colors['accent'],
                       foreground=self.colors['text'], borderwidth=0, font=('Arial', 10, 'bold'))
        
        self.records_tree = ttk.Treeview(tree_container, 
                                        columns=('ID', 'Name', 'Date', 'Time In', 'Time Out', 'Status'),
                                        show='headings', height=20, style="Records.Treeview")
        
        self.records_tree.heading('ID', text='ID')
        self.records_tree.heading('Name', text='Name')
        self.records_tree.heading('Date', text='Date')
        self.records_tree.heading('Time In', text='Time In')
        self.records_tree.heading('Time Out', text='Time Out')
        self.records_tree.heading('Status', text='Status')
        
        self.records_tree.column('ID', width=50)
        self.records_tree.column('Name', width=150)
        self.records_tree.column('Date', width=100)
        self.records_tree.column('Time In', width=100)
        self.records_tree.column('Time Out', width=100)
        self.records_tree.column('Status', width=80)
        
        scrollbar = tk.Scrollbar(tree_container, command=self.records_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.records_tree.config(yscrollcommand=scrollbar.set)
        
        self.records_tree.pack(fill='both', expand=True)
        
        self.refresh_records()
    
    def show_reports(self):
        self.clear_content()
        
        tk.Label(self.content_frame, text="📈 Reports & Analytics", font=('Arial', 28, 'bold'),
                bg=self.colors['bg'], fg=self.colors['text']).pack(anchor='w', pady=(0,20))
        
        # Placeholder for reports functionality
        placeholder = tk.Label(self.content_frame, 
                              text="📊 Reports Dashboard\n\nMonthly attendance reports,\nstatistics, and analytics\nwill appear here.",
                              font=('Arial', 24), bg=self.colors['bg'], fg=self.colors['text_dark'],
                              justify='center')
        placeholder.pack(expand=True)
    
    def show_settings(self):
        self.clear_content()
        
        tk.Label(self.content_frame, text="⚙️ Settings", font=('Arial', 28, 'bold'),
                bg=self.colors['bg'], fg=self.colors['text']).pack(anchor='w', pady=(0,20))
        
        # Connection Settings Card
        conn_card = tk.LabelFrame(self.content_frame, text="  Scanner Connection  ", 
                                 font=('Arial', 14, 'bold'), bg=self.colors['card_bg'],
                                 fg=self.colors['text'], bd=1, relief='flat')
        conn_card.pack(fill='x', pady=10, ipady=10)
        
        conn_content = tk.Frame(conn_card, bg=self.colors['card_bg'])
        conn_content.pack(padx=20, pady=15)
        
        # Auto-detect section
        tk.Label(conn_content, text="Automatic Port Detection:", font=('Arial', 11, 'bold'),
                bg=self.colors['card_bg'], fg=self.colors['text']).grid(row=0, column=0, sticky='w', pady=(0,10))
        
        # Port selection
        tk.Label(conn_content, text="Available COM Ports:", font=('Arial', 11),
                bg=self.colors['card_bg'], fg=self.colors['text']).grid(row=1, column=0, sticky='w', pady=(0,5))
        
        port_frame = tk.Frame(conn_content, bg=self.colors['card_bg'])
        port_frame.grid(row=2, column=0, sticky='ew', pady=(0,15))
        
        self.port_combo = ttk.Combobox(port_frame, font=('Arial', 11), state='readonly')
        self.port_combo.pack(side='left', fill='x', expand=True, ipady=8, padx=(0,10))
        
        refresh_ports_btn = tk.Button(port_frame, text="🔄 Refresh Ports", font=('Arial', 10),
                                     bg=self.colors['accent'], fg=self.colors['text'], bd=0,
                                     cursor='hand2', command=self.auto_detect_ports, padx=15, pady=8)
        refresh_ports_btn.pack(side='right')
        
        # Connection buttons
        btn_frame = tk.Frame(conn_content, bg=self.colors['card_bg'])
        btn_frame.grid(row=3, column=0, sticky='ew', pady=(10,0))
        
        self.connect_btn = tk.Button(btn_frame, text="🔗 Connect Scanner", font=('Arial', 11, 'bold'),
                                     bg=self.colors['success'], fg=self.colors['text'], bd=0,
                                     cursor='hand2', command=self.connect_arduino, padx=25, pady=10)
        self.connect_btn.pack(side='left', padx=(0,10))
        
        self.disconnect_btn = tk.Button(btn_frame, text="🔌 Disconnect", font=('Arial', 11),
                                       bg=self.colors['danger'], fg=self.colors['text'], bd=0,
                                       cursor='hand2', command=self.disconnect_arduino, 
                                       padx=25, pady=10, state='disabled')
        self.disconnect_btn.pack(side='left')
        
        # Status indicator
        self.settings_status = tk.Label(conn_content, text="Status: Not Connected", font=('Arial', 11),
                                       bg=self.colors['card_bg'], fg=self.colors['text_dark'])
        self.settings_status.grid(row=4, column=0, sticky='w', pady=(15,0))
        
        # Test connection button
        test_btn = tk.Button(conn_content, text="🔍 Test Connection", font=('Arial', 10),
                            bg=self.colors['info'], fg=self.colors['text'], bd=0,
                            cursor='hand2', command=self.test_connection, padx=15, pady=6)
        test_btn.grid(row=4, column=0, sticky='e', pady=(15,0))
        
        # Database Settings Card
        db_card = tk.LabelFrame(self.content_frame, text="  Database Management  ", 
                               font=('Arial', 14, 'bold'), bg=self.colors['card_bg'],
                               fg=self.colors['text'], bd=1, relief='flat')
        db_card.pack(fill='x', pady=20, ipady=10)
        
        db_content = tk.Frame(db_card, bg=self.colors['card_bg'])
        db_content.pack(padx=20, pady=15)
        
        tk.Label(db_content, text="Database Operations:", font=('Arial', 11, 'bold'),
                bg=self.colors['card_bg'], fg=self.colors['text']).grid(row=0, column=0, sticky='w', pady=(0,10))
        
        # Database buttons
        db_btn_frame = tk.Frame(db_content, bg=self.colors['card_bg'])
        db_btn_frame.grid(row=1, column=0, columnspan=2, sticky='ew')
        
        backup_btn = tk.Button(db_btn_frame, text="💾 Backup Database", font=('Arial', 10),
                              bg=self.colors['accent'], fg=self.colors['text'], bd=0,
                              cursor='hand2', command=self.backup_database, padx=15, pady=8)
        backup_btn.pack(side='left', padx=5)
        
        clear_logs_btn = tk.Button(db_btn_frame, text="🗑️ Clear Old Logs", font=('Arial', 10),
                                  bg=self.colors['warning'], fg='#000', bd=0,
                                  cursor='hand2', command=self.clear_old_logs, padx=15, pady=8)
        clear_logs_btn.pack(side='left', padx=5)
        
        reset_btn = tk.Button(db_btn_frame, text="⚠️ Reset Database", font=('Arial', 10),
                             bg=self.colors['danger'], fg=self.colors['text'], bd=0,
                             cursor='hand2', command=self.reset_database, padx=15, pady=8)
        reset_btn.pack(side='left', padx=5)
        
        # Initialize port detection
        self.auto_detect_ports()
    
    def start_scan_for_register(self):
        if not self.serial_port:
            messagebox.showwarning("Scanner Not Connected", 
                                 "Please connect the RFID scanner first in Settings!")
            return
        
        self.scanning_for_register = True
        self.rfid_entry.delete(0, 'end')
        self.rfid_entry.insert(0, "Scanning... Tap your card")
        self.rfid_entry.config(state='disabled', fg=self.colors['warning'])
        
        messagebox.showinfo("Scan Card", 
                          "Ready to scan!\n\nPlease tap your RFID card on the scanner.\n\nThe UID will automatically appear in the field.")
    
    def clear_register_form(self):
        self.rfid_entry.config(state='normal', fg=self.colors['text'])
        self.rfid_entry.delete(0, 'end')
        self.name_entry.delete(0, 'end')
        self.dept_entry.delete(0, 'end')
        self.position_entry.delete(0, 'end')
    
    def edit_user(self):
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a user to edit!")
            return
        
        item = self.users_tree.item(selected[0])
        rfid, name, dept = item['values']
        
        self.rfid_entry.config(state='normal')
        self.rfid_entry.delete(0, 'end')
        self.rfid_entry.insert(0, rfid if rfid != "N/A" else "")
        self.name_entry.delete(0, 'end')
        self.name_entry.insert(0, name)
        self.dept_entry.delete(0, 'end')
        self.dept_entry.insert(0, dept)
        
        # Position is not in the treeview, so leave it empty
        self.position_entry.delete(0, 'end')
        
        # Delete the old record
        self.cursor.execute("DELETE FROM users WHERE rfid_uid=? OR name=?", 
                          (rfid if rfid != "N/A" else None, name))
        self.conn.commit()
        self.refresh_users_list()
        
        messagebox.showinfo("Edit Mode", "User loaded for editing. Make changes and click 'Register User' to save.")
    
    def connect_arduino(self):
        if self.is_monitoring:
            messagebox.showinfo("Already Connected", "Scanner is already connected!")
            return
        
        selected_port = self.port_combo.get()
        if not selected_port:
            messagebox.showwarning("No Port Selected", "Please select a COM port!")
            return
        
        # Extract just the port name (before the dash)
        port_name = selected_port.split(' - ')[0].strip()
        
        try:
            self.serial_port = serial.Serial(port_name, 9600, timeout=1)
            time.sleep(2)  # Wait for connection to stabilize
            
            self.is_monitoring = True
            self.connected_port = port_name
            
            # Update UI
            self.connection_status.config(text="🟢 Connected", fg=self.colors['success'])
            self.settings_status.config(text=f"Status: Connected to {port_name}", fg=self.colors['success'])
            self.connect_btn.config(state='disabled')
            self.disconnect_btn.config(state='normal')
            
            # Start monitoring thread
            thread = threading.Thread(target=self.read_rfid, daemon=True)
            thread.start()
            
            self.log_monitor(f"✓ Scanner connected on {port_name}")
            messagebox.showinfo("Connected!", f"Successfully connected to scanner on {port_name}")
            
        except Exception as e:
            messagebox.showerror("Connection Failed", f"Failed to connect to {port_name}:\n{str(e)}")
            self.log_monitor(f"✗ Connection failed: {str(e)}")
            self.disconnect_arduino()
    
    def disconnect_arduino(self):
        self.is_monitoring = False
        if self.serial_port:
            try:
                self.serial_port.close()
            except:
                pass
            self.serial_port = None
        
        # Update UI
        self.connection_status.config(text="🔴 Disconnected", fg=self.colors['danger'])
        self.settings_status.config(text="Status: Not Connected", fg=self.colors['text_dark'])
        self.connect_btn.config(state='normal')
        self.disconnect_btn.config(state='disabled')
        
        self.log_monitor("Scanner disconnected")
        
        if hasattr(self, 'scanning_for_register') and self.scanning_for_register:
            self.scanning_for_register = False
            if hasattr(self, 'rfid_entry'):
                self.rfid_entry.config(state='normal', fg=self.colors['text'])
                self.rfid_entry.delete(0, 'end')
    
    def test_connection(self):
        if not self.serial_port:
            messagebox.showwarning("Not Connected", "Please connect the scanner first!")
            return
        
        try:
            # Send a test command
            self.serial_port.write(b'TEST\n')
            time.sleep(0.1)
            
            if self.serial_port.in_waiting:
                response = self.serial_port.readline().decode('utf-8').strip()
                messagebox.showinfo("Test Successful", 
                                  f"Scanner is responding!\n\nResponse: {response}")
            else:
                messagebox.showinfo("Test Complete", 
                                  "Scanner is connected but not responding.\nThis may be normal for some devices.")
        except Exception as e:
            messagebox.showerror("Test Failed", f"Error testing connection:\n{str(e)}")
    
    def read_rfid(self):
        while self.is_monitoring and self.serial_port:
            try:
                if self.serial_port.in_waiting:
                    data = self.serial_port.readline().decode('utf-8').strip()
                    if data:
                        # Clean the data
                        data = data.replace('\x00', '').replace('\r', '').replace('\n', '').strip()
                        
                        if data and len(data) > 0:
                            if self.scanning_for_register:
                                # Handle registration scan
                                self.root.after(0, self.handle_register_scan, data.upper())
                            else:
                                # Handle attendance scan
                                self.root.after(0, self.process_rfid, data.upper())
            except Exception as e:
                self.log_monitor(f"Error reading scanner: {str(e)}")
                if "device disconnected" in str(e).lower() or "access denied" in str(e).lower():
                    self.root.after(0, self.disconnect_arduino)
                time.sleep(1)
    
    def handle_register_scan(self, rfid_data):
        """Handle RFID scan during registration"""
        self.scanning_for_register = False
        self.rfid_entry.config(state='normal', fg=self.colors['text'])
        self.rfid_entry.delete(0, 'end')
        self.rfid_entry.insert(0, rfid_data.upper())
        self.log_monitor(f"Card scanned for registration: {rfid_data.upper()}")
        
        # Auto-focus to name field
        self.name_entry.focus_set()
    
    def manual_process(self):
        rfid_uid = self.manual_rfid_entry.get().strip().upper()
        if not rfid_uid:
            messagebox.showwarning("No UID", "Please enter an RFID UID!")
            return
        
        self.process_rfid(rfid_uid)
        self.manual_rfid_entry.delete(0, 'end')
    
    def process_rfid(self, rfid_uid):
        """Process RFID scan for attendance"""
        self.cursor.execute("SELECT name FROM users WHERE rfid_uid=?", (rfid_uid,))
        result = self.cursor.fetchone()
        
        if result:
            name = result[0]
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            
            # Check last attendance
            self.cursor.execute("""
                SELECT id, time_out FROM attendance 
                WHERE rfid_uid=? AND date=? 
                ORDER BY id DESC LIMIT 1
            """, (rfid_uid, date_str))
            
            attendance = self.cursor.fetchone()
            
            if attendance and not attendance[1]:
                # Time Out
                self.cursor.execute("UPDATE attendance SET time_out=? WHERE id=?", 
                                  (time_str, attendance[0]))
                status = "🔴 TIME OUT"
                color = "red"
            else:
                # Time In
                self.cursor.execute("""
                    INSERT INTO attendance (rfid_uid, name, time_in, date)
                    VALUES (?, ?, ?, ?)
                """, (rfid_uid, name, time_str, date_str))
                status = "🟢 TIME IN"
                color = "green"
            
            self.conn.commit()
            self.log_monitor(f"{status}: {name} at {time_str}")
            
            # Refresh dashboard if active
            if hasattr(self, 'activity_text'):
                self.load_recent_activity()
                
        else:
            self.log_monitor(f"✗ Unknown RFID: {rfid_uid}")
            # Show notification
            self.root.after(0, lambda: messagebox.showwarning("Unknown Card", 
                f"RFID UID: {rfid_uid}\n\nThis card is not registered in the system.\nPlease register the user first."))
    
    def log_monitor(self, message):
        """Add message to monitor log"""
        try:
            if hasattr(self, 'monitor_text'):
                self.monitor_text.config(state='normal')
                timestamp = datetime.now().strftime('%H:%M:%S')
                self.monitor_text.insert('end', f"[{timestamp}] {message}\n")
                self.monitor_text.see('end')
                self.monitor_text.config(state='disabled')
        except:
            pass
    
    def register_user(self):
        rfid = self.rfid_entry.get().strip().upper() if self.rfid_entry.get().strip() else None
        name = self.name_entry.get().strip()
        dept = self.dept_entry.get().strip()
        position = self.position_entry.get().strip()
        
        if not name:
            messagebox.showwarning("Missing Information", "Name is required!")
            return
        
        try:
            self.cursor.execute("""
                INSERT INTO users (rfid_uid, name, department, position, registered_date)
                VALUES (?, ?, ?, ?, ?)
            """, (rfid, name, dept, position, datetime.now().strftime("%Y-%m-%d")))
            self.conn.commit()
            
            messagebox.showinfo("Success", f"✅ User '{name}' registered successfully!")
            self.log_monitor(f"✓ New user registered: {name}")
            self.clear_register_form()
            self.refresh_users_list()
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate Entry", 
                               "This RFID UID is already registered!\nPlease use a different card or edit the existing user.")
    
    def delete_user(self):
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a user to delete!")
            return
        
        item = self.users_tree.item(selected[0])
        name = item['values'][1]
        rfid = item['values'][0]
        
        confirm = messagebox.askyesno("Confirm Deletion", 
                                     f"Are you sure you want to delete user:\n\n{name}\n\nThis will also remove their attendance records!")
        
        if confirm:
            try:
                # Delete user and their attendance records
                self.cursor.execute("DELETE FROM users WHERE rfid_uid=? OR name=?", 
                                  (rfid if rfid != "N/A" else None, name))
                self.cursor.execute("DELETE FROM attendance WHERE rfid_uid=?", (rfid if rfid != "N/A" else None,))
                self.conn.commit()
                
                self.refresh_users_list()
                self.log_monitor(f"🗑️ User deleted: {name}")
                messagebox.showinfo("Deleted", f"User '{name}' has been deleted.")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete user:\n{str(e)}")
    
    def refresh_users_list(self):
        if not hasattr(self, 'users_tree'):
            return
            
        # Clear existing items
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        # Fetch and display users
        self.cursor.execute("SELECT rfid_uid, name, department FROM users ORDER BY name")
        for row in self.cursor.fetchall():
            rfid = row[0] if row[0] else "N/A"
            self.users_tree.insert('', 'end', values=(rfid, row[1], row[2]))
    
    def refresh_records(self):
        if not hasattr(self, 'records_tree'):
            return
            
        # Clear existing items
        for item in self.records_tree.get_children():
            self.records_tree.delete(item)
        
        # Fetch and display all records
        self.cursor.execute("""
            SELECT id, name, date, time_in, time_out, status 
            FROM attendance 
            ORDER BY date DESC, time_in DESC
        """)
        
        for row in self.cursor.fetchall():
            self.records_tree.insert('', 'end', values=row)
    
    def filter_records(self):
        """Filter records by date"""
        if not hasattr(self, 'records_tree'):
            return
            
        date_filter = self.filter_date_var.get()
        
        # Clear existing items
        for item in self.records_tree.get_children():
            self.records_tree.delete(item)
        
        # Fetch filtered records
        self.cursor.execute("""
            SELECT id, name, date, time_in, time_out, status 
            FROM attendance 
            WHERE date = ?
            ORDER BY time_in DESC
        """, (date_filter,))
        
        count = 0
        for row in self.cursor.fetchall():
            self.records_tree.insert('', 'end', values=row)
            count += 1
        
        # Update status
        self.log_monitor(f"Filtered records for {date_filter}: {count} entries")
    
    def export_to_excel(self):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")],
                initialfile=f"attendance_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            )
            
            if not file_path:
                return
            
            # Get all records
            self.cursor.execute("SELECT name, date, time_in, time_out, status FROM attendance ORDER BY date, time_in")
            data = self.cursor.fetchall()
            
            if not data:
                messagebox.showwarning("No Data", "There are no records to export!")
                return
            
            # Create DataFrame
            df = pd.DataFrame(data, columns=['Name', 'Date', 'Time In', 'Time Out', 'Status'])
            
            # Export based on file extension
            if file_path.endswith('.csv'):
                df.to_csv(file_path, index=False, encoding='utf-8')
            else:
                df.to_excel(file_path, index=False, sheet_name='Attendance')
            
            self.log_monitor(f"✓ Exported {len(data)} records to {file_path}")
            messagebox.showinfo("Export Successful", 
                              f"Successfully exported {len(data)} records!\n\nSaved to:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Export Failed", f"Error exporting data:\n{str(e)}")
            self.log_monitor(f"✗ Export failed: {str(e)}")
    
    def print_report(self):
        """Print attendance report"""
        messagebox.showinfo("Print Report", 
                          "Print functionality will be implemented here.\n\nFor now, please use the Export to Excel feature.")
    
    def backup_database(self):
        """Create a backup of the database"""
        try:
            backup_path = filedialog.asksaveasfilename(
                defaultextension=".db",
                filetypes=[("Database files", "*.db"), ("All files", "*.*")],
                initialfile=f"attendance_backup_{datetime.now().strftime('%Y%m%d')}.db"
            )
            
            if backup_path:
                # Simple file copy for backup
                import shutil
                shutil.copy2('attendance.db', backup_path)
                
                messagebox.showinfo("Backup Successful", 
                                  f"Database backed up to:\n{backup_path}")
                self.log_monitor("Database backup created")
                
        except Exception as e:
            messagebox.showerror("Backup Failed", f"Error creating backup:\n{str(e)}")
    
    def clear_old_logs(self):
        """Clear attendance logs older than 30 days"""
        confirm = messagebox.askyesno("Clear Old Logs", 
                                     "This will delete all attendance logs older than 30 days.\n\nContinue?")
        
        if confirm:
            try:
                # Calculate date 30 days ago
                thirty_days_ago = (datetime.now() - pd.Timedelta(days=30)).strftime("%Y-%m-%d")
                
                self.cursor.execute("DELETE FROM attendance WHERE date < ?", (thirty_days_ago,))
                deleted_count = self.cursor.rowcount
                self.conn.commit()
                
                messagebox.showinfo("Logs Cleared", 
                                  f"Deleted {deleted_count} old attendance records.")
                self.log_monitor(f"Cleared {deleted_count} old logs")
                
                if hasattr(self, 'records_tree'):
                    self.refresh_records()
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear logs:\n{str(e)}")
    
    def reset_database(self):
        """Reset the entire database (DANGEROUS!)"""
        confirm = messagebox.askyesno("DANGER: Reset Database", 
                                     "⚠️ WARNING: This will DELETE ALL DATA!\n\n"
                                     "This action cannot be undone!\n\n"
                                     "Are you absolutely sure?")
        
        if confirm:
            try:
                # Double confirmation
                confirm2 = messagebox.askyesno("FINAL CONFIRMATION", 
                                              "THIS WILL DELETE ALL USERS AND ATTENDANCE RECORDS!\n\n"
                                              "Type 'YES' to confirm:")
                
                if confirm2:
                    # Drop and recreate tables
                    self.cursor.execute("DROP TABLE IF EXISTS users")
                    self.cursor.execute("DROP TABLE IF EXISTS attendance")
                    self.conn.commit()
                    
                    # Recreate tables
                    self.setup_database()
                    
                    # Refresh UI
                    if hasattr(self, 'users_tree'):
                        self.refresh_users_list()
                    if hasattr(self, 'records_tree'):
                        self.refresh_records()
                    
                    messagebox.showinfo("Database Reset", "Database has been reset to empty state.")
                    self.log_monitor("Database reset - ALL DATA DELETED")
                    
            except Exception as e:
                messagebox.showerror("Reset Failed", f"Error resetting database:\n{str(e)}")
    
    def on_closing(self):
        """Cleanup on window close"""
        if self.serial_port:
            self.disconnect_arduino()
        
        if hasattr(self, 'conn'):
            self.conn.close()
        
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernAttendanceSystem(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()