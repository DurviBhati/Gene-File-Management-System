import tkinter as tk;
from tkinter import filedialog, messagebox;
import sqlite3;
import os;
from datetime import datetime;
from Bio import Entrez, SeqIO

## Database setup 
def init_db():
    conn = sqlite3.connect('gene_data.db')
    cursor =conn.cursor()
    ### Create gene_files table 
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gene_files (
            file_id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            upload_date TEXT
        )
     ''')
    #### Create genes table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS genes (
                        gene_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_id INTEGER,
                        gene_name TEXT,
                        sequence TEXT,
                        length INTEGER,
                        FOREIGN KEY(file_id) REFERENCES gene_files(file_id)
                   )
                ''')
    conn.commit()
    conn.close()


### To parse the fasta file
def parse_fasta(file_path):
    gene=[]
    with open(file_path, 'r') as file:
        name = None
        seq = []

        for l in file:
            l = l.strip()
            if l.startswith('>'):
                if name:
                    gene.append((name,''.join(seq)))
                name = l[1:].strip()
                seq = []
            else:
                seq.append(l)
        if name:
                gene.append((name,''.join(seq)))
    return gene

## Save data to the database 
def save_db(file_name, gene_data):
    if not gene_data:
        messagebox.showerror("Error", "No gene data found in the file.")
        return
    
    ## Get the first gene
    first_gene_name, first_sequence = gene_data[0]
    conn = sqlite3.connect('gene_data.db')
    cursor = conn.cursor()

    ###Check if the file has already been uploaded or not 
    cursor.execute('''
        SELECT gene_id FROM genes
        WHERE gene_name = ? AND sequence = ?
    ''', (first_gene_name, first_sequence))
                   
    if cursor.fetchone():
        messagebox.showwarning("Duplicate", f"A file with gene '{first_gene_name}' and same sequence has already been uploaded.")
        conn.close()
        return  # Stop execution if duplicate

    upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('INSERT INTO gene_files (file_name, upload_date) VALUES (?,?)', (file_name, upload_date))
    file_id = cursor.lastrowid

    for gene_name, sequence in gene_data:
        cursor.execute('''
            INSERT INTO genes(file_id, gene_name, sequence, length)
            VALUES (?,?,?,?)
        ''', (file_id, gene_name, sequence, len(sequence)))
    conn.commit()
    conn.close()

## Upload the file from the GUI
def upload_file():
    file_path = filedialog.askopenfilename(filetypes=[("FASTA files", "*.fasta *.fa *.txt")])
    if not file_path:
        return
    try:
        gene_data = parse_fasta(file_path)
        if not gene_data:
            messagebox.showerror("Error", "No gene sequences found in the file.")
            
            return
        save_db(os.path.basename(file_path),gene_data)
        
        messagebox.showinfo("Success", f"Parsed and saved {len(gene_data)} genes succesfully!!!")
    except Exception as e :
        messagebox.showerror("Error", f"An error occured: {e}")
    
# Set your email to access NCBI
Entrez.email = "durvibhati69@gmail.com"

from Bio import Entrez, SeqIO
from tkinter import simpledialog

Entrez.email = "your_email@example.com"  # Replace with your email

def download_from_ncbi():
    gene_id = simpledialog.askstring("Download Gene", "Enter Gene Accession or Nucleotide ID:")
    if not gene_id:
        return

    try:
        # Check if the ID exists in NCBI Nucleotide DB
        search = Entrez.esearch(db="nucleotide", term=gene_id, retmode="xml")
        search_results = Entrez.read(search)
        search.close()

        if not search_results["IdList"]:
            messagebox.showwarning("Not Found", f"No nucleotide entry found for '{gene_id}'.")
            return

        ncbi_id = search_results["IdList"][0]

        # Fetch the sequence
        handle = Entrez.efetch(db="nucleotide", id=ncbi_id, rettype="fasta", retmode="text")
        record = SeqIO.read(handle, "fasta")
        handle.close()

        gene_data = [(record.id, str(record.seq))]
        file_name = f"NCBI_{record.id}"

        # Save to your DB
        save_db(file_name, gene_data)
        messagebox.showinfo("Success", f"Downloaded and saved gene '{record.id}' from NCBI.")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to download gene:\n{e}")


