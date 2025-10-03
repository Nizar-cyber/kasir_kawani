import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Kasir App", layout="wide")

# ----------------- SESSION STATE -----------------
if "products" not in st.session_state:
    st.session_state.products = []
if "cart" not in st.session_state:
    st.session_state.cart = []
if "laporan" not in st.session_state:
    st.session_state.laporan = []

# ----------------- EXPORT FUNCTIONS -----------------
def export_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Laporan Penjualan")
    return output.getvalue()

def export_pdf(df):
    output = BytesIO()
    c = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica", 10)
    text = c.beginText(40, height - 40)
    text.textLine("Laporan Penjualan")
    text.textLine("")

    for i, row in df.iterrows():
        line = f"{row['Timestamp']} | {row['Owner']} | {row['Nama Produk']} | Qty:{row['Qty']} | Rp{row['Subtotal']}"
        text.textLine(line)
    c.drawText(text)
    c.showPage()
    c.save()
    return output.getvalue()

def download_template():
    df_template = pd.DataFrame({
        "Owner": ["contoh_owner"],
        "Nama Produk": ["Produk Contoh"],
        "Harga Retail": [10000],
        "Potongan": [1000],
        "Stock": [10]
    })
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_template.to_excel(writer, index=False, sheet_name="Template Produk")
    return output.getvalue()

# ----------------- SIDEBAR MENU -----------------
menu = st.sidebar.radio(
    "Menu",
    ["Kasir", "Daftar Produk", "Tambah Produk", "Edit Produk", "Laporan Penjualan"]
)

# ----------------- MENU KASIR -----------------
if menu == "Kasir":
    st.title("💰 Kasir")

    if st.session_state.products:
        cols = st.columns(4)  # tampilkan grid 4 kolom
        for idx, product in enumerate(st.session_state.products):
            with cols[idx % 4]:
                st.markdown(f"**{product['Nama Produk']}**")
                st.write(f"Owner: {product['Owner']}")
                st.write(f"Harga: Rp{product['Harga Retail']}")
                st.write(f"Stock: {product['Stock']}")
                qty = st.number_input(f"Qty {product['Nama Produk']}", min_value=0, max_value=product["Stock"], key=f"qty_{idx}")
                if st.button(f"Tambah {product['Nama Produk']}", key=f"btn_{idx}"):
                    if qty > 0:
                        st.session_state.cart.append({
                            "Owner": product["Owner"],
                            "Nama Produk": product["Nama Produk"],
                            "Harga Retail": product["Harga Retail"],
                            "Potongan": product["Potongan"],
                            "Qty": qty
                        })
                        st.success(f"{qty} {product['Nama Produk']} ditambahkan ke keranjang!")

    if st.session_state.cart:
        st.subheader("🛒 Keranjang Belanja")
        df_cart = pd.DataFrame(st.session_state.cart)
        df_cart["Subtotal"] = df_cart["Harga Retail"] * df_cart["Qty"] - df_cart["Potongan"] * df_cart["Qty"]
        st.table(df_cart)
        total = df_cart["Subtotal"].sum()
        st.write(f"### Total: Rp{total}")

        if st.button("Checkout"):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            laporan = []
            for item in st.session_state.cart:
                # kurangi stock
                for p in st.session_state.products:
                    if p["Nama Produk"] == item["Nama Produk"] and p["Owner"] == item["Owner"]:
                        p["Stock"] -= item["Qty"]

                laporan.append({
                    "Owner": item["Owner"],
                    "Nama Produk": item["Nama Produk"],
                    "Harga Retail": item["Harga Retail"],
                    "Potongan": item["Potongan"],
                    "Qty": item["Qty"],
                    "Subtotal": item["Harga Retail"] * item["Qty"] - item["Potongan"] * item["Qty"],
                    "Timestamp": timestamp
                })

            df_laporan = pd.DataFrame(laporan)
            st.session_state.laporan.append(df_laporan)
            st.session_state.cart = []
            st.success("Checkout berhasil!")

# ----------------- MENU DAFTAR PRODUK -----------------
elif menu == "Daftar Produk":
    st.title("📦 Daftar Produk")
    if st.session_state.products:
        df_produk = pd.DataFrame(st.session_state.products)
        st.table(df_produk)
    else:
        st.info("Belum ada produk.")

# ----------------- MENU TAMBAH PRODUK -----------------
elif menu == "Tambah Produk":
    st.title("➕ Tambah Produk")

    with st.form("form_tambah"):
        owner = st.text_input("Owner")
        nama_produk = st.text_input("Nama Produk")
        harga = st.number_input("Harga Retail", min_value=0)
        potongan = st.number_input("Potongan", min_value=0)
        stock = st.number_input("Stock", min_value=0)
        submitted = st.form_submit_button("Tambah")

        if submitted:
            st.session_state.products.append({
                "Owner": owner,
                "Nama Produk": nama_produk,
                "Harga Retail": harga,
                "Potongan": potongan,
                "Stock": stock
            })
            st.success(f"Produk {nama_produk} berhasil ditambahkan!")

    # upload Excel
    st.subheader("📤 Upload Produk dari Excel")
    file = st.file_uploader("Upload file Excel", type=["xlsx"])
    if file:
        df_upload = pd.read_excel(file)
        st.session_state.products.extend(df_upload.to_dict(orient="records"))
        st.success("Produk dari Excel berhasil ditambahkan!")

    # download template
    st.subheader("📥 Download Template Excel")
    st.download_button(
        label="Download Template Produk",
        data=download_template(),
        file_name="template_produk.xlsx"
    )

# ----------------- MENU EDIT PRODUK -----------------
# ----------------- MENU EDIT PRODUK -----------------
elif menu == "Edit Produk":
    st.title("✏️ Edit Produk")
    if st.session_state.products:
        pilihan = [p["Nama Produk"] for p in st.session_state.products]
        pilih = st.selectbox("Pilih Produk", pilihan)
        produk = next(p for p in st.session_state.products if p["Nama Produk"] == pilih)

        with st.form("form_edit"):
            produk["Owner"] = st.text_input("Owner", produk["Owner"])
            produk["Nama Produk"] = st.text_input("Nama Produk", produk["Nama Produk"])
            produk["Harga Retail"] = st.number_input("Harga Retail", min_value=0, value=produk["Harga Retail"])
            produk["Potongan"] = st.number_input("Potongan", min_value=0, value=produk["Potongan"])
            produk["Stock"] = st.number_input("Stock", min_value=0, value=produk["Stock"])
            col1, col2 = st.columns(2)

            with col1:
                updated = st.form_submit_button("Update")
            with col2:
                deleted = st.form_submit_button("Hapus Produk")

            if updated:
                st.success("Produk berhasil diupdate!")
            if deleted:
                st.session_state.products = [p for p in st.session_state.products if p["Nama Produk"] != pilih]
                st.warning(f"Produk {pilih} telah dihapus!")
    else:
        st.info("Belum ada produk untuk diedit.")

# ----------------- MENU LAPORAN PENJUALAN -----------------
elif menu == "Laporan Penjualan":
    st.title("📑 Laporan Penjualan")
    if st.session_state.laporan:
        df_laporan_all = pd.concat(st.session_state.laporan, ignore_index=True)
        st.dataframe(df_laporan_all)

        st.download_button(
            label="Download Excel",
            data=export_excel(df_laporan_all),
            file_name="laporan_penjualan.xlsx"
        )

        st.download_button(
            label="Download PDF",
            data=export_pdf(df_laporan_all),
            file_name="laporan_penjualan.pdf"
        )
    else:
        st.info("Belum ada transaksi.")
