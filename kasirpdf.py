import streamlit as st
import pandas as pd
import sqlite3

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
                    owner TEXT,
                    harga_reseller REAL,
                    harga_retail REAL,
                    stock INTEGER,
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
    owner = st.text_input("Owner")
    harga_reseller = st.number_input("Harga Reseller", min_value=0.0, step=100.0)
    harga_retail = st.number_input("Harga Retail", min_value=0.0, step=100.0)
    stock = st.number_input("Stock", min_value=0, step=1)
    foto = st.text_input("URL Foto Produk (opsional)")

    if st.button("Simpan Produk"):
        try:
            run_query("""INSERT INTO produk 
                         (sku, nama, owner, harga_reseller, harga_retail, stock, foto) 
                         VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                      (sku, nama, owner, harga_reseller, harga_retail, stock, foto))
            st.success(f"Produk {nama} berhasil ditambahkan!")
        except Exception as e:
            st.error(f"Error: {e}")

# ========== PAGE: EDIT PRODUK ==========
def edit_produk():
    st.header("Edit Produk")
    produk = run_query("SELECT id, sku, nama, owner, harga_reseller, harga_retail, stock, foto FROM produk", fetch=True)
    df = pd.DataFrame(produk, columns=["ID", "SKU", "Nama", "Owner", "Harga Reseller", "Harga Retail", "Stock", "Foto"])

    if not df.empty:
        pilihan = st.selectbox("Pilih produk untuk diedit", df["Nama"])
        produk_data = df[df["Nama"] == pilihan].iloc[0]

        new_sku = st.text_input("SKU", produk_data["SKU"])
        new_nama = st.text_input("Nama", produk_data["Nama"])
        new_owner = st.text_input("Owner", produk_data["Owner"])
        new_hr = st.number_input("Harga Reseller", value=float(produk_data["Harga Reseller"]))
        new_ht = st.number_input("Harga Retail", value=float(produk_data["Harga Retail"]))
        new_stock = st.number_input("Stock", value=int(produk_data["Stock"]))
        new_foto = st.text_input("Foto", produk_data["Foto"])

        if st.button("Update Produk"):
            run_query("""UPDATE produk 
                         SET sku=?, nama=?, owner=?, harga_reseller=?, harga_retail=?, stock=?, foto=? 
                         WHERE id=?""", 
                      (new_sku, new_nama, new_owner, new_hr, new_ht, new_stock, new_foto, produk_data["ID"]))
            st.success("Produk berhasil diupdate!")
    else:
        st.warning("Belum ada produk.")

# ========== PAGE: KASIR ==========
def kasir():
    st.header("Kasir")

    produk = run_query("SELECT sku, nama, owner, harga_reseller, harga_retail, stock, foto FROM produk", fetch=True)
    df_produk = pd.DataFrame(produk, columns=["SKU", "Nama", "Owner", "Harga Reseller", "Harga Retail", "Stock", "Foto"])

    if "keranjang" not in st.session_state:
        st.session_state.keranjang = []

    if not df_produk.empty:
        for idx, row in df_produk.iterrows():
            with st.container():
                col1, col2 = st.columns([1, 2])
                with col1:
                    if row["Foto"]:
                        st.image(row["Foto"], width=100)
                    else:
                        st.write("No Image")
                with col2:
                    st.write(f"**{row['Nama']}** (SKU: {row['SKU']})")
                    st.write(f"Owner: {row['Owner']}")
                    st.write(f"Reseller: Rp {int(row['Harga Reseller']):,}")
                    st.write(f"Retail: Rp {int(row['Harga Retail']):,}")
                    st.write(f"Stock: {row['Stock']}")
                    if st.button(f"Tambah ke Keranjang - {row['SKU']}", key=row["SKU"]):
                        if row["Stock"] > 0:
                            st.session_state.keranjang.append(row.to_dict())
                        else:
                            st.warning("Stock habis!")
                st.markdown("---")

    # Keranjang
    st.sidebar.subheader("Keranjang Belanja")
    total = 0
    if st.session_state.keranjang:
        for item in st.session_state.keranjang:
            st.sidebar.write(f"{item['Nama']} - Rp {int(item['Harga Retail']):,}")
            total += item["Harga Retail"]

        st.sidebar.write(f"**Total: Rp {int(total):,}**")

        if st.sidebar.button("Bayar"):
            for item in st.session_state.keranjang:
                # Simpan transaksi
                run_query("""INSERT INTO transaksi (sku, nama, harga, qty, total) VALUES (?, ?, ?, ?, ?)""", 
                          (item["SKU"], item["Nama"], item["Harga Retail"], 1, item["Harga Retail"]))
                # Update stok
                run_query("UPDATE produk SET stock = stock - 1 WHERE sku=?", (item["SKU"],))
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