### Tkinter GUI setup 
def main():
    init_db()
    root = tk.Tk()
    root.title("GENE FILE MANAGEMENT SYSTEM")
    root.geometry("300x200")

    lbl = tk.Label(root, text= "Upload and Parse a Gene File (FASTA)", font = ("Arial", 12))
    lbl.pack(pady=20)
    
    upload_btn = tk.Button(
        root, 
        text="Upload FASTA File", 
        command = upload_file, 
        bg="#4CAF50", 
        fg="white", 
        padx=10, 
        pady=5
    )
    upload_btn.pack()

    view_btn = tk.Button(root, 
        text="View Stored Genes", 
        command = view_genes, 
        bg="#2196F3", 
        fg="white", 
        padx=10, 
        pady=5
    )
    view_btn.pack(pady=10)

    download_btn = tk.Button(
    root, 
    text="Download Gene from NCBI", 
    command= download_from_ncbi, 
    bg="#673AB7", 
    fg="white", 
    padx=10, 
    pady=5
    )
    download_btn.pack(pady=10)

    print("Launching GUI... ")
    root.mainloop()

def view_genes():
        try:
            conn = sqlite3.connect('gene_data.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT g.gene_name, g.length, gf.file_name, gf.upload_date
                FROM genes g
                JOIN gene_files gf ON g.file_id = gf.file_id
                ORDER BY gf.upload_date DESC
            ''')
            records = cursor.fetchall()
            conn.close()
            if not records: 
                messagebox.showinfo("No Genes", "No gene records found in the database.")
                return

            view_window =tk.Toplevel()
            view_window.title("Stored Gene Data")
            ##view_window.geometry("600X400") (The window doesnt appear with this line)

            ###search box
            search_var = tk.StringVar()
            tk.Label(view_window, text="Search Gene Name:").pack(pady=5)
            tk.Entry(view_window, textvariable=search_var).pack(pady=5)
            tk.Button(view_window, text="Search", command=lambda: populate_table(search_var.get())).pack(pady=5)

            ####  For table view 
            from tkinter import ttk
            tree = ttk.Treeview(view_window, columns=("file_id", "file_name", "gene_name", "sequence", "length", "upload_date"), show="headings")
            for col in tree["columns"]:
                tree.heading("file_name", text="File Name")
                tree.heading("gene_name", text="Gene Name")
                tree.heading("sequence", text="Sequence")
                tree.heading("length", text="Length")
                tree.heading("upload_date", text="Upload Date")
                tree.column("file_id", width=0, stretch=False)
                tree.heading("file_id", text="")  # Hide header
            tree.pack(expand=True, fill="both")

            ####  To export the table in csv format 
            def export_to_csv():
                import csv
                file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
                if not file_path:
                    return 

                with open(file_path, 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(["File Name", "Gene Name", "Sequence", "Length", "Upload Date"])
                    for child in tree.get_children():
                        writer.writerow(tree.item(child)["values"])
    
                messagebox.showinfo("Exported", f"Data exported to {file_path}")

            tk.Button(view_window, text="Export as CSV", command=export_to_csv, bg="orange", fg="white").pack(pady=10)

            #####  Populate table function    
            def populate_table(keyword=""):
                tree.delete(*tree.get_children())
                conn = sqlite3.connect("gene_data.db")
                cursor = conn.cursor()
                query = '''
                    SELECT gf.file_id, gf.file_name, g.gene_name, g.sequence, g.length, gf.upload_date
                    FROM genes g
                    JOIN gene_files gf ON g.file_id = gf.file_id
                    WHERE g.gene_name LIKE ?
                '''
                cursor.execute(query, ('%' + keyword + '%',))
                rows =cursor.fetchall()
                for row in rows:
                    tree.insert("", "end", values=row)
                conn.close()
            populate_table()


            def delete_selected():
                selected_item = tree.selection()
                if not selected_item:
                    messagebox.showwarning("No Selection", "Please select a record to delete.")
                    return

                values = tree.item(selected_item[0], "values")
                print("Selected item values:", values) ### debug line
                
                file_id = values[0]

                confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete File ID {file_id}? This will remove all associated genes.")

                if confirm:
                    try:
                        conn = sqlite3.connect("gene_data.db")
                        cursor = conn.cursor()

                        # Delete genes linked to the file
                        cursor.execute("DELETE FROM genes WHERE file_id = ?", (file_id,))
                        # Delete the file record itself
                        cursor.execute("DELETE FROM gene_files WHERE file_id = ?", (file_id,))

                        conn.commit()
                        conn.close()
                        messagebox.showinfo("Deleted", "File and associated gene entries deleted.")
                        populate_table()  # Refresh table
                    except Exception as e:
                            messagebox.showerror("Error", f"Failed to delete: {e}")
            tk.Button(view_window, text="Delete Selected File", command=delete_selected, bg="#f44336", fg="white").pack(pady=10)

            def edit_file_name():
                selected_item = tree.selection()
                if not selected_item:
                    messagebox.showwarning("No Selection", "Please select a record to edit.")
                    return

                values = tree.item(selected_item[0], "values")
                file_id = values[0]
                old_name = values[1]

                # Ask for the new name
                new_name = tk.simpledialog.askstring("Edit File Name", f"Enter new name for file '{old_name}':")
                if new_name:
                    try:
                        conn = sqlite3.connect("gene_data.db")
                        cursor = conn.cursor()
                        cursor.execute("UPDATE gene_files SET file_name = ? WHERE file_id = ?", (new_name, file_id))
                        conn.commit()
                        conn.close()

                        messagebox.showinfo("Updated", f"File name updated to '{new_name}'.")
                        populate_table()
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to update file name:\n{e}")
            tk.Button(view_window, text="Edit File Name", command=edit_file_name, bg="#FFC107", fg="black").pack(pady=5)

            def view_selected_file():
                selected_item = tree.selection()
                if not selected_item:
                    messagebox.showwarning("No Selection", "Please select a file to view.")
                    return

                values = tree.item(selected_item[0], "values")
                file_id = values[0]

                try:
                    conn = sqlite3.connect("gene_data.db")
                    cursor = conn.cursor()

                    # Get gene entries associated with the file_id
                    cursor.execute('''
                        SELECT gene_name, sequence FROM genes WHERE file_id = ?
                    ''', (file_id,))
                    genes = cursor.fetchall()
                    conn.close()

                    if not genes:
                        messagebox.showinfo("Empty", "No gene entries found for this file.")
                        return

                     # Create a new window to show file content
                    content_window = tk.Toplevel()
                    content_window.title("View File Contents")
                    content_window.geometry("500x400")

                    text_box = tk.Text(content_window, wrap="word")
                    text_box.pack(expand=True, fill="both")

                    for gene_name, sequence in genes:
                        text_box.insert(tk.END, f">{gene_name}\n")
                        # Format sequence in chunks of 60 characters
                        for i in range(0, len(sequence), 60):
                            text_box.insert(tk.END, sequence[i:i+60] + "\n")
                        text_box.insert(tk.END, "\n")

                    text_box.config(state=tk.DISABLED)

                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load file content: {e}")
            tk.Button(view_window, text="View Selected File", command=view_selected_file, bg="#795548", fg="white").pack(pady=10)


        except Exception as e:
            messagebox.showerror("Error", f"Could not retrieve gene data.\n{e}")    
            

        

### to launch the app
if __name__ == "__main__":
    main()
        
    