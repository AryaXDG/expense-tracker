import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
import os
import requests
from collections import defaultdict

class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Expense Tracker by Arya")
        self.root.geometry("600x500")
        
        # File paths
        self.data_file = "data.txt"
        self.config_file = "config.txt"
        self.env_file = ".env"
        
        # Initialize data
        self.expenses = []
        self.monthly_limit = 0
        self.gemini_api_key = ""
        
        # Load configuration and data
        self.load_config()
        self.load_expenses()
        self.load_env()
        
        # Setup GUI
        self.setup_gui()
        
        # Update display
        self.update_budget_display()
    
    def load_env(self):
        """Load environment variables from .env file"""
        if os.path.exists(self.env_file):
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        if key.strip() == 'GEMINI_API_KEY':
                            self.gemini_api_key = value.strip().strip('"\'')
    
    def load_config(self):
        """Load monthly budget from config.txt or prompt user to set it"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                content = f.read().strip()
                if content.startswith('monthly_limit='):
                    self.monthly_limit = float(content.split('=')[1])
        else:
            self.setup_monthly_limit()
    
    def setup_monthly_limit(self):
        """Prompt user to set monthly budget and save to config.txt"""
        while True:
            try:
                limit = simpledialog.askfloat(
                    "Setup", 
                    "Enter your monthly budget limit:",
                    minvalue=0.01
                )
                if limit is None:  # User cancelled
                    self.monthly_limit = 1000.0  # Default value
                    break
                self.monthly_limit = limit
                break
            except:
                messagebox.showerror("Error", "Please enter a valid number")
        
        self.save_config()
    
    def save_config(self):
        """Save monthly budget to config.txt"""
        with open(self.config_file, 'w') as f:
            f.write(f"monthly_limit={self.monthly_limit}")
    
    def load_expenses(self):
        """Load expenses from data.txt"""
        self.expenses = []
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            date_str = parts[0].strip()
                            category = parts[1].strip()
                            amount = float(parts[2].strip())
                            description = parts[3].strip() if len(parts) > 3 else ""
                            
                            self.expenses.append({
                                'date': datetime.datetime.strptime(date_str, '%Y-%m-%d').date(),
                                'category': category,
                                'amount': amount,
                                'description': description
                            })
    
    def save_expense(self, date, category, amount, description):
        """Save a new expense to data.txt"""
        with open(self.data_file, 'a') as f:
            f.write(f"{date} | {category} | {amount:.2f} | {description}\n")
        
        # Add to memory
        self.expenses.append({
            'date': datetime.datetime.strptime(str(date), '%Y-%m-%d').date(),
            'category': category,
            'amount': float(amount),
            'description': description
        })
    
    def get_current_month_expenses(self):
        """Get expenses for current month"""
        current_date = datetime.date.today()
        current_month_expenses = []
        
        for expense in self.expenses:
            if (expense['date'].year == current_date.year and 
                expense['date'].month == current_date.month):
                current_month_expenses.append(expense)
        
        return current_month_expenses
    
    def get_current_month_total(self):
        """Calculate total spending for current month"""
        current_expenses = self.get_current_month_expenses()
        return sum(expense['amount'] for expense in current_expenses)
    
    def setup_gui(self):
        """Setup the main GUI interface"""
        # Title
        title_label = tk.Label(self.root, text="Personal Expense Tracker", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Expense entry frame
        entry_frame = tk.Frame(self.root)
        entry_frame.pack(pady=10, padx=20, fill="x")
        
        # Amount field
        tk.Label(entry_frame, text="Amount:").grid(row=0, column=0, sticky="w", padx=5)
        self.amount_entry = tk.Entry(entry_frame)
        self.amount_entry.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Category field
        tk.Label(entry_frame, text="Category:").grid(row=1, column=0, sticky="w", padx=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(entry_frame, textvariable=self.category_var,
                                          values=["Food", "Travel", "Shopping", "Entertainment", 
                                                 "Bills", "Healthcare", "Other"])
        self.category_combo.grid(row=1, column=1, padx=5, sticky="ew")
        
        # Description field
        tk.Label(entry_frame, text="Description:").grid(row=2, column=0, sticky="w", padx=5)
        self.description_entry = tk.Entry(entry_frame)
        self.description_entry.grid(row=2, column=1, padx=5, sticky="ew")
        
        # Date field
        tk.Label(entry_frame, text="Date:").grid(row=3, column=0, sticky="w", padx=5)
        self.date_entry = tk.Entry(entry_frame)
        self.date_entry.insert(0, datetime.date.today().strftime('%Y-%m-%d'))
        self.date_entry.grid(row=3, column=1, padx=5, sticky="ew")
        
        # Configure column weights for resizing
        entry_frame.columnconfigure(1, weight=1)
        
        # Add expense button
        add_btn = tk.Button(entry_frame, text="Add Expense", command=self.add_expense,
                           bg="#4CAF50", fg="white", font=("Arial", 10, "bold"))
        add_btn.grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")
        
        # Budget display frame
        budget_frame = tk.Frame(self.root)
        budget_frame.pack(pady=10, padx=20, fill="x")
        
        self.budget_label = tk.Label(budget_frame, text="", font=("Arial", 12))
        self.budget_label.pack()
        
        # Progress bar for budget
        self.budget_progress = ttk.Progressbar(budget_frame, length=400, mode='determinate')
        self.budget_progress.pack(pady=5)
        
        # Buttons frame
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(pady=20)
        
        # Chart buttons
        daily_chart_btn = tk.Button(buttons_frame, text="Show Daily Chart", 
                                   command=self.show_daily_chart,
                                   bg="#2196F3", fg="white")
        daily_chart_btn.grid(row=0, column=0, padx=5)
        
        monthly_chart_btn = tk.Button(buttons_frame, text="Show Monthly Chart", 
                                     command=self.show_monthly_chart,
                                     bg="#2196F3", fg="white")
        monthly_chart_btn.grid(row=0, column=1, padx=5)
        
        # AI suggestion button
        ai_btn = tk.Button(buttons_frame, text="Get AI Suggestion", 
                          command=self.get_ai_suggestion,
                          bg="#FF9800", fg="white")
        ai_btn.grid(row=1, column=0, padx=5, pady=5)
        
        # Update limit button
        update_limit_btn = tk.Button(buttons_frame, text="Update Budget Limit", 
                                    command=self.update_limit,
                                    bg="#9C27B0", fg="white")
        update_limit_btn.grid(row=1, column=1, padx=5, pady=5)
    
    def add_expense(self):
        """Add a new expense entry"""
        try:
            amount = float(self.amount_entry.get())
            category = self.category_var.get()
            description = self.description_entry.get()
            date_str = self.date_entry.get()
            
            # Validate inputs
            if not category:
                messagebox.showerror("Error", "Please select a category")
                return
            
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be greater than 0")
                return
            
            # Validate date format
            try:
                datetime.datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Error", "Date must be in YYYY-MM-DD format")
                return
            
            # Save expense
            self.save_expense(date_str, category, amount, description)
            
            # Clear fields
            self.amount_entry.delete(0, tk.END)
            self.category_var.set("")
            self.description_entry.delete(0, tk.END)
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, datetime.date.today().strftime('%Y-%m-%d'))
            
            # Update budget display
            self.update_budget_display()
            
            messagebox.showinfo("Success", "Expense added successfully!")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
    
    def update_budget_display(self):
        """Update the budget display and progress bar"""
        current_total = self.get_current_month_total()
        remaining = self.monthly_limit - current_total
        percentage = (current_total / self.monthly_limit) * 100
        
        self.budget_label.config(
            text=f"This Month: Rs.{current_total:.2f} / Rs.{self.monthly_limit:.2f} "
                 f"(Remaining: Rs.{remaining:.2f})"
        )
        
        self.budget_progress['value'] = min(percentage, 100)
        
        # Change color based on spending
        if percentage > 90:
            self.budget_label.config(fg="red")
        elif percentage > 75:
            self.budget_label.config(fg="orange")
        else:
            self.budget_label.config(fg="green")
    
    def show_daily_chart(self):
        """Display daily expenses chart for current month"""
        current_expenses = self.get_current_month_expenses()
        
        if not current_expenses:
            messagebox.showinfo("No Data", "No expenses found for current month")
            return
        
        # Group by day
        daily_totals = defaultdict(float)
        for expense in current_expenses:
            day = expense['date'].strftime('%Y-%m-%d')
            daily_totals[day] += expense['amount']
        
        # Create chart
        fig, ax = plt.subplots(figsize=(12, 6))
        days = list(daily_totals.keys())
        amounts = list(daily_totals.values())
        
        ax.bar(days, amounts, color='#4CAF50')
        ax.set_title('Daily Expenses - Current Month')
        ax.set_xlabel('Date')
        ax.set_ylabel('Amount (Rs.)')
        ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.show()
    
    def show_monthly_chart(self):
        """Display monthly expenses chart"""
        if not self.expenses:
            messagebox.showinfo("No Data", "No expenses found")
            return
        
        # Group by month
        monthly_totals = defaultdict(float)
        for expense in self.expenses:
            month_key = expense['date'].strftime('%Y-%m')
            monthly_totals[month_key] += expense['amount']
        
        # Create chart
        fig, ax = plt.subplots(figsize=(12, 6))
        months = list(monthly_totals.keys())
        amounts = list(monthly_totals.values())
        
        ax.bar(months, amounts, color='#2196F3')
        ax.set_title('Monthly Expenses')
        ax.set_xlabel('Month')
        ax.set_ylabel('Amount (Rs.)')
        ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.show()
    
    def get_ai_suggestion(self):
        """Get AI-powered spending suggestions from Gemini API"""
        if not self.gemini_api_key:
            messagebox.showwarning(
                "API Key Missing", 
                "Please add your GEMINI_API_KEY to the .env file to use AI suggestions."
            )
            return
        
        try:
            # Get last 20 expenses
            last_20_expenses = self.expenses[-20:] if len(self.expenses) >= 20 else self.expenses
            
            # Prepare data for AI
            current_total = self.get_current_month_total()
            
            # Format expenses for AI
            expenses_text = ""
            for expense in last_20_expenses:
                expenses_text += f"Date: {expense['date']}, Category: {expense['category']}, Amount: Rs.{expense['amount']:.2f}, Description: {expense['description']}\n"
            
            # Prepare prompt
            prompt = f"""
            Based on the following spending data, please provide personalized financial advice:
            
            Monthly Budget: Rs.{self.monthly_limit:.2f}
            Current Month Spending: Rs.{current_total:.2f}
            Remaining Budget: Rs.{self.monthly_limit - current_total:.2f}
            
            Recent Expenses (last 20):
            {expenses_text}
            
            Please provide:
            1. Analysis of spending patterns
            2. Areas where I might be overspending
            3. Specific suggestions to stay within budget
            4. Tips for better financial management
            
            Keep the response concise and actionable.
            """
            
            # Make API call (placeholder - you'll need to implement actual Gemini API call)
            response = self.call_gemini_api(prompt)
            
            # Display response in popup
            self.show_ai_response(response)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get AI suggestion: {str(e)}")
    
    def call_gemini_api(self, prompt):
        """Make API call to Gemini 1.5 Flash API"""
        # Placeholder implementation - replace with actual Gemini API endpoint
        api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.gemini_api_key
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1000
            }
        }
        
        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                return "Sorry, I couldn't generate a suggestion at this time."
                
        except requests.exceptions.RequestException as e:
            return f"API Error: {str(e)}\n\nPlease check your API key and internet connection."
        except Exception as e:
            return f"Error processing AI response: {str(e)}"
    
    def show_ai_response(self, response):
        """Display AI response in a popup window"""
        popup = tk.Toplevel(self.root)
        popup.title("AI Spending Suggestion")
        popup.geometry("500x400")
        
        # Text widget with scrollbar
        text_frame = tk.Frame(popup)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap="word", font=("Arial", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        text_widget.insert("1.0", response)
        text_widget.configure(state="disabled")
        
        # Close button
        close_btn = tk.Button(popup, text="Close", command=popup.destroy)
        close_btn.pack(pady=10)
    
    def update_limit(self):
        """Update monthly budget limit"""
        try:
            new_limit = simpledialog.askfloat(
                "Update Budget", 
                f"Enter new monthly budget limit (current: Rs.{self.monthly_limit:.2f}):",
                minvalue=0.01,
                initialvalue=self.monthly_limit
            )
            
            if new_limit is not None:
                self.monthly_limit = new_limit
                self.save_config()
                self.update_budget_display()
                messagebox.showinfo("Success", f"Budget limit updated to Rs.{new_limit:.2f}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update limit: {str(e)}")


def create_env_file():
    """Create .env file with placeholder for API key"""
    env_content = """# Expense Tracker Environment Variables
# Add your Gemini API key here
GEMINI_API_KEY=your_gemini_api_key_here

# To get a Gemini API key:
# 1. Go to https://makersuite.google.com/app/apikey
# 2. Create a new API key
# 3. Replace 'your_gemini_api_key_here' with your actual key
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print("Created .env file. Please add your GEMINI_API_KEY.")


def main():
    """Main function to run the application"""
    # Create .env file if it doesn't exist
    create_env_file()
    
    # Create and run the application
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()


if __name__ == "__main__":
    main()