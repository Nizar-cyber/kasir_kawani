import streamlit as st
import pandas as pd
import sqlite3
import datetime

# ---------------------------
# Database setup
# ---------------------------
DB_FILE = "kasir.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        sku TEXT PRIMARY KEY,
        name TEXT,
        price REAL,
        stock INTEGER
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        sku TEXT,
        name TEXT,
        qty INTEGER,
        price REAL,
        subtotal REAL
    )""")
    conn.commit()
    conn.close()

def add_product(sku, name, price, stock):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT INTO products (sku, name, price, stock) VALUES (?, ?, ?, ?)",
                (sku, name, price, stock))
    conn.commit()
    conn.close()

def get_products():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM products", conn)
    conn.close()
    return df

def remove_product(sku):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE sku=?", (sku,))
    conn.commit()
    conn.close()

def add_transaction(date, sku, name, qty, price, subtotal):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT INTO transactions (date, sku, name, qty, price, subtotal) VALUES (?, ?, ?, ?, ?, ?)",
                (date, sku, name, qty, price, subtotal))
    conn.commit()
    conn.close()

def get_transactions():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM transactions", conn)
    conn.close()
    return df

# ---------------------------
# Init
# ---------------------------
init_db()
if "cart" not in st.session_state:
    st.session_state.cart = {}

st.title("🛒 Aplikasi Kasir")

# ---------------------------
# Sidebar menu
# ---------------------------
menu = st.sidebar.radio("Menu", ["Tambah Produk", "Histori Transaksi"])

if menu == "Tambah Produk":
    st.sidebar.subheader("Tambah Produk Baru")
    sku = st.sidebar.text_input("SKU")
    name = st.sidebar.text_input("Nama Produk")
    price = st.sidebar.number_input("Harga", min_value=0.0, step=1000.0)
    stock = st.sidebar.number_input("Stok", min_value=0, step=1)
    if st.sidebar.button("Tambah"):
        if sku and name:
            try:
                add_product(sku, name, price, stock)
                st.sidebar.success("Produk berhasil ditambahkan!")
            except Exception as e:
                st.sidebar.error(f"SKU sudah ada atau error: {e}")
        else:
            st.sidebar.warning("Lengkapi semua data produk.")

elif menu == "Histori Transaksi":
    st.sidebar.subheader("Histori Transaksi")
    df_trans = get_transactions()
    if df_trans.empty:
        st.sidebar.info("Belum ada transaksi.")
    else:
        st.sidebar.dataframe(df_trans)

# ---------------------------
# Main area: Daftar Produk
# ---------------------------
st.subheader("📦 Daftar Produk")
df_products = get_products()

if df_products.empty:
    st.info("Belum ada produk, silakan tambah di menu sidebar.")
else:
    st.write("📋 Debug Produk:", df_products)  # debug tampilkan semua produk
    for _, row in df_products.iterrows():
        col1, col2, col3, col4 = st.columns([3,1,1,1])
        with col1:
            st.write(f"**{row['name']}** — {row['sku']} — Rp{row['price']:.0f} — stok: {int(row['stock'])}")
        with col2:
            qty = st.number_input(f"qty_{row['sku']}", min_value=1, max_value=100, value=1, key=f"qty_{row['sku']}")
        with col3:
            if st.button("➕ Tambah", key=f"add_{row['sku']}"):
                if int(row['stock']) < qty:
                    st.warning("Stok tidak cukup!")
                else:
                    if row['sku'] in st.session_state.cart:
                        st.session_state.cart[row['sku']]['qty'] += int(qty)
                        st.session_state.cart[row['sku']]['subtotal'] = (
                            st.session_state.cart[row['sku']]['qty'] * st.session_state.cart[row['sku']]['price']
                        )
                    else:
                        st.session_state.cart[row['sku']] = {
                            "sku": row['sku'],
                            "name": row['name'],
                            "price": float(row['price']),
                            "qty": int(qty),
                            "subtotal": float(row['price']) * int(qty)
                        }
                    st.success(f"{row['name']} x{qty} ditambahkan ke keranjang")
        with col4:
            if st.button("🗑 Hapus", key=f"del_{row['sku']}"):
                remove_product(row['sku'])
                st.success(f"Produk {row['name']} dihapus")
                st.experimental_rerun()

# ---------------------------
# Keranjang Belanja
# ---------------------------
st.subheader("🛒 Keranjang Belanja")

if not st.session_state.cart:
    st.info("Keranjang kosong.")
else:
    df_cart = pd.DataFrame(st.session_state.cart).T
    total = df_cart["subtotal"].sum()

    for _, row in df_cart.iterrows():
        c1, c2, c3, c4 = st.columns([4,1,1,1])
        with c1:
            st.write(f"**{row['name']}** ({row['sku']})")
        with c2:
            newq = st.number_input(f"qty_cart_{row['sku']}", min_value=1, value=int(row['qty']), key=f"qty_cart_{row['sku']}")
            st.session_state.cart[row['sku']]['qty'] = int(newq)
            st.session_state.cart[row['sku']]['subtotal'] = st.session_state.cart[row['sku']]['price'] * int(newq)
        with c3:
            if st.button("🗑 Hapus", key=f"remove_{row['sku']}"):
                del st.session_state.cart[row['sku']]
                st.experimental_rerun()
        with c4:
            st.write(f"Rp{st.session_state.cart[row['sku']]['subtotal']:.0f}")

    st.write("### Total: Rp{:.0f}".format(sum([item['subtotal'] for item in st.session_state.cart.values()])))

    if st.button("✅ Checkout"):
        today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for item in st.session_state.cart.values():
            add_transaction(today, item['sku'], item['name'], item['qty'], item['price'], item['subtotal'])
        st.success("Transaksi berhasil disimpan.")
        st.session_state.cart = {}
