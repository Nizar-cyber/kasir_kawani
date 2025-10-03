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
def parse_int(value):
    try:
        return int(str(value).replace('.', '').replace('Rp','').replace(',',''))
    except:
        return 0

def load_produk():
    try:
        data = sheet_produk.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"Gagal ambil data produk: {e}")
        return pd.DataFrame()

def save_produk(df):
    try:
        sheet_produk.clear()
        sheet_produk.update([df.columns.values.tolist()] + df.values.tolist())
    except Exception as e:
        st.error(f"Gagal simpan produk: {e}")

def load_penjualan():
    try:
        data = sheet_penjualan.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"Gagal ambil laporan penjualan: {e}")
        return pd.DataFrame()

def save_penjualan(df):
    try:
        sheet_penjualan.clear()
        sheet_penjualan.update([df.columns.values.tolist()] + df.values.tolist())
    except Exception as e:
        st.error(f"Gagal simpan laporan penjualan: {e}")

# ================= STREAMLIT APP =================
st.set_page_config(page_title="Kasir Kawani", layout="wide")

# Load produk & penjualan ke session_state
if "produk_df" not in st.session_state:
    st.session_state.produk_df = load_produk()
if "penjualan_df" not in st.session_state:
    st.session_state.penjualan_df = load_penjualan()
if "cart" not in st.session_state:
    st.session_state.cart = []

menu = st.sidebar.radio("Menu", ["Kasir", "Daftar Produk", "Tambah Produk", "Edit Produk", "Hapus Produk", "Laporan Penjualan"])

# ================= KASIR =================
if menu == "Kasir":
    st.title("🛒 Kasir")
    produk_df = st.session_state.produk_df

    if produk_df.empty:
        st.warning("Belum ada produk di database.")
    else:
        for idx, row in produk_df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
            with col1:
                st.write(f"**{row['Nama Produk']}**")
                st.caption(f"Owner: {row['Owner']}")
            with col2:
                harga_retail = parse_int(row['Harga Retail'])
                st.write(f"Harga Retail: Rp{harga_retail:,}")
                st.write(f"Stock: {row['Stock']}")
            with col3:
                qty = st.number_input(f"Qty-{idx}", 1, int(row['Stock']), 1, key=f"qty{idx}")
            with col4:
                if st.button("Tambah", key=f"add{idx}"):
                    found = False
                    for item in st.session_state.cart:
                        if item["Nama Produk"] == row['Nama Produk']:
                            item["Qty"] += qty
                            item["Subtotal"] = item["Harga Jual"] * item["Qty"]
                            found = True
                            break
                    if not found:
                        st.session_state.cart.append({
                            "Nama Produk": row['Nama Produk'],
                            "Owner": row['Owner'],
                            "Harga Jual": harga_retail,
                            "Potongan": parse_int(row['Potongan']),
                            "Qty": qty,
                            "Subtotal": harga_retail * qty
                        })
                    st.success(f"{row['Nama Produk']} ditambahkan ke keranjang!")

    # Tampilkan keranjang
    st.subheader("Keranjang")
    if st.session_state.cart:
        hapus_index = None
        for i, item in enumerate(st.session_state.cart):
            col1, col2, col3 = st.columns([3,2,1])
            with col1:
                st.write(f"{item['Nama Produk']} ({item['Owner']})")
            with col2:
                new_qty = st.number_input(f"Edit Qty-{i}", 1, 1000, item['Qty'], key=f"editqty{i}")
                st.session_state.cart[i]['Qty'] = new_qty
                st.session_state.cart[i]['Subtotal'] = new_qty * item['Harga Jual']
            with col3:
                if st.button("Hapus", key=f"hapus{i}"):
                    hapus_index = i
        if hapus_index is not None:
            st.session_state.cart.pop(hapus_index)
            st.experimental_rerun()

        df_cart = pd.DataFrame(st.session_state.cart)
        st.dataframe(df_cart)

        total = sum([x["Subtotal"] for x in st.session_state.cart])
        st.write(f"### Total: Rp{int(total):,}")

        bayar = st.number_input("Nominal Pembayaran", min_value=0, step=1000)
        if st.button("Checkout"):
            if bayar >= total:
                kembalian = bayar - total
                st.success(f"Transaksi berhasil! Kembalian Rp{kembalian:,}")

                for item in st.session_state.cart:
                    new_row = {
                        "Waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Nama Produk": item["Nama Produk"],
                        "Owner": item["Owner"],
                        "Harga Jual": item["Harga Jual"],
                        "Potongan": item["Potongan"],
                        "Qty": item["Qty"],
                        "Subtotal": item["Subtotal"]
                    }
                    st.session_state.penjualan_df = pd.concat([st.session_state.penjualan_df, pd.DataFrame([new_row])], ignore_index=True)

                    # Update stock
                    idx_produk = produk_df[produk_df["Nama Produk"] == item["Nama Produk"]].index[0]
                    produk_df.at[idx_produk, "Stock"] = int(produk_df.at[idx_produk, "Stock"]) - item["Qty"]

                save_penjualan(st.session_state.penjualan_df)
                save_produk(produk_df)
                st.session_state.cart = []
                st.experimental_rerun()
            else:
                st.error("Nominal pembayaran kurang!")

