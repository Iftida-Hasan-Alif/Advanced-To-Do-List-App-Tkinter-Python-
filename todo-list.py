import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum
import csv

# Try optional tkcalendar for date picking; fall back to text entry
try:
    from tkcalendar import DateEntry
    TKCALENDAR_AVAILABLE = True
except Exception:
    TKCALENDAR_AVAILABLE = False

# ----------------------------
# Models and Data Management
# ----------------------------
class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Status(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"

class Theme:
    """Theme colors for dark and light themes"""
    DARK = {
        'primary': '#6366f1',      # Purple accent color
        'primary_dark': '#4338ca',
        'secondary': '#4b5563',
        'accent': '#10b981',
        'danger': '#ef4444',
        'warning': '#f59e0b',
        'dark_text': '#f8fafc',
        'background': '#1f2937',
        'muted': '#9ca3af',
        'card': '#374151',
        'sidebar_bg': '#111827',
        'sidebar_card': '#1f2937',
        'sidebar_text': '#ffffff',
        'input': '#374151',
        'white': '#ffffff'
    }
    LIGHT = {
        'primary': '#4f46e5',
        'primary_dark': '#3730a3',
        'secondary': '#6b7280',
        'accent': '#10b981',
        'danger': '#dc2626',
        'warning': '#b45309',
        'dark_text': '#111827',
        'background': '#f8fafc',
        'muted': '#6b7280',
        'card': '#ffffff',
        'sidebar_bg': '#e6eef8',
        'sidebar_card': '#ffffff',
        'sidebar_text': '#111827',
        'input': '#ffffff',
        'white': '#ffffff'
    }

    FONTS = {
        'title': ('Arial', 16, 'bold'),
        'heading': ('Arial', 14, 'bold'),
        'body': ('Arial', 11),
        'small': ('Arial', 10)
    }

class Task:
    def __init__(self, id: int, description: str, priority: Priority = Priority.MEDIUM,
                 due_date: Optional[str] = None, category: str = "general"):
        self.id = id
        self.description = description
        self.priority = priority
        self.status = Status.PENDING
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.due_date = due_date  # ISO date 'YYYY-MM-DD' or None
        self.category = category
        self.completed_at = None

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'description': self.description,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_at': self.created_at,
            'due_date': self.due_date,
            'category': self.category,
            'completed_at': self.completed_at
        }

    @classmethod
    def from_dict(cls, data: Dict):
        task = cls(
            id=data['id'],
            description=data['description'],
            priority=Priority(data.get('priority', 'medium')),
            due_date=data.get('due_date'),
            category=data.get('category', 'general')
        )
        task.status = Status(data.get('status', 'pending'))
        task.created_at = data.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        task.completed_at = data.get('completed_at')
        return task

