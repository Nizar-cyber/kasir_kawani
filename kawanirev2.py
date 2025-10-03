import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Kasir Kawani", layout="wide")

# ----------------- SESSION STATE -----------------
if "products" not in st.session_state:
    # contoh produk awal
    st.session_state.products = [
        {"Owner": "Bu.Ilah", "Nama Produk": "Kacang Bawang", "Harga Reseller": 18000, "Harga Retail": 20000, "Potongan": 2000, "Stock": 10},
        {"Owner": "Bu.Ilah", "Nama Produk": "Emping Melinjo", "Harga Reseller": 22000, "Harga Retail": 25000, "Potongan": 3000, "Stock": 5},
        {"Owner": "Pak.Budi", "Nama Produk": "Keripik Pisang", "Harga Reseller": 15000, "Harga Retail": 18000, "Potongan": 3000, "Stock": 8},
    ]

if "cart" not in st.session_state:
    st.session_state.cart = []

if "laporan" not in st.session_state:
    st.session_state.laporan = []


# ----------------- FUNGSI -----------------
def add_to_cart(product, qty):
    for item in st.session_state.cart:
        if item["Nama Produk"] == product["Nama Produk"] and item["Owner"] == product["Owner"]:
            item["Qty"] += qty
            return
    st.session_state.cart.append({
        "Owner": product["Owner"],
        "Nama Produk": product["Nama Produk"],
        "Harga Retail": product["Harga Retail"],
        "Harga Reseller": product["Harga Reseller"],
        "Potongan": product["Potongan"],
        "Qty": qty
    })


def checkout(payment):
    total = sum(item["Harga Retail"] * item["Qty"] for item in st.session_state.cart)
    if payment < total:
        return None, "Uang pembayaran kurang!"
    change = payment - total
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # kurangi stok & simpan laporan
    for item in st.session_state.cart:
        for p in st.session_state.products:
            if p["Nama Produk"] == item["Nama Produk"] and p["Owner"] == item["Owner"]:
                p["Stock"] -= item["Qty"]

        st.session_state.laporan.append({
            "Timestamp": timestamp,
            "Owner": item["Owner"],
            "Nama Produk": item["Nama Produk"],
            "Qty": item["Qty"],
            "Harga Retail": item["Harga Retail"],
            "Harga Reseller": item["Harga Reseller"],
            "Potongan": item["Potongan"],
            "Gross Income": item["Harga Retail"] * item["Qty"],
            "Net Income": (item["Harga Retail"] - item["Potongan"]) * item["Qty"]
        })
    st.session_state.cart = []
    return change, None


def export_excel(data):
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Laporan")
    return output.getvalue()


def export_pdf(data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, y, "Laporan Penjualan")
    y -= 30
    c.setFont("Helvetica", 9)
    for row in data:
        line = f"{row['Timestamp']} | {row['Owner']} | {row['Nama Produk']} | Qty:{row['Qty']} | Gross:{row['Gross Income']} | Net:{row['Net Income']}"
        c.drawString(30, y, line)
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 50
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def download_template():
    df = pd.DataFrame([{
        "Owner": "Nama Pemilik",
        "Nama Produk": "Nama Produk",
        "Harga Reseller": 10000,
        "Harga Retail": 12000,
        "Potongan": 2000,
        "Stock": 10
    }])
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Template")
    return output.getvalue()


def upload_products(file):
    df = pd.read_excel(file)
    for _, row in df.iterrows():
        st.session_state.products.append({
            "Owner": row["Owner"],
            "Nama Produk": row["Nama Produk"],
            "Harga Reseller": row["Harga Reseller"],
            "Harga Retail": row["Harga Retail"],
            "Potongan": row["Harga Retail"] - row["Harga Reseller"],
            "Stock": row["Stock"]
        })


# ----------------- SIDEBAR -----------------
menu = st.sidebar.radio("Menu", ["Kasir", "Daftar Produk", "Tambah Produk", "Edit Produk", "Laporan Penjualan"])

