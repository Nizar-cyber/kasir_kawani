import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt

st.set_page_config(page_title="Kasir App", layout="wide")

# ----------------- SESSION STATE -----------------
if "products" not in st.session_state:
    st.session_state.products = [
        {
            "name": "Produk A",
            "owner": "Nizar",
            "reseller_price": 50000,
            "retail_price": 60000,
            "potongan": 5000,
            "stock": 10,
            "image": None,
        },
        {
            "name": "Produk B",
            "owner": "Andi",
            "reseller_price": 70000,
            "retail_price": 85000,
            "potongan": 0,
            "stock": 5,
            "image": None,
        },
    ]

if "cart" not in st.session_state:
    st.session_state.cart = []

if "history" not in st.session_state:
    st.session_state.history = []  # transaksi tersimpan di sini

# ----------------- FUNGSI -----------------
def add_to_cart(product, qty):
    if product["stock"] >= qty:
        found = False
        for item in st.session_state.cart:
            if item["name"] == product["name"]:
                item["qty"] += qty
                found = True
                break
        if not found:
            st.session_state.cart.append({
                "name": product["name"],
                "owner": product["owner"],
                "price": product["retail_price"],
                "potongan": product["potongan"],
                "qty": qty
            })
        st.success(f"{product['name']} ditambahkan ke keranjang")
    else:
        st.error("Stok tidak mencukupi!")

def checkout():
    if len(st.session_state.cart) == 0:
        st.warning("Keranjang kosong!")
        return
    total = 0
    transaksi = []
    for item in st.session_state.cart:
        subtotal = (item["price"] * item["qty"])
        total += subtotal
        transaksi.append({
            "name": item["name"],
            "owner": item["owner"],
            "qty": item["qty"],
            "price": item["price"],
            "potongan": item["potongan"],
            "subtotal": subtotal,
            "total_potongan": item["potongan"] * item["qty"]
        })
        # kurangi stok
        for p in st.session_state.products:
            if p["name"] == item["name"]:
                p["stock"] -= item["qty"]
    st.session_state.history.append(transaksi)
    st.session_state.cart = []
    st.success(f"Checkout berhasil! Total: Rp{total:,}")

def export_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Laporan Penjualan")
    return output.getvalue()

def export_pdf(df):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(200, height - 50, "Laporan Penjualan per Owner")

    c.setFont("Helvetica", 10)
    y = height - 100
    headers = ["Owner", "Qty", "Penjualan Kotor", "Potongan", "Penjualan Bersih"]
    col_widths = [100, 60, 120, 100, 120]

    # header tabel
    x = 50
    for i, h in enumerate(headers):
        c.drawString(x, y, h)
        x += col_widths[i]
    y -= 20

    # isi tabel
    for _, row in df.iterrows():
        x = 50
        c.drawString(x, y, str(row["owner"])); x += col_widths[0]
        c.drawString(x, y, str(row["total_qty"])); x += col_widths[1]
        c.drawString(x, y, f"Rp{row['penjualan_kotor']:,}"); x += col_widths[2]
        c.drawString(x, y, f"Rp{row['total_potongan']:,}"); x += col_widths[3]
        c.drawString(x, y, f"Rp{row['penjualan_bersih']:,}")
        y -= 20

        if y < 50:
            c.showPage()
            y = height - 50
    c.save()
    return buffer.getvalue()

# ----------------- SIDEBAR -----------------
menu = st.sidebar.radio("📌 Menu", ["Kasir", "Daftar Produk", "Tambah Produk", "Edit Produk", "Laporan Penjualan"])

# ----------------- MENU KASIR -----------------
if menu == "Kasir":
    st.title("🛒 Kasir")
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Pilih Produk")
        for product in st.session_state.products:
            with st.container():
                col1, col2 = st.columns([1, 2])
                with col1:
                    if product["image"]:
                        st.image(product["image"], width=120)
                    else:
                        st.write("No Image")

                with col2:
                    st.write(f"**{product['name']}**")
                    st.write(f"Harga: Rp{product['retail_price']:,}")
                    st.write(f"Potongan: Rp{product['potongan']:,}")
                    st.write(f"Stok: {product['stock']}")
                    qty = st.number_input(
                        f"Qty {product['name']}",
                        min_value=1,
                        max_value=product["stock"],
                        value=1,
                        key=f"qty_{product['name']}"
                    )
                    if st.button(f"Tambah ke Keranjang ({product['name']})", key=f"btn_{product['name']}"):
                        add_to_cart(product, qty)
            st.markdown("---")

    with col_right:
        st.subheader("Keranjang")
        if len(st.session_state.cart) == 0:
            st.info("Keranjang kosong")
        else:
            total = 0
            for item in st.session_state.cart:
                subtotal = item["price"] * item["qty"]
                total += subtotal
                st.write(f"{item['name']} x{item['qty']} - Rp{subtotal:,}")
                if st.button(f"Hapus {item['name']}", key=f"del_{item['name']}"):
                    st.session_state.cart.remove(item)
                    st.rerun()
            st.write(f"### Total: Rp{total:,}")
            if st.button("Checkout"):
                checkout()
                st.rerun()