# ================= DAFTAR PRODUK =================
elif menu == "Daftar Produk":
    st.title("📦 Daftar Produk")
    produk_df = st.session_state.produk_df
    st.dataframe(produk_df)

    st.download_button("Download Template Produk", 
        data=produk_df.to_csv(index=False).encode("utf-8"), 
        file_name="template_produk.csv", 
        mime="text/csv")

    uploaded_file = st.file_uploader("Upload Produk (CSV)", type=["csv"])
    if uploaded_file:
        new_df = pd.read_csv(uploaded_file)
        st.session_state.produk_df = new_df
        save_produk(new_df)
        st.success("Produk berhasil diupload.")

# ================= TAMBAH PRODUK =================
elif menu == "Tambah Produk":
    st.title("➕ Tambah Produk")
    produk_df = st.session_state.produk_df

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
            "Harga Reseller": harga_reseller, 
            "Harga Retail": harga_retail, 
            "Potongan": potongan,
            "Stock": stock
        }
        produk_df = pd.concat([produk_df, pd.DataFrame([new_row])], ignore_index=True)
        st.session_state.produk_df = produk_df
        save_produk(produk_df)
        st.success("Produk berhasil ditambahkan.")

# ================= EDIT PRODUK =================
elif menu == "Edit Produk":
    st.title("✏️ Edit Produk")
    produk_df = st.session_state.produk_df

    if not produk_df.empty:
        pilihan = st.selectbox("Pilih Produk", produk_df["Nama Produk"].unique())
        row = produk_df[produk_df["Nama Produk"] == pilihan].iloc[0]

        nama = st.text_input("Nama Produk", row["Nama Produk"])
        owner = st.text_input("Owner", row["Owner"])
        harga_reseller = st.number_input("Harga Reseller", min_value=0, value=int(row["Harga Reseller"]))
        harga_retail = st.number_input("Harga Retail", min_value=0, value=int(row["Harga Retail"]))
        potongan = st.number_input("Potongan", min_value=0, value=int(row["Potongan"]))
        stock = st.number_input("Stock", min_value=0, value=int(row["Stock"]))

        if st.button("Update Produk"):
            idx_produk = produk_df[produk_df["Nama Produk"] == pilihan].index[0]
            produk_df.at[idx_produk, "Nama Produk"] = nama
            produk_df.at[idx_produk, "Owner"] = owner
            produk_df.at[idx_produk, "Harga Reseller"] = harga_reseller
            produk_df.at[idx_produk, "Harga Retail"] = harga_retail
            produk_df.at[idx_produk, "Potongan"] = potongan
            produk_df.at[idx_produk, "Stock"] = stock
            st.session_state.produk_df = produk_df
            save_produk(produk_df)
            st.success("Produk berhasil diupdate.")

# ================= HAPUS PRODUK =================
elif menu == "Hapus Produk":
    st.title("🗑️ Hapus Produk")
    produk_df = st.session_state.produk_df

    if not produk_df.empty:
        pilihan = st.selectbox("Pilih Produk", produk_df["Nama Produk"].unique())
        if st.button("Hapus"):
            produk_df = produk_df[produk_df["Nama Produk"] != pilihan]
            st.session_state.produk_df = produk_df
            save_produk(produk_df)
            st.success("Produk berhasil dihapus.")

# ================= LAPORAN PENJUALAN =================
elif menu == "Laporan Penjualan":
    st.title("📊 Laporan Penjualan")
    laporan_df = st.session_state.penjualan_df

    if not laporan_df.empty:
        laporan_df["Total Harga Jual"] = laporan_df["Harga Jual"] * laporan_df["Qty"]
        laporan_df["Total Potongan"] = laporan_df["Potongan"] * laporan_df["Qty"]
        laporan_df["Laba Bersih"] = laporan_df["Total Harga Jual"] - laporan_df["Total Potongan"]

        st.dataframe(laporan_df)

        total_harga_jual = laporan_df["Total Harga Jual"].sum()
        total_potongan = laporan_df["Total Potongan"].sum()
        total_laba = laporan_df["Laba Bersih"].sum()

        st.write(f"**Total Harga Jual:** Rp{total_harga_jual:,}")
        st.write(f"**Total Potongan:** Rp{total_potongan:,}")
        st.write(f"**Total Laba Bersih:** Rp{total_laba:,}")

        # Export Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            laporan_df.to_excel(writer, index=False, sheet_name="Laporan")
        st.download_button("Download Excel", data=output.getvalue(), file_name="laporan_penjualan.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # Export PDF
        pdf_output = BytesIO()
        doc = SimpleDocTemplate(pdf_output, pagesize=A4)
        styles = getSampleStyleSheet()
        table_data = [laporan_df.columns.tolist()] + laporan_df.values.tolist()
        table = Table(table_data)
        table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.grey),
                                   ("GRID", (0,0), (-1,-1), 1, colors.black)]))
        doc.build([Paragraph("Laporan Penjualan", styles["Title"]), table])
        st.download_button("Download PDF", data=pdf_output.getvalue(), file_name="laporan_penjualan.pdf", mime="application/pdf")
