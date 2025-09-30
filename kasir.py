import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from sqlalchemy import create_engine, text

# ---------------------------
# Database (SQLite) helpers
# ---------------------------
DB_FILE = "pos.db"
engine = create_engine(f"sqlite:///{DB_FILE}", connect_args={"check_same_thread": False})

def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE,
            name TEXT,
            price REAL,
            stock INTEGER
        )
        """))
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            total REAL,
            items TEXT,
            cashier TEXT
        )
        """))
    seed_products()

def seed_products():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM products"))
        count = result.scalar_one()
        if count == 0:
            sample = [
                ("P001","Air Mineral 600ml",4000,50),
                ("P002","Roti Tawar",12000,30),
                ("P003","Kopi Sachet",3000,100),
                ("P004","Susu UHT",8000,25),
            ]
            for sku,name,price,stock in sample:
                try:
                    conn.execute(text("INSERT INTO products (sku,name,price,stock) VALUES (:sku,:name,:price,:stock)"),
                                 {"sku":sku,"name":name,"price":price,"stock":stock})
                except:
                    pass

def get_products():
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM products"), conn)
    return df

def add_or_update_product(sku, name, price, stock):
    with engine.connect() as conn:
        res = conn.execute(text("SELECT id FROM products WHERE sku=:sku"), {"sku":sku}).fetchone()
        if res:
            conn.execute(text("UPDATE products SET name=:name, price=:price, stock=:stock WHERE sku=:sku"),
                         {"sku":sku,"name":name,"price":price,"stock":stock})
        else:
            conn.execute(text("INSERT INTO products (sku,name,price,stock) VALUES (:sku,:name,:price,:stock)"),
                         {"sku":sku,"name":name,"price":price,"stock":stock})

def remove_product(sku):
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM products WHERE sku=:sku"), {"sku":sku})

def change_stock(sku, delta):
    with engine.connect() as conn:
        conn.execute(text("UPDATE products SET stock = stock + :d WHERE sku=:sku"), {"d":delta,"sku":sku})

def save_transaction(items_df, total, cashier="kasir"):
    items_str = items_df.to_json(orient="records", force_ascii=False)
    timestamp = datetime.now().isoformat()
    with engine.connect() as conn:
        conn.execute(text("INSERT INTO transactions (timestamp,total,items,cashier) VALUES (:t,:total,:items,:cashier)"),
                     {"t":timestamp,"total":total,"items":items_str,"cashier":cashier})
    # juga simpan CSV struk
    filename = f"receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    items_df.to_csv(filename, index=False)
    return filename

def get_transactions():
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM transactions ORDER BY id DESC LIMIT 200"), conn)
    return df

# ---------------------------
# Streamlit App
# ---------------------------

st.set_page_config(page_title="Aplikasi Kasir", layout="wide")
init_db()

st.title("🧾 Aplikasi Kasir — Python + Streamlit")

# session_state: cart
if "cart" not in st.session_state:
    st.session_state.cart = {}

# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.header("Menu")
    tab = st.radio("Pilih", ["Tambah/Edit Produk", "Histori Transaksi"])

    if tab == "Tambah/Edit Produk":
        st.subheader("Tambah atau Edit Produk")
        with st.form("form_add"):
            sku = st.text_input("SKU (unik, misal P001)")
            name = st.text_input("Nama produk")
            price = st.number_input("Harga (Rp)", min_value=0.0, value=1000.0, step=500.0)
            stock = st.number_input("Stok awal", min_value=0, value=0, step=1)
            submitted = st.form_submit_button("Simpan")
            if submitted:
                if not sku or not name:
                    st.error("SKU dan nama wajib diisi")
                else:
                    add_or_update_product(sku, name, float(price), int(stock))
                    st.success("Produk disimpan")
        st.write("---")
        st.subheader("Hapus Produk")
        sku_del = st.text_input("SKU untuk dihapus")
        if st.button("🗑 Hapus produk"):
            if sku_del:
                remove_product(sku_del)
                st.success(f"Produk {sku_del} dihapus (jika ada)")
            else:
                st.error("Masukkan SKU")

    elif tab == "Histori Transaksi":
        st.subheader("Histori Transaksi")
        tx = get_transactions()
        if tx.empty:
            st.info("Belum ada transaksi.")
        else:
            st.dataframe(tx, use_container_width=True)
            sel = st.selectbox("Lihat detail transaksi (pilih id)", options=tx['id'].tolist())
            if st.button("Tampilkan detail"):
                rec = tx[tx['id'] == sel].iloc[0]
                st.write("Waktu:", rec['timestamp'])
                st.write("Total: Rp", rec['total'])
                try:
                    items = pd.read_json(rec['items'])
                    st.table(items)
                except Exception as e:
                    st.write("Tidak bisa parse items:", e)

