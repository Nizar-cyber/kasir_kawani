import streamlit as st
import pandas as pd
import base64
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt

st.set_page_config(page_title="Kasir App", layout="wide")

# ----------------- DATA AWAL -----------------
if "products" not in st.session_state:
    st.session_state.products = [
        {"Owner": "Bu.Ilah", "Nama Produk": "Kacang Bawang", "Harga Reseller": 18000, "Harga Retail": 20000, "Potongan": 2000, "Stock": 10},
        {"Owner": "Bu.Ilah", "Nama Produk": "Stik Balado", "Harga Reseller": 25000, "Harga Retail": 28000, "Potongan": 3000, "Stock": 8},
        {"Owner": "Pak.Andi", "Nama Produk": "Keripik Pisang", "Harga Reseller": 15000, "Harga Retail": 17000, "Potongan": 2000, "Stock": 12},
        {"Owner": "Pak.Andi", "Nama Produk": "Sale Pisang", "Harga Reseller": 22000, "Harga Retail": 25000, "Potongan": 3000, "Stock": 6},
    ]

if "cart" not in st.session_state:
    st.session_state.cart = []

if "history" not in st.session_state:
    st.session_state.history = []  # transaksi tersimpan di sini

# ----------------- SIDEBAR -----------------
menu = st.sidebar.radio("📌 Menu", ["Kasir", "Daftar Produk", "Tambah Produk", "Edit Produk", "Laporan Penjualan"])

# ----------------- FUNGSI -----------------
def add_to_cart(product, qty):
    if product["Stock"] >= qty:
        found = False
        for item in st.session_state.cart:
            if item["Nama Produk"] == product["Nama Produk"] and item["Owner"] == product["Owner"]:
                item["qty"] += qty
                found = True
                break
        if not found:
            st.session_state.cart.append({
                "name": product["Nama Produk"],
                "owner": product["Owner"],
                "price": product["Harga Retail"],
                "potongan": product["Potongan"],
                "qty": qty
            })
        st.success(f"{product['Nama Produk']} ditambahkan ke keranjang")
    else:
        st.error("Stok tidak mencukupi!")

def checkout():
    if len(st.session_state.cart) == 0:
        st.warning("Keranjang kosong!")
        return

    total = sum(item["price"] * item["qty"] for item in st.session_state.cart)

    st.subheader("💵 Pembayaran")
    pembayaran = st.number_input("Masukkan Nominal Pembayaran", min_value=0, step=1000, key="pay_input")

    if st.button("Proses Checkout"):
        if pembayaran < total:
            st.error("Uang tidak cukup!")
            return

        transaksi = []
        for item in st.session_state.cart:
            subtotal = item["price"] * item["qty"]
            transaksi.append({
                "name": item["name"],
                "owner": item["owner"],
                "qty": item["qty"],
                "price": item["price"],
                "potongan": item["potongan"],
                "subtotal": subtotal
            })

            # kurangi stok
            for p in st.session_state.products:
                if p["Nama Produk"] == item["name"] and p["Owner"] == item["owner"]:
                    p["Stock"] -= item["qty"]

        kembalian = pembayaran - total

        st.session_state.history.append({
            "timestamp": pd.Timestamp.now(),
            "items": transaksi,
            "total": total,
            "pembayaran": pembayaran,
            "kembalian": kembalian
        })
        st.session_state.cart = []
        st.success(f"Checkout berhasil! Total: Rp{total:,}, Pembayaran: Rp{pembayaran:,}, Kembalian: Rp{kembalian:,}")

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
    c.drawString(200, height - 50, "Laporan Penjualan")

    c.setFont("Helvetica", 10)
    y = height - 100
    for idx, row in df.iterrows():
        text = f"{row['Owner']} - {row['Nama Produk']} | Qty: {row['Qty Terjual']} | Gross: Rp{row['Gross Income']:,} | Net: Rp{row['Net Income']:,}"
        c.drawString(50, y, text)
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50
    c.save()
    return buffer.getvalue()

# ----------------- MENU -----------------
if menu == "Kasir":
    st.title("🛒 Kasir")

    # tampil grid produk
    cols = st.columns(4)
    for idx, product in enumerate(st.session_state.products):
        with cols[idx % 4]:
            with st.container():
                st.markdown(f"**{product['Nama Produk']}**")
                st.write(f"Owner: {product['Owner']}")
                st.write(f"Harga: Rp{product['Harga Retail']:,}")
                st.write(f"Stok: {product['Stock']}")
                qty = st.number_input(
                    f"Qty_{idx}", min_value=1, max_value=product["Stock"], value=1, key=f"qty_{idx}"
                )
                if st.button(f"Tambah ({product['Nama Produk']})", key=f"btn_{idx}"):
                    add_to_cart(product, qty)
            st.markdown("---")

    st.subheader("Keranjang")
    if len(st.session_state.cart) == 0:
        st.info("Keranjang kosong")
    else:
        total = 0
        for item in st.session_state.cart:
            subtotal = item["price"] * item["qty"]
            total += subtotal
            st.write(f"{item['name']} ({item['owner']}) x{item['qty']} - Rp{subtotal:,}")
            if st.button(f"Hapus {item['name']}", key=f"del_{item['name']}"):
                st.session_state.cart.remove(item)
                st.rerun()
        st.write(f"### Total: Rp{total:,}")
        checkout()

