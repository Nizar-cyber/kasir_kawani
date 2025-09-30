import streamlit as st
import pandas as pd
import sqlite3
import os

# ========== DATABASE SETUP ==========
DB_FILE = "kasir.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Produk
    c.execute("""CREATE TABLE IF NOT EXISTS produk (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT UNIQUE,
                    nama TEXT,
                    harga REAL,
                    foto TEXT
                )""")
    # Transaksi
    c.execute("""CREATE TABLE IF NOT EXISTS transaksi (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT,
                    nama TEXT,
                    harga REAL,
                    qty INTEGER,
                    total REAL,
                    tanggal TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""")
    conn.commit()
    conn.close()

def run_query(query, params=(), fetch=False):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(query, params)
    data = c.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return data

# ========== PAGE: TAMBAH PRODUK ==========
def tambah_produk():
    st.header("Tambah Produk Baru")
    sku = st.text_input("SKU Produk")
    nama = st.text_input("Nama Produk")
    harga = st.number_input("Harga Produk", min_value=0.0, step=100.0)
    foto = st.text_input("URL Foto Produk (opsional)")

    if st.button("Simpan Produk"):
        try:
            run_query("INSERT INTO produk (sku, nama, harga, foto) VALUES (?, ?, ?, ?)", 
                      (sku, nama, harga, foto))
            st.success(f"Produk {nama} berhasil ditambahkan!")
        except Exception as e:
            st.error(f"Error: {e}")

# ========== PAGE: EDIT PRODUK ==========
def edit_produk():
    st.header("Edit Produk")
    produk = run_query("SELECT id, sku, nama, harga, foto FROM produk", fetch=True)
    df = pd.DataFrame(produk, columns=["ID", "SKU", "Nama", "Harga", "Foto"])

    if not df.empty:
        pilihan = st.selectbox("Pilih produk untuk diedit", df["Nama"])
        produk_data = df[df["Nama"] == pilihan].iloc[0]

        new_sku = st.text_input("SKU", produk_data["SKU"])
        new_nama = st.text_input("Nama", produk_data["Nama"])
        new_harga = st.number_input("Harga", value=float(produk_data["Harga"]))
        new_foto = st.text_input("Foto", produk_data["Foto"])

        if st.button("Update Produk"):
            run_query("UPDATE produk SET sku=?, nama=?, harga=?, foto=? WHERE id=?", 
                      (new_sku, new_nama, new_harga, new_foto, produk_data["ID"]))
            st.success("Produk berhasil diupdate!")
    else:
        st.warning("Belum ada produk.")

# ========== PAGE: KASIR ==========
def kasir():
    st.header("Kasir")

    produk = run_query("SELECT sku, nama, harga, foto FROM produk", fetch=True)
    df_produk = pd.DataFrame(produk, columns=["SKU", "Nama", "Harga", "Foto"])

    if "keranjang" not in st.session_state:
        st.session_state.keranjang = []

    if not df_produk.empty:
        cols = st.columns(3)
        for idx, row in df_produk.iterrows():
            col = cols[idx % 3]
            with col:
                if row["Foto"]:
                    st.image(row["Foto"], width=120)
                st.write(f"**{row['Nama']}**")
                st.write(f"Rp {int(row['Harga']):,}")
                if st.button(f"Tambah {row['SKU']}", key=row["SKU"]):
                    st.session_state.keranjang.append(row)

    # Keranjang
    st.sidebar.subheader("Keranjang Belanja")
    total = 0
    if st.session_state.keranjang:
        for item in st.session_state.keranjang:
            st.sidebar.write(f"{item['Nama']} - Rp {int(item['Harga']):,}")
            total += item["Harga"]

        st.sidebar.write(f"**Total: Rp {int(total):,}**")

        if st.sidebar.button("Bayar"):
            for item in st.session_state.keranjang:
                run_query("INSERT INTO transaksi (sku, nama, harga, qty, total) VALUES (?, ?, ?, ?, ?)", 
                          (item["SKU"], item["Nama"], item["Harga"], 1, item["Harga"]))
            st.session_state.keranjang = []
            st.sidebar.success("Transaksi berhasil disimpan!")
    else:
        st.sidebar.write("Keranjang kosong.")

# ========== PAGE: LAPORAN ==========
def laporan():
    st.header("Laporan Penjualan")

    data = run_query("SELECT sku, nama, SUM(qty), SUM(total) FROM transaksi GROUP BY sku, nama", fetch=True)
    df = pd.DataFrame(data, columns=["SKU", "Nama", "Jumlah Terjual", "Total Penjualan"])

    if not df.empty:
        st.dataframe(df)
    else:
        st.warning("Belum ada transaksi.")

    st.subheader("Hapus Histori Penjualan")
    password = st.text_input("Masukkan Password untuk Hapus Histori", type="password")
    if st.button("Hapus Semua Histori"):
        if password == "Sellacyute":
            run_query("DELETE FROM transaksi")
            st.success("Histori transaksi berhasil dihapus!")
        else:
            st.error("Password salah!")

# ========== MAIN ==========
def main():
    st.set_page_config(page_title="Kasir Sederhana", layout="wide")
    init_db()

    menu = st.sidebar.radio("Menu", ["Kasir", "Tambah Produk", "Edit Produk", "Laporan Penjualan"])

    if menu == "Kasir":
        kasir()
    elif menu == "Tambah Produk":
        tambah_produk()
    elif menu == "Edit Produk":
        edit_produk()
    elif menu == "Laporan Penjualan":
        laporan()

if __name__ == "__main__":
    main()
