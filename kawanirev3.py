import streamlit as st
import pandas as pd
import datetime
from io import BytesIO

st.set_page_config(page_title="Kasir Kawani", layout="wide")

# ==================== SESSION STATE ====================
if "products" not in st.session_state:
    st.session_state.products = [
        {"Nama Produk": "Produk A", "Harga Jual": 15000, "Harga Reseller": 12000, "Owner": "Owner1"},
        {"Nama Produk": "Produk B", "Harga Jual": 20000, "Harga Reseller": 17000, "Owner": "Owner1"},
        {"Nama Produk": "Produk C", "Harga Jual": 10000, "Harga Reseller": 8000, "Owner": "Owner2"},
    ]

if "cart" not in st.session_state:
    st.session_state.cart = []

if "sales" not in st.session_state:
    st.session_state.sales = []

# ==================== HELPER FUNCTIONS ====================
def add_to_cart(product, qty):
    for item in st.session_state.cart:
        if item["Nama Produk"] == product["Nama Produk"]:
            item["Qty"] += qty
            item["Subtotal"] = item["Qty"] * item["Harga Jual"]
            return
    st.session_state.cart.append({
        "Nama Produk": product["Nama Produk"],
        "Owner": product["Owner"],
        "Harga Jual": product["Harga Jual"],
        "Harga Reseller": product["Harga Reseller"],
        "Potongan": product["Harga Jual"] - product["Harga Reseller"],
        "Qty": qty,
        "Subtotal": qty * product["Harga Jual"]
    })

def checkout(payment):
    total = sum(item["Subtotal"] for item in st.session_state.cart)
    kembalian = payment - total
    for item in st.session_state.cart:
        st.session_state.sales.append({
            "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Nama Produk": item["Nama Produk"],
            "Owner": item["Owner"],
            "Harga Jual": item["Harga Jual"],
            "Harga Reseller": item["Harga Reseller"],
            "Potongan": item["Potongan"],
            "Qty": item["Qty"],
            "Subtotal": item["Subtotal"],
            "Pembayaran": payment,
            "Kembalian": kembalian
        })
    st.session_state.cart = []
    return kembalian

def export_excel(data):
    output = BytesIO()
    df = pd.DataFrame(data)
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Laporan")
    return output.getvalue()

def template_excel():
    template = pd.DataFrame([{
        "Timestamp": "",
        "Nama Produk": "",
        "Owner": "",
        "Harga Jual": "",
        "Harga Reseller": "",
        "Potongan": "",
        "Qty": "",
        "Subtotal": "",
        "Pembayaran": "",
        "Kembalian": ""
    }])
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        template.to_excel(writer, index=False, sheet_name="Template")
    return output.getvalue()

# ==================== MENU ====================
menu = st.sidebar.radio("Menu", ["Kasir", "Daftar Produk", "Tambah Produk", "Edit Produk", "Laporan Penjualan"])

# ==================== KASIR ====================
if menu == "Kasir":
    st.header("💰 Kasir")
    for p in st.session_state.products:
        col1, col2, col3, col4 = st.columns([3,2,2,2])
        with col1: st.write(p["Nama Produk"])
        with col2: st.write(f"Rp{p['Harga Jual']:,}")
        with col3: qty = st.number_input(f"Qty {p['Nama Produk']}", 1, 100, 1, key=f"qty_{p['Nama Produk']}")
        with col4: 
            if st.button("Tambah", key=f"add_{p['Nama Produk']}"):
                add_to_cart(p, qty)
                try: st.rerun()
                except: st.experimental_rerun()

    st.subheader("Keranjang")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        st.dataframe(df_cart)
        total = sum(item["Subtotal"] for item in st.session_state.cart)
        st.write(f"**Total: Rp{total:,}**")

        payment = st.number_input("Nominal Pembayaran", min_value=0, step=1000)
        if st.button("Checkout"):
            if payment >= total:
                kembalian = checkout(payment)
                st.success(f"Transaksi berhasil! Kembalian: Rp{kembalian:,}")
            else:
                st.error("Nominal pembayaran kurang!")
    else:
        st.write("Keranjang kosong.")

# ==================== DAFTAR PRODUK ====================
elif menu == "Daftar Produk":
    st.header("📦 Daftar Produk")
    df_products = pd.DataFrame(st.session_state.products)
    st.dataframe(df_products)

    st.subheader("Hapus Produk")
    if st.session_state.products:
        product_names = [p["Nama Produk"] for p in st.session_state.products]
        pilih = st.selectbox("Pilih produk yang ingin dihapus:", product_names)
        if st.button("Hapus Produk"):
            st.session_state.products = [p for p in st.session_state.products if p["Nama Produk"] != pilih]
            try: st.rerun()
            except: st.experimental_rerun()

# ==================== TAMBAH PRODUK ====================
elif menu == "Tambah Produk":
    st.header("➕ Tambah Produk")
    nama = st.text_input("Nama Produk")
    harga_jual = st.number_input("Harga Jual", min_value=0, step=1000)
    harga_reseller = st.number_input("Harga Reseller", min_value=0, step=1000)
    owner = st.text_input("Owner")

    if st.button("Simpan Produk Baru"):
        st.session_state.products.append({
            "Nama Produk": nama,
            "Harga Jual": harga_jual,
            "Harga Reseller": harga_reseller,
            "Owner": owner
        })
        st.success("Produk berhasil ditambahkan!")

# ==================== EDIT PRODUK ====================
elif menu == "Edit Produk":
    st.header("✏️ Edit Produk")
    if st.session_state.products:
        product_names = [p["Nama Produk"] for p in st.session_state.products]
        pilih = st.selectbox("Pilih produk yang ingin diedit:", product_names)
        product = next(p for p in st.session_state.products if p["Nama Produk"] == pilih)

        nama = st.text_input("Nama Produk", value=product["Nama Produk"])
        harga_jual = st.number_input("Harga Jual", min_value=0, step=1000, value=product["Harga Jual"])
        harga_reseller = st.number_input("Harga Reseller", min_value=0, step=1000, value=product["Harga Reseller"])
        owner = st.text_input("Owner", value=product["Owner"])

        if st.button("Simpan Perubahan"):
            product.update({
                "Nama Produk": nama,
                "Harga Jual": harga_jual,
                "Harga Reseller": harga_reseller,
                "Owner": owner
            })
            st.success("Produk berhasil diupdate!")

# ==================== LAPORAN ====================
elif menu == "Laporan Penjualan":
    st.header("📑 Laporan Penjualan")
    if st.session_state.sales:
        df_sales = pd.DataFrame(st.session_state.sales)
        st.dataframe(df_sales)

        st.download_button("Download Laporan Excel", data=export_excel(st.session_state.sales),
                           file_name="laporan_penjualan.xlsx")

        st.download_button("Download Template Excel", data=template_excel(),
                           file_name="template_laporan.xlsx")
    else:
        st.info("Belum ada transaksi.")