# ----------------- KASIR -----------------
# ----------------- KASIR -----------------
if menu == "Kasir":
    st.header("Kasir")

    cols = st.columns(4)
    for i, product in enumerate(st.session_state.products):
        with cols[i % 4]:
            st.markdown(f"**{product['Nama Produk']}**")
            st.write(f"Owner: {product['Owner']}")
            st.write(f"Harga: Rp{product['Harga Retail']:,}")
            st.write(f"Stock: {product['Stock']}")
            qty = st.number_input(f"Qty {product['Nama Produk']}", min_value=1, max_value=product["Stock"], value=1, key=f"qty_{i}")
            if st.button(f"Tambah {product['Nama Produk']}", key=f"add_{i}"):
                if product["Stock"] >= qty:
                    add_to_cart(product, qty)
                    st.success("Ditambahkan ke keranjang")

    st.subheader("Keranjang")
    if st.session_state.cart:
        total = sum(item["Harga Retail"] * item["Qty"] for item in st.session_state.cart)
        df_cart = pd.DataFrame(st.session_state.cart)
        st.table(df_cart)
        st.write(f"Total: Rp{total:,}")

        # --- fitur hapus/kurangi qty ---
        pilih_item = st.selectbox("Pilih item keranjang", range(len(st.session_state.cart)),
                                  format_func=lambda x: f"{st.session_state.cart[x]['Nama Produk']} (Qty:{st.session_state.cart[x]['Qty']})")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Kurangi Qty"):
                if st.session_state.cart[pilih_item]["Qty"] > 1:
                    st.session_state.cart[pilih_item]["Qty"] -= 1
                    st.success("Qty dikurangi 1")
                else:
                    st.warning("Qty sudah 1, gunakan hapus jika ingin menghilangkan item")
                st.rerun()

        with col2:
            if st.button("Hapus Item"):
                nama_item = st.session_state.cart[pilih_item]["Nama Produk"]
                st.session_state.cart.pop(pilih_item)
                st.success(f"Item '{nama_item}' dihapus dari keranjang")
                st.rerun()

        # --- checkout ---
        payment = st.number_input("Nominal Pembayaran", min_value=0, value=0)
        if st.button("Checkout"):
            change, error = checkout(payment)
            if error:
                st.error(error)
            else:
                st.success(f"Checkout berhasil! Kembalian: Rp{change:,}")
    else:
        st.write("Keranjang kosong.")


# ----------------- DAFTAR PRODUK -----------------
elif menu == "Daftar Produk":
    st.header("Daftar Produk")
    st.table(pd.DataFrame(st.session_state.products))

# ----------------- TAMBAH PRODUK -----------------
elif menu == "Tambah Produk":
    st.header("Tambah Produk")
    with st.form("tambah_produk"):
        owner = st.text_input("Owner")
        nama = st.text_input("Nama Produk")
        harga_reseller = st.number_input("Harga Reseller", min_value=0)
        harga_retail = st.number_input("Harga Retail", min_value=0)
        stock = st.number_input("Stock", min_value=0)
        submit = st.form_submit_button("Tambah")
        if submit:
            st.session_state.products.append({
                "Owner": owner,
                "Nama Produk": nama,
                "Harga Reseller": harga_reseller,
                "Harga Retail": harga_retail,
                "Potongan": harga_retail - harga_reseller,
                "Stock": stock
            })
            st.success("Produk berhasil ditambahkan!")

# ----------------- EDIT PRODUK -----------------
# ----------------- EDIT PRODUK -----------------
elif menu == "Edit Produk":
    st.header("Edit Produk")
    if st.session_state.products:
        produk_names = [f"{p['Nama Produk']} ({p['Owner']})" for p in st.session_state.products]
        pilihan = st.selectbox("Pilih produk", range(len(produk_names)), format_func=lambda x: produk_names[x])
        product = st.session_state.products[pilihan]

        with st.form("edit_produk"):
            product["Owner"] = st.text_input("Owner", value=product["Owner"])
            product["Nama Produk"] = st.text_input("Nama Produk", value=product["Nama Produk"])
            product["Harga Reseller"] = st.number_input("Harga Reseller", min_value=0, value=product["Harga Reseller"])
            product["Harga Retail"] = st.number_input("Harga Retail", min_value=0, value=product["Harga Retail"])
            product["Stock"] = st.number_input("Stock", min_value=0, value=product["Stock"])
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Update")
            with col2:
                hapus = st.form_submit_button("Hapus Produk")

            if submit:
                product["Potongan"] = product["Harga Retail"] - product["Harga Reseller"]
                st.success("Produk berhasil diupdate!")

            if hapus:
                nama_dihapus = product["Nama Produk"]
                st.session_state.products.pop(pilihan)
                st.success(f"Produk '{nama_dihapus}' berhasil dihapus!")
                st.rerun()

# ----------------- LAPORAN PENJUALAN -----------------
elif menu == "Laporan Penjualan":
    st.header("Laporan Penjualan")
    if st.session_state.laporan:
        df = pd.DataFrame(st.session_state.laporan)
        st.dataframe(df)

        # Group by Owner untuk summary
        summary = df.groupby("Owner").agg(
            Gross_Income=("Gross Income", "sum"),
            Net_Income=("Net Income", "sum")
        ).reset_index()
        st.subheader("Summary per Owner")
        st.table(summary)

        # Download
        excel_data = export_excel(st.session_state.laporan)
        st.download_button("Download Excel", excel_data, "laporan.xlsx")
        pdf_data = export_pdf(st.session_state.laporan)
        st.download_button("Download PDF", pdf_data, "laporan.pdf")

    else:
        st.write("Belum ada transaksi.")

    st.subheader("Template Produk")
    st.download_button("Download Template Excel", download_template(), "template_produk.xlsx")
    uploaded = st.file_uploader("Upload Produk Excel", type=["xlsx"])
    if uploaded:
        upload_products(uploaded)
        st.success("Produk berhasil diupload!")