elif menu == "Daftar Produk":
    st.title("📦 Daftar Produk")
    df = pd.DataFrame(st.session_state.products)
    st.dataframe(df)

elif menu == "Tambah Produk":
    st.title("➕ Tambah Produk")
    with st.form("add_product"):
        owner = st.text_input("Owner")
        name = st.text_input("Nama Produk")
        reseller_price = st.number_input("Harga Reseller", min_value=0)
        retail_price = st.number_input("Harga Retail", min_value=0)
        stock = st.number_input("Stok", min_value=0)
        submit = st.form_submit_button("Simpan")

        if submit:
            st.session_state.products.append({
                "Owner": owner,
                "Nama Produk": name,
                "Harga Reseller": reseller_price,
                "Harga Retail": retail_price,
                "Potongan": retail_price - reseller_price,
                "Stock": stock
            })
            st.success("Produk berhasil ditambahkan!")

elif menu == "Edit Produk":
    st.title("✏️ Edit Produk")
    product_names = [f"{p['Nama Produk']} ({p['Owner']})" for p in st.session_state.products]
    selected = st.selectbox("Pilih Produk", product_names)
    product = next((p for p in st.session_state.products if f"{p['Nama Produk']} ({p['Owner']})" == selected), None)

    if product:
        with st.form("edit_product"):
            owner = st.text_input("Owner", product["Owner"])
            name = st.text_input("Nama Produk", product["Nama Produk"])
            reseller_price = st.number_input("Harga Reseller", min_value=0, value=product["Harga Reseller"])
            retail_price = st.number_input("Harga Retail", min_value=0, value=product["Harga Retail"])
            stock = st.number_input("Stok", min_value=0, value=product["Stock"])
            submit = st.form_submit_button("Update")

            if submit:
                product["Owner"] = owner
                product["Nama Produk"] = name
                product["Harga Reseller"] = reseller_price
                product["Harga Retail"] = retail_price
                product["Potongan"] = retail_price - reseller_price
                product["Stock"] = stock
                st.success("Produk berhasil diupdate!")

elif menu == "Laporan Penjualan":
    st.title("📊 Laporan Penjualan")
    if len(st.session_state.history) == 0:
        st.info("Belum ada transaksi.")
    else:
        all_data = []
        for trx in st.session_state.history:
            for item in trx["items"]:
                all_data.append({
                    "Timestamp": trx["timestamp"],
                    "Owner": item["owner"],
                    "Nama Produk": item["name"],
                    "Qty Terjual": item["qty"],
                    "Gross Income": item["price"] * item["qty"],
                    "Net Income": (item["price"] - item["potongan"]) * item["qty"]
                })
        df = pd.DataFrame(all_data)
        st.dataframe(df)

        # Grafik penjualan
        st.subheader("📈 Grafik Penjualan per Owner")
        fig, ax = plt.subplots()
        df_group = df.groupby("Owner")["Qty Terjual"].sum()
        ax.bar(df_group.index, df_group.values)
        st.pyplot(fig)

        # Export
        col1, col2 = st.columns(2)
        with col1:
            excel_data = export_excel(df)
            st.download_button("⬇️ Download Excel", data=excel_data, file_name="laporan_penjualan.xlsx")
        with col2:
            pdf_data = export_pdf(df)
            st.download_button("⬇️ Download PDF", data=pdf_data, file_name="laporan_penjualan.pdf")

        # Upload/Download produk template
        st.subheader("📤 Upload/Download Produk Excel")
        template = pd.DataFrame([{"Owner":"", "Nama Produk":"", "Harga Reseller":0, "Harga Retail":0, "Stock":0}])
        st.download_button("⬇️ Download Template Produk", data=template.to_csv(index=False).encode("utf-8"),
                           file_name="template_produk.csv", mime="text/csv")
        uploaded = st.file_uploader("Upload Produk (Excel/CSV)", type=["csv", "xlsx"])
        if uploaded:
            if uploaded.name.endswith(".csv"):
                df_new = pd.read_csv(uploaded)
            else:
                df_new = pd.read_excel(uploaded)
            for _, row in df_new.iterrows():
                st.session_state.products.append({
                    "Owner": row["Owner"],
                    "Nama Produk": row["Nama Produk"],
                    "Harga Reseller": int(row["Harga Reseller"]),
                    "Harga Retail": int(row["Harga Retail"]),
                    "Potongan": int(row["Harga Retail"] - row["Harga Reseller"]),
                    "Stock": int(row["Stock"])
                })
            st.success("Produk berhasil diupload!")