class TodoList:
    def __init__(self, filename: str = "todo_data.json"):
        self.filename = filename
        self.tasks: List[Task] = []
        self.next_id = 1
        self.load_tasks()

    def load_tasks(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    self.tasks = [Task.from_dict(td) for td in data.get('tasks', [])]
                    if self.tasks:
                        self.next_id = max(t.id for t in self.tasks) + 1
                    else:
                        self.next_id = 1
            except (json.JSONDecodeError, KeyError):
                self.tasks = []
                self.next_id = 1

    def save_tasks(self):
        data = {
            'tasks': [t.to_dict() for t in self.tasks],
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(self.filename, 'w') as f:
            json.dump(data, f, indent=2)

    def add_task(self, description: str, priority: Priority = Priority.MEDIUM,
                 due_date: Optional[str] = None, category: str = "general") -> Task:
        task = Task(self.next_id, description, priority, due_date, category)
        self.tasks.append(task)
        self.next_id += 1
        self.save_tasks()
        return task

    def remove_task(self, task_id: int) -> bool:
        for i, t in enumerate(self.tasks):
            if t.id == task_id:
                self.tasks.pop(i)
                self.save_tasks()
                return True
        return False

    def complete_task(self, task_id: int) -> bool:
        for t in self.tasks:
            if t.id == task_id:
                t.status = Status.COMPLETED
                t.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.save_tasks()
                return True
        return False

    def update_task_status(self, task_id: int, status: Status) -> bool:
        for t in self.tasks:
            if t.id == task_id:
                t.status = status
                if status == Status.COMPLETED:
                    t.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    t.completed_at = None
                self.save_tasks()
                return True
        return False

    def update_task(self, task_id: int, description: str = None, priority: Priority = None,
                    due_date: str = None, category: str = None) -> bool:
        for t in self.tasks:
            if t.id == task_id:
                if description is not None:
                    t.description = description
                if priority is not None:
                    t.priority = priority
                if due_date is not None:
                    t.due_date = due_date
                if category is not None:
                    t.category = category
                self.save_tasks()
                return True
        return False

    def get_tasks(self, status: Optional[Status] = None, category: Optional[str] = None,
                  priority: Optional[Priority] = None) -> List[Task]:
        filtered = self.tasks
        if status:
            filtered = [t for t in filtered if t.status == status]
        if category:
            filtered = [t for t in filtered if t.category == category]
        if priority:
            filtered = [t for t in filtered if t.priority == priority]
        return filtered

    def get_task(self, task_id: int) -> Optional[Task]:
        for t in self.tasks:
            if t.id == task_id:
                return t
        return None

    def get_statistics(self) -> Dict:
        total = len(self.tasks)
        completed = len([t for t in self.tasks if t.status == Status.COMPLETED])
        pending = len([t for t in self.tasks if t.status == Status.PENDING])
        in_progress = len([t for t in self.tasks if t.status == Status.IN_PROGRESS])
        return {
            'total': total,
            'completed': completed,
            'pending': pending,
            'in_progress': in_progress,
            'completion_rate': (completed / total * 100) if total else 0
        }

# ----------------------------
# GUI Application
# ----------------------------
class TodoApp:
    def __init__(self, root):
        self.root = root
        self.todo_list = TodoList()
        self.theme_mode = 'dark'  # default
        self.theme = Theme.DARK if self.theme_mode == 'dark' else Theme.LIGHT
        self.setup_window()
        self.create_widgets()
        self.refresh_task_list()
        self.update_statistics()

    def setup_window(self):
        self.root.title("To-Do - APP (Enhanced)")
        self.root.geometry("1024x720")
        self.root.minsize(900, 600)
        self.root.configure(bg=Theme.DARK['background'])
        try:
            self.root.eval('tk::PlaceWindow . center')
        except Exception:
            pass  # Not critical

    def create_widgets(self):
        self.root.config(bg=self.theme['background'])
        main_frame = tk.Frame(self.root, bg=self.theme['background'], padx=16, pady=16)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = tk.Frame(main_frame, bg=self.theme['background'])
        header_frame.pack(fill=tk.X, pady=(0, 12))
        title = tk.Label(header_frame, text="📝  To-Do List", font=Theme.FONTS['title'],
                         fg=self.theme['dark_text'], bg=self.theme['background'])
        title.pack(side=tk.LEFT)

        # Controls at top-right: Search, Sort, Theme toggle, Export
        control_frame = tk.Frame(header_frame, bg=self.theme['background'])
        control_frame.pack(side=tk.RIGHT)

        # Search
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(control_frame, textvariable=self.search_var, font=Theme.FONTS['body'],
                                width=28, bg=self.theme['input'], fg=self.theme['dark_text'], relief=tk.FLAT,
                                insertbackground=self.theme['dark_text'])
        search_entry.pack(side=tk.LEFT, padx=(0, 8))
        search_entry.bind('<KeyRelease>', lambda e: self.refresh_task_list())

        # Sort combobox
        self.sort_var = tk.StringVar(value="Newest")
        sort_combo = ttk.Combobox(control_frame, textvariable=self.sort_var,
                                  values=["Newest", "Oldest", "Priority (High→Low)", "Due Date (Soon→Later)"],
                                  state="readonly", width=24)
        sort_combo.pack(side=tk.LEFT, padx=(0, 8))
        sort_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_task_list())

        # Theme toggle
        theme_btn = tk.Button(control_frame, text="Toggle Theme", command=self.toggle_theme,
                              bg=self.theme['primary'], fg=self.theme['dark_text'], relief=tk.FLAT, padx=8)
        theme_btn.pack(side=tk.LEFT, padx=(0, 8))

        # Export CSV
        export_btn = tk.Button(control_frame, text="Export CSV", command=self.export_csv,
                               bg=self.theme['secondary'], fg=self.theme['dark_text'], relief=tk.FLAT, padx=8)
        export_btn.pack(side=tk.LEFT)

        # Two-column layout
        content_frame = tk.Frame(main_frame, bg=self.theme['background'])
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        # Left sidebar (add + filters)
        left_frame = tk.Frame(content_frame, bg=self.theme['sidebar_bg'], width=320)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 16))
        left_frame.pack_propagate(False)

        # Add Task Card
        add_card = self.create_card(left_frame)
        add_card.configure(bg=self.theme['sidebar_card'])
        add_card.pack(fill=tk.X, pady=(0, 12))

        tk.Label(add_card, text="Add New Task", font=Theme.FONTS['heading'],
                 fg=self.theme['sidebar_text'], bg=self.theme['sidebar_card']).pack(anchor=tk.W, pady=(0, 10))
        tk.Label(add_card, text="Description:", font=Theme.FONTS['body'],
                 fg=self.theme['sidebar_text'], bg=self.theme['sidebar_card']).pack(anchor=tk.W)

        self.task_entry = tk.Entry(add_card, font=Theme.FONTS['body'],
                                   bg=self.theme['input'], fg=self.theme['sidebar_text'],
                                   relief=tk.FLAT, insertbackground=self.theme['sidebar_text'])
        self.task_entry.pack(fill=tk.X, pady=(6, 10))
        self.task_entry.bind('<Return>', lambda e: self.add_task())

        # Priority + Category + Due Date
        row = tk.Frame(add_card, bg=self.theme['sidebar_card'])
        row.pack(fill=tk.X, pady=(0, 8))
        tk.Label(row, text="Priority:", fg=self.theme['sidebar_text'], bg=self.theme['sidebar_card']).pack(side=tk.LEFT)
        self.priority_var = tk.StringVar(value="medium")
        pcombo = ttk.Combobox(row, textvariable=self.priority_var, values=["low", "medium", "high"], width=8, state="readonly")
        pcombo.pack(side=tk.LEFT, padx=(6, 12))

        tk.Label(row, text="Category:", fg=self.theme['sidebar_text'], bg=self.theme['sidebar_card']).pack(side=tk.LEFT)
        self.category_var = tk.StringVar(value="general")
        ccombo = ttk.Combobox(row, textvariable=self.category_var, values=["general", "work", "personal", "shopping", "health"], width=12, state="readonly")
        ccombo.pack(side=tk.LEFT, padx=(6, 0))

        # Due date
        tk.Label(add_card, text="Due Date (optional):", fg=self.theme['sidebar_text'], bg=self.theme['sidebar_card']).pack(anchor=tk.W, pady=(6, 4))
        if TKCALENDAR_AVAILABLE:
            self.due_picker = DateEntry(add_card, date_pattern='yyyy-mm-dd')
            self.due_picker.pack(fill=tk.X)
        else:
            # fallback simple entry
            self.due_picker = tk.Entry(add_card, font=Theme.FONTS['body'],
                                       bg=self.theme['input'], fg=self.theme['sidebar_text'],
                                       relief=tk.FLAT, insertbackground=self.theme['sidebar_text'])
            self.due_picker.insert(0, "YYYY-MM-DD")
            self.due_picker.pack(fill=tk.X)

        add_btn = tk.Button(add_card, text="➕ Add Task", command=self.add_task,
                            bg=self.theme['primary'], fg=self.theme['dark_text'], relief=tk.FLAT, pady=8)
        add_btn.pack(fill=tk.X, pady=(10, 0))

        # Filters card
        filters_card = self.create_card(left_frame)
        filters_card.configure(bg=self.theme['sidebar_card'])
        filters_card.pack(fill=tk.X, pady=(0, 12))

        tk.Label(filters_card, text="Filters", font=Theme.FONTS['heading'],
                 fg=self.theme['sidebar_text'], bg=self.theme['sidebar_card']).pack(anchor=tk.W, pady=(0, 10))

        self.status_var = tk.StringVar(value="all")
        sf = tk.Frame(filters_card, bg=self.theme['sidebar_card'])
        sf.pack(fill=tk.X)
        tk.Radiobutton(sf, text="All", variable=self.status_var, value="all", command=self.refresh_task_list,
                       bg=self.theme['sidebar_card'], fg=self.theme['sidebar_text'], selectcolor=self.theme['sidebar_card']).pack(anchor=tk.W)
        tk.Radiobutton(sf, text="Pending", variable=self.status_var, value="pending", command=self.refresh_task_list,
                       bg=self.theme['sidebar_card'], fg=self.theme['sidebar_text'], selectcolor=self.theme['sidebar_card']).pack(anchor=tk.W)
        tk.Radiobutton(sf, text="Completed", variable=self.status_var, value="completed", command=self.refresh_task_list,
                       bg=self.theme['sidebar_card'], fg=self.theme['sidebar_text'], selectcolor=self.theme['sidebar_card']).pack(anchor=tk.W)

        # Category filter dropdown
        tk.Label(filters_card, text="Category Filter:", fg=self.theme['sidebar_text'], bg=self.theme['sidebar_card']).pack(anchor=tk.W, pady=(8, 4))
        self.category_filter_var = tk.StringVar(value="all")
        categories = ["all", "general", "work", "personal", "shopping", "health"]
        cat_combo = ttk.Combobox(filters_card, textvariable=self.category_filter_var, values=categories, state="readonly")
        cat_combo.pack(fill=tk.X)
        cat_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_task_list())

        # Quick actions
        actions_card = self.create_card(left_frame)
        actions_card.configure(bg=self.theme['sidebar_card'])
        actions_card.pack(fill=tk.X)
        tk.Label(actions_card, text="Quick Actions", font=Theme.FONTS['heading'],
                 fg=self.theme['sidebar_text'], bg=self.theme['sidebar_card']).pack(anchor=tk.W, pady=(0, 10))

        stats_btn = tk.Button(actions_card, text="📊 Show Statistics", command=self.show_statistics,
                              bg=self.theme['primary'], fg=self.theme['dark_text'], relief=tk.FLAT)
        stats_btn.pack(fill=tk.X, pady=4)

        clear_btn = tk.Button(actions_card, text="🗑️ Clear Completed", command=self.clear_completed,
                              bg=self.theme['danger'], fg=self.theme['dark_text'], relief=tk.FLAT)
        clear_btn.pack(fill=tk.X, pady=4)

        # Right side: tasks list
        right_frame = tk.Frame(content_frame, bg=self.theme['background'])
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        list_card = self.create_card(right_frame)
        list_card.configure(bg=self.theme['card'])
        list_card.pack(fill=tk.BOTH, expand=True)

        tk.Label(list_card, text="Your Tasks", font=Theme.FONTS['heading'],
                 fg=self.theme['dark_text'], bg=self.theme['card']).pack(anchor=tk.W, pady=(0, 10))

        # Canvas scrolling region
        list_frame = tk.Frame(list_card, bg=self.theme['card'])
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(list_frame, bg=self.theme['card'], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.theme['card'])
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel for different platforms
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)      # Windows
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)        # Linux scroll up
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)        # Linux scroll down

        # Stats label at header right
        self.stats_label = tk.Label(header_frame, text="Tasks: 0 | Completed: 0",
                                   font=Theme.FONTS['small'], fg=self.theme['muted'], bg=self.theme['background'])
        self.stats_label.pack(side=tk.RIGHT, padx=(0, 12))

    def create_card(self, parent):
        card = tk.Frame(parent, bg=self.theme['card'], relief=tk.FLAT, padx=12, pady=12)
        card.config(highlightbackground=self.theme['muted'], highlightthickness=1)
        return card

    def _on_mousewheel(self, event):
        # Cross-platform mousewheel handling
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")

    # ---------------------------
    # Task operations
    # ---------------------------
    def add_task(self):
        description = self.task_entry.get().strip()
        if not description:
            messagebox.showwarning("Warning", "Please enter a task description!")
            return

        try:
            priority = Priority(self.priority_var.get())
        except Exception:
            priority = Priority.MEDIUM

        category = self.category_var.get()

        # due date handling
        due_date = None
        if TKCALENDAR_AVAILABLE:
            try:
                val = self.due_picker.get_date()
                if val:
                    due_date = val.strftime('%Y-%m-%d')
            except Exception:
                due_date = None
        else:
            raw = self.due_picker.get().strip()
            if raw and raw.upper() != "YYYY-MM-DD":
                # validate date format
                try:
                    datetime.strptime(raw, '%Y-%m-%d')
                    due_date = raw
                except Exception:
                    # allow empty or invalid -> warn user
                    messagebox.showwarning("Warning", "Due date must be in YYYY-MM-DD format or left blank.")
                    return

        # Use explicit keyword args (fixes previous positional bug)
        self.todo_list.add_task(description, priority=priority, due_date=due_date, category=category)
        self.task_entry.delete(0, tk.END)
        if not TKCALENDAR_AVAILABLE:
            self.due_picker.delete(0, tk.END)
            self.due_picker.insert(0, "YYYY-MM-DD")
        self.refresh_task_list()
        self.update_statistics()

    def refresh_task_list(self):
        # clear current widgets
        for w in self.scrollable_frame.winfo_children():
            w.destroy()

        # get filters
        status_filter = self.status_var.get()
        cat_filter = self.category_filter_var.get()
        search_term = self.search_var.get().strip().lower()
        sort_mode = self.sort_var.get()

        tasks = list(self.todo_list.tasks)  # copy

        # apply status filter
        if status_filter == "pending":
            tasks = [t for t in tasks if t.status == Status.PENDING or t.status == Status.IN_PROGRESS]
        elif status_filter == "completed":
            tasks = [t for t in tasks if t.status == Status.COMPLETED]

        # category filter
        if cat_filter != "all":
            tasks = [t for t in tasks if t.category == cat_filter]

        # search
        if search_term:
            tasks = [t for t in tasks if search_term in t.description.lower() or search_term in t.category.lower()]

        # sorting
        if sort_mode == "Newest":
            tasks.sort(key=lambda x: x.created_at, reverse=True)
        elif sort_mode == "Oldest":
            tasks.sort(key=lambda x: x.created_at)
        elif sort_mode == "Priority (High→Low)":
            prio_order = {'high': 0, 'medium': 1, 'low': 2}
            tasks.sort(key=lambda x: prio_order.get(x.priority.value, 1))
        elif sort_mode == "Due Date (Soon→Later)":
            def due_key(x):
                return x.due_date if x.due_date else "9999-12-31"
            tasks.sort(key=due_key)

        if not tasks:
            empty = tk.Label(self.scrollable_frame, text="No tasks found. Add a new task to get started!",
                             font=Theme.FONTS['body'], fg=self.theme['muted'], bg=self.theme['card'], pady=20)
            empty.pack(fill=tk.X)
            return

        for t in tasks:
            self.create_task_widget(t)

    def create_task_widget(self, task: Task):
        tf = tk.Frame(self.scrollable_frame, bg=self.theme['card'], padx=12, pady=8)
        tf.pack(fill=tk.X, pady=6)
        tf.config(highlightbackground=self.theme['muted'], highlightthickness=1)

        # priority color bar
        pcolors = {
            Priority.LOW: self.theme['accent'],
            Priority.MEDIUM: self.theme['warning'],
            Priority.HIGH: self.theme['danger']
        }
        pb = tk.Frame(tf, bg=pcolors.get(task.priority, self.theme['warning']), width=6)
        pb.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        content = tk.Frame(tf, bg=self.theme['card'])
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # description
        desc_style = Theme.FONTS['body']
        if task.status == Status.COMPLETED:
            desc_lbl = tk.Label(content, text=task.description, font=('Arial', 11, 'overstrike'),
                                fg=self.theme['muted'], bg=self.theme['card'], anchor=tk.W)
        else:
            desc_lbl = tk.Label(content, text=task.description, font=desc_style,
                                fg=self.theme['dark_text'], bg=self.theme['card'], anchor=tk.W)
        desc_lbl.pack(fill=tk.X)

        # metadata
        meta = tk.Frame(content, bg=self.theme['card'])
        meta.pack(fill=tk.X)
        tk.Label(meta, text=f"#{task.category}", font=Theme.FONTS['small'], fg=self.theme['primary'],
                 bg=self.theme['card']).pack(side=tk.LEFT)
        tk.Label(meta, text=f"• {task.priority.value}", font=Theme.FONTS['small'], fg=self.theme['muted'],
                 bg=self.theme['card']).pack(side=tk.LEFT, padx=(8, 0))
        if task.due_date:
            try:
                due_obj = datetime.strptime(task.due_date, '%Y-%m-%d')
                due_display = due_obj.strftime('%b %d, %Y')
            except Exception:
                due_display = task.due_date
            tk.Label(meta, text=f"• Due: {due_display}", font=Theme.FONTS['small'], fg=self.theme['muted'],
                     bg=self.theme['card']).pack(side=tk.LEFT, padx=(8, 0))

        # action buttons
        actions = tk.Frame(tf, bg=self.theme['card'])
        actions.pack(side=tk.RIGHT)
        if task.status != Status.COMPLETED:
            complete_btn = tk.Button(actions, text="✓", command=lambda id=task.id: self.complete_task(id),
                                     bg=self.theme['accent'], fg=self.theme['dark_text'], relief=tk.FLAT, width=3)
            complete_btn.pack(side=tk.LEFT, padx=4)
        edit_btn = tk.Button(actions, text="✏️", command=lambda id=task.id: self.edit_task(id),
                             bg=self.theme['secondary'], fg=self.theme['dark_text'], relief=tk.FLAT, width=3)
        edit_btn.pack(side=tk.LEFT, padx=4)
        delete_btn = tk.Button(actions, text="🗑️", command=lambda id=task.id: self.delete_task(id),
                               bg=self.theme['danger'], fg=self.theme['dark_text'], relief=tk.FLAT, width=3)
        delete_btn.pack(side=tk.LEFT, padx=4)

    def complete_task(self, task_id: int):
        if self.todo_list.complete_task(task_id):
            self.refresh_task_list()
            self.update_statistics()
        else:
            messagebox.showerror("Error", "Failed to complete task.")

    def delete_task(self, task_id: int):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this task?"):
            if self.todo_list.remove_task(task_id):
                self.refresh_task_list()
                self.update_statistics()
            else:
                messagebox.showerror("Error", "Failed to delete task!")

    def edit_task(self, task_id: int):
        task = self.todo_list.get_task(task_id)
        if not task:
            return

        ew = tk.Toplevel(self.root)
        ew.title("Edit Task")
        ew.geometry("420x320")
        ew.configure(bg=self.theme['background'])
        ew.transient(self.root)
        ew.grab_set()

        try:
            ew.eval(f'tk::PlaceWindow {str(ew)} center')
        except Exception:
            pass

        card = self.create_card(ew)
        card.configure(bg=self.theme['card'])
        card.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        tk.Label(card, text="Edit Task", font=Theme.FONTS['heading'], fg=self.theme['dark_text'], bg=self.theme['card']).pack(anchor=tk.W, pady=(0, 8))

        tk.Label(card, text="Description:", bg=self.theme['card'], fg=self.theme['dark_text']).pack(anchor=tk.W)
        desc_var = tk.StringVar(value=task.description)
        desc_entry = tk.Entry(card, textvariable=desc_var, bg=self.theme['input'], fg=self.theme['dark_text'], relief=tk.FLAT)
        desc_entry.pack(fill=tk.X, pady=(4, 8))

        # Priority + Category
        row = tk.Frame(card, bg=self.theme['card'])
        row.pack(fill=tk.X, pady=(0, 8))
        tk.Label(row, text="Priority:", bg=self.theme['card'], fg=self.theme['dark_text']).pack(side=tk.LEFT)
        pr_var = tk.StringVar(value=task.priority.value)
        ttk.Combobox(row, textvariable=pr_var, values=["low", "medium", "high"], state="readonly", width=10).pack(side=tk.LEFT, padx=8)

        tk.Label(row, text="Category:", bg=self.theme['card'], fg=self.theme['dark_text']).pack(side=tk.LEFT, padx=(8,0))
        cat_var = tk.StringVar(value=task.category)
        ttk.Combobox(row, textvariable=cat_var, values=["general", "work", "personal", "shopping", "health"], state="readonly", width=12).pack(side=tk.LEFT, padx=8)

        tk.Label(card, text="Due Date (optional):", bg=self.theme['card'], fg=self.theme['dark_text']).pack(anchor=tk.W)
        if TKCALENDAR_AVAILABLE:
            due_edit = DateEntry(card, date_pattern='yyyy-mm-dd')
            if task.due_date:
                try:
                    due_obj = datetime.strptime(task.due_date, '%Y-%m-%d')
                    due_edit.set_date(due_obj)
                except Exception:
                    pass
            due_edit.pack(fill=tk.X, pady=(4, 8))
        else:
            due_edit = tk.Entry(card, bg=self.theme['input'], fg=self.theme['dark_text'], relief=tk.FLAT)
            due_edit.insert(0, task.due_date if task.due_date else "YYYY-MM-DD")
            due_edit.pack(fill=tk.X, pady=(4, 8))

        def save_changes():
            new_desc = desc_var.get().strip()
            if not new_desc:
                messagebox.showwarning("Warning", "Please enter a task description!")
                return
            try:
                new_pr = Priority(pr_var.get())
            except Exception:
                new_pr = Priority.MEDIUM
            new_cat = cat_var.get()
            new_due = None
            if TKCALENDAR_AVAILABLE:
                try:
                    d = due_edit.get_date()
                    new_due = d.strftime('%Y-%m-%d')
                except Exception:
                    new_due = None
            else:
                raw = due_edit.get().strip()
                if raw and raw.upper() != "YYYY-MM-DD":
                    try:
                        datetime.strptime(raw, '%Y-%m-%d')
                        new_due = raw
                    except Exception:
                        messagebox.showwarning("Warning", "Due date must be YYYY-MM-DD or blank.")
                        return

            if self.todo_list.update_task(task_id, description=new_desc, priority=new_pr, due_date=new_due, category=new_cat):
                ew.destroy()
                self.refresh_task_list()
            else:
                messagebox.showerror("Error", "Failed to update task.")

        save_btn = tk.Button(card, text="Save Changes", command=save_changes, bg=self.theme['primary'], fg=self.theme['dark_text'], relief=tk.FLAT)
        save_btn.pack(fill=tk.X, pady=(8, 4))
        tk.Button(card, text="Cancel", command=ew.destroy, bg=self.theme['secondary'], fg=self.theme['dark_text'], relief=tk.FLAT).pack(fill=tk.X)

    def clear_completed(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all completed tasks?"):
            completed = [t for t in self.todo_list.tasks if t.status == Status.COMPLETED]
            for t in completed:
                self.todo_list.remove_task(t.id)
            self.refresh_task_list()
            self.update_statistics()

    def show_statistics(self):
        stats = self.todo_list.get_statistics()
        sw = tk.Toplevel(self.root)
        sw.title("Statistics")
        sw.geometry("380x380")
        sw.configure(bg=self.theme['background'])
        sw.transient(self.root)

        try:
            sw.eval(f'tk::PlaceWindow {str(sw)} center')
        except Exception:
            pass

        card = self.create_card(sw)
        card.configure(bg=self.theme['card'])
        card.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        tk.Label(card, text="📊 Statistics", font=Theme.FONTS['heading'], fg=self.theme['dark_text'], bg=self.theme['card']).pack(anchor=tk.W, pady=(0, 12))

        stats_data = [
            ("Total Tasks", f"{stats['total']}"),
            ("Completed", f"{stats['completed']}"),
            ("Pending", f"{stats['pending']}"),
            ("In Progress", f"{stats['in_progress']}"),
            ("Completion Rate", f"{stats['completion_rate']:.1f}%")
        ]
        for label, value in stats_data:
            f = tk.Frame(card, bg=self.theme['card'])
            f.pack(fill=tk.X, pady=6)
            tk.Label(f, text=label, fg=self.theme['muted'], bg=self.theme['card']).pack(side=tk.LEFT)
            tk.Label(f, text=value, fg=self.theme['dark_text'], bg=self.theme['card']).pack(side=tk.RIGHT)

    def update_statistics(self):
        stats = self.todo_list.get_statistics()
        self.stats_label.config(text=f"Tasks: {stats['total']} | Completed: {stats['completed']} | Rate: {stats['completion_rate']:.1f}%")

    def toggle_theme(self):
        self.theme_mode = 'light' if self.theme_mode == 'dark' else 'dark'
        self.theme = Theme.DARK if self.theme_mode == 'dark' else Theme.LIGHT
        # Rebuild UI with the selected theme: easiest reliable way is to destroy and recreate widgets
        for widget in self.root.winfo_children():
            widget.destroy()
        self.create_widgets()
        self.refresh_task_list()
        self.update_statistics()

    def export_csv(self):
        # Ask where to save
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")], title="Export tasks to CSV")
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id','description','priority','status','created_at','due_date','category','completed_at'])
                for t in self.todo_list.tasks:
                    writer.writerow([t.id, t.description, t.priority.value, t.status.value, t.created_at, t.due_date or "", t.category, t.completed_at or ""])
            messagebox.showinfo("Exported", f"Tasks successfully exported to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV:\n{e}")

def main():
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
