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

# ================= HELPER FUNCTIONS =================
def parse_rupiah(x):
    """Konversi string 'Rp20.000' menjadi integer 20000"""
    if pd.isna(x):
        return 0
    return int(str(x).replace("Rp", "").replace(".", "").strip())

@st.cache_data(ttl=60)  # cache data 60 detik
def load_produk():
    data = sheet_produk.get_all_records()
    df = pd.DataFrame(data)
    for col in ["Harga Reseller", "Harga Retail", "Potongan"]:
        if col in df.columns:
            df[col] = df[col].apply(parse_rupiah)
    return df

def save_produk(df):
    df_to_save = df.copy()
    for col in ["Harga Reseller", "Harga Retail", "Potongan"]:
        if col in df_to_save.columns:
            df_to_save[col] = df_to_save[col].apply(lambda x: f"Rp{int(x):,}".replace(",", "."))
    sheet_produk.clear()
    sheet_produk.update([df_to_save.columns.values.tolist()] + df_to_save.values.tolist())

@st.cache_data(ttl=60)
def load_penjualan():
    data = sheet_penjualan.get_all_records()
    df = pd.DataFrame(data)
    for col in ["Harga Jual", "Subtotal"]:
        if col in df.columns:
            df[col] = df[col].apply(parse_rupiah)
    return df

def save_penjualan(df):
    df_to_save = df.copy()
    for col in ["Harga Jual", "Subtotal"]:
        if col in df_to_save.columns:
            df_to_save[col] = df_to_save[col].apply(lambda x: f"Rp{int(x):,}".replace(",", "."))
    sheet_penjualan.clear()
    sheet_penjualan.update([df_to_save.columns.values.tolist()] + df_to_save.values.tolist())

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
        for idx, row in produk_df.iterrows():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            with col1:
                st.write(f"**{row['Nama Produk']}**")
                st.caption(f"Owner: {row['Owner']}")
            with col2:
                st.write(f"Harga Retail: Rp{row['Harga Retail']:,}")
                st.write(f"Stock: {row['Stock']}")
            with col3:
                max_qty = int(row['Stock'])
                if max_qty <= 0:
                    st.write("Stok Habis")
                    qty = 0
                else:
                    qty = st.number_input(f"Qty-{idx}", 1, max_qty, 1, key=f"qty{idx}")
            with col4:
                if st.button("Tambah", key=f"add{idx}") and qty > 0:
                    st.session_state.cart.append({
                        "Nama Produk": row['Nama Produk'],
                        "Owner": row['Owner'],
                        "Harga Jual": row['Harga Retail'],
                        "Qty": qty,
                        "Subtotal": row['Harga Retail'] * qty
                    })
                    # langsung kurangi stock di sheet
                    produk_df.at[idx, "Stock"] -= qty
                    save_produk(produk_df)
                    st.success(f"{row['Nama Produk']} ditambahkan ke keranjang! Stok berkurang {qty}.")

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
    harga_reseller = st.text_input("Harga Reseller (contoh: Rp8.000)")
    harga_retail = st.text_input("Harga Retail (contoh: Rp10.000)")
    potongan = st.text_input("Potongan (contoh: Rp2000)")
    stock = st.number_input("Stock", min_value=0)

    if st.button("Simpan Produk"):
        new_row = {
            "Owner": owner,
            "Nama Produk": nama,
            "Harga Reseller": parse_rupiah(harga_reseller),
            "Harga Retail": parse_rupiah(harga_retail),
            "Potongan": parse_rupiah(potongan),
            "Stock": stock
        }
        produk_df = pd.concat([produk_df, pd.DataFrame([new_row])], ignore_index=True)
        save_produk(produk_df)
        st.success("Produk berhasil ditambahkan.")

# ================= EDIT PRODUK =================
elif menu == "Edit Produk":
    st.title("✏️ Edit Produk")
    produk_df = load_produk()

    if not produk_df.empty:
        pilihan = st.selectbox("Pilih Produk", produk_df["Nama Produk"].unique())
        row = produk_df[produk_df["Nama Produk"] == pilihan].iloc[0]

        nama = st.text_input("Nama Produk", row["Nama Produk"])
        owner = st.text_input("Owner", row["Owner"])
        harga_reseller = st.text_input("Harga Reseller", f"Rp{row['Harga Reseller']:,}".replace(",", "."))
        harga_retail = st.text_input("Harga Retail", f"Rp{row['Harga Retail']:,}".replace(",", "."))
        potongan = st.text_input("Potongan", f"Rp{row['Potongan']:,}".replace(",", "."))
        stock = st.number_input("Stock", min_value=0, value=int(row["Stock"]))

        if st.button("Update Produk"):
            idx_produk = produk_df[produk_df["Nama Produk"] == pilihan].index[0]
            produk_df.at[idx_produk, "Nama Produk"] = nama
            produk_df.at[idx_produk, "Owner"] = owner
            produk_df.at[idx_produk, "Harga Reseller"] = parse_rupiah(harga_reseller)
            produk_df.at[idx_produk, "Harga Retail"] = parse_rupiah(harga_retail)
            produk_df.at[idx_produk, "Potongan"] = parse_rupiah(potongan)
            produk_df.at[idx_produk, "Stock"] = stock
