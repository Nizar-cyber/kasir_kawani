import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Kasir App", layout="wide")

# ----------------- SESSION STATE -----------------
if "products" not in st.session_state:
    st.session_state.products = [
        {"owner": "Toko A", "nama": "Produk A", "harga_retail": 10000, "potongan": 1000, "stok": 50},
        {"owner": "Toko B", "nama": "Produk B", "harga_retail": 20000, "potongan": 2000, "stok": 30},
        {"owner": "Toko C", "nama": "Produk C", "harga_retail": 15000, "potongan": 1500, "stok": 40},
        {"owner": "Toko D", "nama": "Produk D", "harga_retail": 30000, "potongan": 2500, "stok": 20},
    ]

if "cart" not in st.session_state:
    st.session_state.cart = []

if "history" not in st.session_state:
    st.session_state.history = []  # untuk laporan penjualan

# ----------------- FUNGSI -----------------
def create_pdf(cart_df, total):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(200, height - 50, "Struk Pembelian")

    c.setFont("Helvetica", 10)
    y = height - 100
    for _, row in cart_df.iterrows():
        line = f"{row['nama']} ({row['qty']} x {row['harga_final']}) = {row['subtotal']}"
        c.drawString(50, y, line)
        y -= 20
    c.drawString(50, y - 30, f"Total: Rp {total:,}")
    c.save()

    buffer.seek(0)
    return buffer

def download_template():
    template = pd.DataFrame(columns=["owner", "nama", "harga_retail", "potongan", "stok"])
    towrite = BytesIO()
    template.to_excel(towrite, index=False)
    towrite.seek(0)
    return towrite

# ----------------- TAMPILAN -----------------
st.title("🛒 Kasir")

# === Grid Produk (4 kolom per baris) ===
st.subheader("Daftar Produk")
cols = st.columns(4)
for i, product in enumerate(st.session_state.products):
    col = cols[i % 4]
    with col:
        with st.container():
            st.markdown(f"**{product['nama']}**")
            st.write(f"👤 Owner: {product['owner']}")
            st.write(f"💰 Harga: Rp{product['harga_retail']:,}")
            st.write(f"🔖 Potongan: Rp{product['potongan']:,}")
            st.write(f"📦 Stok: {product['stok']}")
            qty = st.number_input(f"Qty_{i}", min_value=1, max_value=product["stok"], value=1, key=f"qty_{i}")
            if st.button(f"Tambah {product['nama']}", key=f"btn_{i}"):
                harga_final = product["harga_retail"] - product["potongan"]
                subtotal = harga_final * qty
                st.session_state.cart.append({
                    "owner": product["owner"],
                    "nama": product["nama"],
                    "harga_retail": product["harga_retail"],
                    "potongan": product["potongan"],
                    "harga_final": harga_final,
                    "qty": qty,
                    "subtotal": subtotal
                })
                st.success(f"{product['nama']} ditambahkan ke keranjang!")

    if (i + 1) % 4 == 0 and i != len(st.session_state.products) - 1:
        cols = st.columns(4)

# === Keranjang ===
if st.session_state.cart:
    st.subheader("Keranjang Belanja")
    cart_df = pd.DataFrame(st.session_state.cart)
    st.dataframe(cart_df)

    total = cart_df["subtotal"].sum()
    st.write(f"### 💰 Total: Rp {total:,}")

    # Checkout
    if st.button("✅ Checkout"):
        # simpan transaksi ke history
        st.session_state.history.append(cart_df.to_dict("records"))
        # kurangi stok
        for item in st.session_state.cart:
            for p in st.session_state.products:
                if p["nama"] == item["nama"] and p["owner"] == item["owner"]:
                    p["stok"] -= item["qty"]
        st.session_state.cart = []
        st.success("Checkout berhasil, stok sudah berkurang!")

    # Download PDF
    pdf_file = create_pdf(cart_df, total)
    st.download_button(
        "🧾 Download Struk (PDF)",
        data=pdf_file,
        file_name="struk.pdf",
        mime="application/pdf"
    )

# === Download Template Produk & Upload Produk ===
st.subheader("📥 Download / Upload Produk")
col1, col2 = st.columns(2)

with col1:
    st.download_button(
        label="📥 Download Template Produk (Excel)",
        data=download_template(),
        file_name="template_produk.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

with col2:
    uploaded_file = st.file_uploader("📤 Upload Produk (Excel)", type=["xlsx"])
    if uploaded_file:
        df_upload = pd.read_excel(uploaded_file)
        for _, row in df_upload.iterrows():
            st.session_state.products.append({
                "owner": row["owner"],
                "nama": row["nama"],
                "harga_retail": row["harga_retail"],
                "potongan": row["potongan"],
                "stok": row["stok"]
            })
        st.success("Produk berhasil ditambahkan dari Excel!")
