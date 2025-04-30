import tkinter as tk

root = tk.Tk()
root.title("Test Window")
root.geometry("300x200")
label = tk.Label(root, text="Tkinter is working!")
label.pack(pady=50)
root.mainloop()