# ---------------------------
# Main Area: Produk + Keranjang
# ---------------------------

# Produk
st.subheader("📦 Daftar Produk")

df_products = get_products()
if df_products.empty:
    st.info("Belum ada produk, silakan tambah di sidebar.")
else:
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

# Keranjang
st.subheader("🛒 Keranjang Belanja")

def cart_to_df():
    if not st.session_state.cart:
        return pd.DataFrame(columns=["sku","name","price","qty","subtotal"])
    rows = []
    for sku,v in st.session_state.cart.items():
        rows.append({"sku":sku,"name":v['name'],"price":v['price'],"qty":v['qty'],"subtotal":v['subtotal']})
    return pd.DataFrame(rows)

df_cart = cart_to_df()
if df_cart.empty:
    st.info("Keranjang kosong.")
else:
    for i, row in df_cart.iterrows():
        c1, c2, c3, c4 = st.columns([4,1,1,1])
        with c1:
            st.write(f"**{row['name']}** ({row['sku']})")
        with c2:
            newq = st.number_input(f"qty_cart_{row['sku']}", min_value=1, value=int(row['qty']), key=f"qty_cart_{row['sku']}")
            st.session_state.cart[row['sku']]['qty'] = int(newq)
            st.session_state.cart[row['sku']]['subtotal'] = (
                st.session_state.cart[row['sku']]['price'] * int(newq)
            )
        with c3:
            if st.button("🗑 Hapus", key=f"remove_{row['sku']}"):
                del st.session_state.cart[row['sku']]
                st.experimental_rerun()
        with c4:
            st.write(f"Rp{st.session_state.cart[row['sku']]['subtotal']:.0f}")

    # Summary & Checkout
    subtotal = sum(v['subtotal'] for v in st.session_state.cart.values())
    st.metric("Subtotal (Rp)", f"{subtotal:,.0f}")
    diskon_pct = st.number_input("Diskon (%)", min_value=0.0, max_value=100.0, value=0.0, format="%.2f")
    diskon_val = subtotal * (diskon_pct/100)
    pajak_pct = st.number_input("Pajak (%)", min_value=0.0, max_value=100.0, value=0.0, format="%.2f")
    pajak_val = (subtotal - diskon_val) * (pajak_pct/100)
    total = subtotal - diskon_val + pajak_val

    st.markdown(f"### Total: Rp {total:,.0f}")

    bayar = st.number_input("Bayar (Rp)", min_value=0.0, value=float(total))
    kembalian = bayar - total
    st.write("Kembalian: Rp", f"{kembalian:,.0f}")

    cashier_name = st.text_input("Nama Kasir", value="Kasir 1")

    if st.button("Checkout / Bayar"):
        if not st.session_state.cart:
            st.error("Keranjang kosong")
        elif bayar < total:
            st.error("Uang bayar kurang")
        else:
            items_df = cart_to_df()
            filename = save_transaction(items_df, float(total), cashier=cashier_name)
            for sku, v in st.session_state.cart.items():
                change_stock(sku, -v['qty'])
            st.success(f"Transaksi sukses. Struk disimpan: {filename}")
            st.session_state.cart = {}
            st.experimental_rerun()