# ----------------- MENU DAFTAR PRODUK -----------------
elif menu == "Daftar Produk":
    st.title("📦 Daftar Produk")
    df = pd.DataFrame(st.session_state.products)
    st.dataframe(df[["name", "owner", "reseller_price", "retail_price", "potongan", "stock"]])

# ----------------- MENU TAMBAH PRODUK -----------------
elif menu == "Tambah Produk":
    st.title("➕ Tambah Produk")
    with st.form("add_product"):
        name = st.text_input("Nama Produk")
        owner = st.text_input("Owner")
        reseller_price = st.number_input("Harga Reseller", min_value=0)
        retail_price = st.number_input("Harga Ritel", min_value=0)
        potongan = st.number_input("Potongan", min_value=0, value=0)
        stock = st.number_input("Stok", min_value=0)
        image_file = st.file_uploader("Upload Foto Produk", type=["jpg", "png", "jpeg"])
        submit = st.form_submit_button("Simpan")

        if submit:
            image_data = None
            if image_file:
                image_data = image_file.read()
            st.session_state.products.append({
                "name": name,
                "owner": owner,
                "reseller_price": reseller_price,
                "retail_price": retail_price,
                "potongan": potongan,
                "stock": stock,
                "image": image_data
            })
            st.success("Produk berhasil ditambahkan!")

# ----------------- MENU EDIT PRODUK -----------------
elif menu == "Edit Produk":
    st.title("✏️ Edit Produk")
    product_list = [p["name"] for p in st.session_state.products]
    selected_product = st.selectbox("Pilih Produk", product_list)
    product = next((p for p in st.session_state.products if p["name"] == selected_product), None)

    if product:
        with st.form("edit_product"):
            name = st.text_input("Nama Produk", product["name"])
            owner = st.text_input("Owner", product["owner"])
            reseller_price = st.number_input("Harga Reseller", min_value=0, value=product["reseller_price"])
            retail_price = st.number_input("Harga Ritel", min_value=0, value=product["retail_price"])
            potongan = st.number_input("Potongan", min_value=0, value=product["potongan"])
            stock = st.number_input("Stok", min_value=0, value=product["stock"])
            image_file = st.file_uploader("Upload Foto Produk Baru", type=["jpg", "png", "jpeg"])
            submit = st.form_submit_button("Update")

            if submit:
                product["name"] = name
                product["owner"] = owner
                product["reseller_price"] = reseller_price
                product["retail_price"] = retail_price
                product["potongan"] = potongan
                product["stock"] = stock
                if image_file:
                    product["image"] = image_file.read()
                st.success("Produk berhasil diupdate!")

# ----------------- MENU LAPORAN PENJUALAN -----------------
elif menu == "Laporan Penjualan":
    st.title("📊 Laporan Penjualan")
    if len(st.session_state.history) == 0:
        st.info("Belum ada transaksi.")
    else:
        all_data = []
        for transaksi in st.session_state.history:
            for item in transaksi:
                all_data.append(item)
        df = pd.DataFrame(all_data)

        laporan = df.groupby("owner").agg(
            total_qty=("qty", "sum"),
            penjualan_kotor=("subtotal", "sum"),
            total_potongan=("total_potongan", "sum")
        ).reset_index()
        laporan["penjualan_bersih"] = laporan["penjualan_kotor"] - laporan["total_potongan"]

        st.dataframe(laporan)

        # Grafik penjualan
        st.subheader("📈 Grafik Penjualan per Owner")
        fig, ax = plt.subplots()
        ax.bar(laporan["owner"], laporan["total_qty"])
        ax.set_xlabel("Owner")
        ax.set_ylabel("Total Qty Terjual")
        ax.set_title("Grafik Penjualan")
        st.pyplot(fig)

        # Export
        col1, col2 = st.columns(2)
        with col1:
            excel_data = export_excel(laporan)
            st.download_button("⬇️ Download Excel", data=excel_data, file_name="laporan_penjualan.xlsx")
        with col2:
            pdf_data = export_pdf(laporan)
            st.download_button("⬇️ Download PDF", data=pdf_data, file_name="laporan_penjualan.pdf")
