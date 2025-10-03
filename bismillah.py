import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

# ================= HELPER FUNCTIONS =================
def parse_rp(value):
    """Ubah string 'Rp18.000' jadi integer 18000"""
    if isinstance(value, str):
        value = value.replace("Rp", "").replace(".", "").replace(",", "").strip()
    try:
        return int(value)
    except:
        return 0

# ================= GOOGLE SHEET SETUP =================
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    CLIENT = gspread.authorize(creds)

    SHEET_ID = "1ksV8WUxNLleiyAv9FbpLUqgIQ3Njt-_HNTshfSEDVS4"
    sheet_produk = CLIENT.open_by_key(SHEET_ID).worksheet("Produk")
    sheet_penjualan = CLIENT.open_by_key(SHEET_ID).worksheet("Penjualan")

except Exception as e:
    st.error(f"Gagal konek ke Google Sheet. Pastikan credential JSON benar dan sheet sudah dishare ke service account. Error: {e}")
    st.stop()

# ================= HELPER FUNCTIONS SHEET =================
def load_produk():
    data = sheet_produk.get_all_records()
    df = pd.DataFrame(data)
    # Bersihkan harga
    for col in ["Harga Reseller", "Harga Retail", "Potongan", "Stock"]:
        if col in df.columns:
            df[col] = df[col].apply(parse_rp)
    return df

def save_produk(df):
    sheet_produk.clear()
    sheet_produk.update([df.columns.values.tolist()] + df.values.tolist())

def load_penjualan():
    data = sheet_penjualan.get_all_records()
    df = pd.DataFrame(data)
    return df

def save_penjualan(df):
    sheet_penjualan.clear()
    sheet_penjualan.update([df.columns.values.tolist()] + df.values.tolist())

# ================= STREAMLIT APP =================
st.set_page_config(page_title="Kasir Kawani", layout="wide")

if "cart" not in st.session_state:
    st.session_state.cart = []

menu = st.sidebar.radio("Menu", ["Kasir", "Daftar Produk", "Tambah Produk", "Edit Produk", "Hapus Produk", "Laporan Penjualan"])

# ================= KASIR =================
if menu == "Kasir":
    st.title("🛒 Kasir")
    produk_df = load_produk()
    
    if produk_df.empty:
        st.warning("Belum ada produk di database.")
    else:
        # Tampilkan produk
        for idx, row in produk_df.iterrows():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            harga_retail = parse_rp(row['Harga Retail'])
            with col1:
                st.write(f"**{row['Nama Produk']}**")
                st.caption(f"Owner: {row['Owner']}")
            with col2:
                st.write(f"Harga Retail: Rp{harga_retail:,}")
                st.write(f"Stock: {row['Stock']}")
            with col3:
                qty = st.number_input(f"Qty-{idx}", 1, row['Stock'], 1, key=f"qty{idx}")
            with col4:
                if st.button("Tambah", key=f"add{idx}"):
                    # Cek apakah sudah ada di cart
                    exists = False
                    for item in st.session_state.cart:
                        if item["Nama Produk"] == row["Nama Produk"]:
                            item["Qty"] += qty
                            item["Subtotal"] = item["Harga Jual"] * item["Qty"]
                            exists = True
                            break
                    if not exists:
                        st.session_state.cart.append({
                            "Nama Produk": row['Nama Produk'],
                            "Owner": row['Owner'],
                            "Harga Jual": harga_retail,
                            "Qty": qty,
                            "Subtotal": harga_retail * qty
                        })
                    st.success(f"{row['Nama Produk']} ditambahkan ke keranjang!")

        # Tampilkan keranjang
        st.subheader("Keranjang")
        if st.session_state.cart:
            df_cart = pd.DataFrame(st.session_state.cart)

            # Edit / hapus item di keranjang
            for i, item in enumerate(st.session_state.cart):
                cols = st.columns([3,2,2])
                cols[0].write(f"**{item['Nama Produk']}** - Rp{item['Harga Jual']:,}")
                cols[1].number_input(f"Qty Cart-{i}", min_value=1, value=item['Qty'], key=f"cart_qty_{i}", on_change=lambda idx=i: st.session_state.cart[idx].update({"Qty": st.session_state[f"cart_qty_{idx}"], "Subtotal": st.session_state[f"cart_qty_{idx}"]*st.session_state.cart[idx]["Harga Jual"]}))
                if cols[2].button("Hapus", key=f"cart_del_{i}"):
                    st.session_state.cart.pop(i)
                    st.experimental_rerun()

            st.table(pd.DataFrame(st.session_state.cart))
            total = sum([x["Subtotal"] for x in st.session_state.cart])
            st.write(f"### Total: Rp{total:,}")

            bayar = st.number_input("Nominal Pembayaran", min_value=0, step=1000)
            if st.button("Checkout"):
                if bayar >= total:
                    kembalian = bayar - total
                    st.success(f"Transaksi berhasil! Kembalian Rp{kembalian:,}")

                    # Simpan ke laporan penjualan & update stock
                    penjualan_df = load_penjualan()
                    for item in st.session_state.cart:
                        new_row = {
                            "Waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Nama Produk": item["Nama Produk"],
                            "Owner": item["Owner"],
                            "Harga Jual": item["Harga Jual"],
                            "Qty": item["Qty"],
                            "Subtotal": item["Subtotal"]
                        }
                        penjualan_df = pd.concat([penjualan_df, pd.DataFrame([new_row])], ignore_index=True)

                        # Update stock produk
                        idx_produk = produk_df[produk_df["Nama Produk"] == item["Nama Produk"]].index[0]
                        produk_df.at[idx_produk, "Stock"] -= item["Qty"]

                    save_penjualan(penjualan_df)
                    save_produk(produk_df)
                    st.session_state.cart = []
                else:
                    st.error("Nominal pembayaran kurang!")

# ================= DAFTAR PRODUK =================
elif menu == "Daftar Produk":
    st.title("📦 Daftar Produk")
    produk_df = load_produk()
    st.dataframe(produk_df)

    st.download_button("Download Template Produk", 
        data=produk_df.to_csv(index=False).encode("utf-8"), 
        file_name="template_produk.csv", 
        mime="text/csv")

    uploaded_file = st.file_uploader("Upload Produk (CSV)", type=["csv"])
    if uploaded_file:
        new_df = pd.read_csv(uploaded_file)
        save_produk(new_df)
        st.success("Produk berhasil diupload.")

# ================= TAMBAH PRODUK =================
elif menu == "Tambah Produk":
    st.title("➕ Tambah Produk")
    produk_df = load_produk()

    nama = st.text_input("Nama Produk")
    owner = st.text_input("Owner")
    harga_reseller = st.number_input("Harga Reseller", min_value=0)
    harga_retail = st.number_input("Harga Retail", min_value=0)
    potongan = st.number_input("Potongan", min_value=0)
    stock = st.number_input("Stock", min_value=0)

    if st.button("Simpan Produk"):
        new_row = {
            "Owner": owner, 
            "Nama Produk": nama, 
            "Harga Reseller": harga_resell_
