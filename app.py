import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from cipher import cipher, key

import sqlcheck
import sqldump
import sqlformat

CONFIG_FILE = Path(__file__).with_name("settings.dat")


class Application(tk.Frame):
    def __init__(self, master):

        super().__init__(master)

        master.title("SQL Checker")
        master.geometry("800x600")

        self.sql_file = tk.StringVar()
        self.dat_file = tk.StringVar()

        self.pack(fill="both", expand=True)
        self.create_widgets()

    def ask_sqlfile(self):

        types = [("SQL ファイル", "*.sql *.txt"), ("SQLite データベース", "*.sqlite3 *.db")]
        filename = filedialog.askopenfilename(filetypes=types)
        if filename:
            self.sql_file.set(filename)
            self.output.delete("1.0", "end")

    def ask_datfile(self):

        types = [("データファイル", "*.dat")]
        filename = filedialog.askopenfilename(filetypes=types)
        if filename:
            self.dat_file.set(filename)
            self.output.delete("1.0", "end")

    def run_checker(self):

        sql = self.sql_file.get()
        if not sql:
            messagebox.showerror("Error", "SQL ファイルが指定されていません。")
            return

        dat = self.dat_file.get()
        if not dat:
            messagebox.showerror("Error", "データファイルが指定されていません。")
            return

        sql_path = Path(sql)
        if not sql_path.is_file():
            messagebox.showerror("Error", "指定された SQL ファイルが見つかりません。")
            return

        dat_path = Path(dat)
        if not dat_path.is_file():
            messagebox.showerror("Error", "指定されたデータファイルが見つかりません。")
            return

        self.output.delete("1.0", "end")

        # 答案データの読み込み
        # データベースのダンプはそのまま使い，SQL ファイルは整形して使う
        if sql_path.suffix in (".sqlite3", ".db"):
            target_sql = sqldump.dump(sql_path)
        else:
            with sql_path.open(encoding="utf-8") as f:
                target_sql = sqlformat.format(f.read())

        # 解答データの読み込み
        with dat_path.open("rb") as f:
            d = f.read()
        p = key.load(CONFIG_FILE)
        try:
            answer_sql = cipher.decrypt(d, p).splitlines(keepends=True)
        except ValueError:
            messagebox.showerror("Error", "データファイルが破損しています。")
            return

        lines = sqlcheck.check(target_sql, answer_sql)

        # 解答データのみに存在する行をマスク
        def mask(line: str) -> str:
            if line.startswith("+ "):
                return "+ " + re.sub(r"[^\s\"'`(),;]", "?", line[2:])
            return line

        lines = list(map(mask, lines))

        # 問題箇所があった場合のみ結果を出力
        for line in lines:
            if re.match(r"^[+-] ", line):
                self.output.insert("end", "以下の箇所が怪しいかもしれません。\n\n")
                break
        else:
            self.output.insert("end", "問題は見つかりませんでした。\n")
            return
        self.output.insert("end", "".join(lines))

    def create_widgets(self):

        # チェック対象ファイル
        frame1 = tk.Frame(self)
        frame1.pack(side="top", pady=16, padx=16, fill="x")

        label1 = tk.Label(frame1, text="SQL ファイル:", width=10, anchor="e")
        label1.pack(side="left")

        entry1 = tk.Entry(frame1, textvariable=self.sql_file)
        entry1.pack(side="left", padx=8, fill="x", expand=True)

        button1 = tk.Button(frame1, text="参照...", command=self.ask_sqlfile)
        button1.pack(side="left")

        # データファイル
        frame2 = tk.Frame(self)
        frame2.pack(side="top", pady=16, padx=16, fill="x")

        label2 = tk.Label(frame2, text="データファイル:", width=10, anchor="e")
        label2.pack(side="left")

        entry2 = tk.Entry(frame2, textvariable=self.dat_file)
        entry2.pack(side="left", padx=8, fill="x", expand=True)

        button2 = tk.Button(frame2, text="参照...", command=self.ask_datfile)
        button2.pack(side="left")

        # チェックボタン
        button3 = tk.Button(self, width=10, text="チェック", command=self.run_checker)
        button3.pack(side="top", pady=16, padx=16)

        # 出力欄
        frame3 = tk.Frame(self)
        frame3.pack(side="top", pady=16, padx=16, fill="both", expand=True)
        frame3.columnconfigure(0, weight=1)
        frame3.rowconfigure(0, weight=1)

        text = tk.Text(frame3, wrap="none")
        text.grid(column=0, row=0, sticky="news")
        self.output = text

        yscroll = tk.Scrollbar(frame3, orient="vertical", command=text.yview)
        yscroll.grid(column=1, row=0, sticky="ns")
        text.configure(yscrollcommand=yscroll.set)

        xscroll = tk.Scrollbar(frame3, orient="horizontal", command=text.xview)
        xscroll.grid(column=0, row=1, sticky="ew")
        text.configure(xscrollcommand=xscroll.set)


def main():
    root = tk.Tk()
    app = Application(root)
    app.mainloop()


if __name__ == "__main__":
    main()
