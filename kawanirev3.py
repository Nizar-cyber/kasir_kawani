import streamlit as st
import pandas as pd
import base64
from io import BytesIO
import matplotlib.pyplot as plt

st.set_page_config(page_title="Kasir App", layout="wide")

# ----------------- SESSION STATE -----------------
if "products" not in st.session_state:
    st.session_state.products = [
        {"SKU": "SKU001", "Nama Produk": "Produk A", "Harga Jual": 10000, "Owner": "Owner1"},
        {"SKU": "SKU002", "Nama Produk": "Produk B", "Harga Jual": 15000, "Owner": "Owner1"},
        {"SKU": "SKU003", "Nama Produk": "Produk C", "Harga Jual": 20000, "Owner": "Owner2"},
    ]

if "cart" not in st.session_state:
    st.session_state.cart = []

if "report" not in st.session_state:
    st.session_state.report = []


# ----------------- FUNGSI TEMPLATE EXCEL -----------------
def download_template_excel():
    df_template = pd.DataFrame({
        "SKU": ["SKU001", "SKU002"],
        "Nama Produk": ["Produk Contoh A", "Produk Contoh B"],
        "Harga Jual": [10000, 20000],
        "Owner": ["Owner1", "Owner2"]
    })

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_template.to_excel(writer, index=False, sheet_name="Template Produk")

    return buffer.getvalue()


# ----------------- MENU -----------------
menu = st.sidebar.radio("Menu", ["Kasir", "List Produk", "Laporan Penjualan"])

# ----------------- KASIR -----------------
if menu == "Kasir":
    st.subheader("Kasir")

    if not st.session_state.products:
        st.warning("Belum ada produk. Tambahkan produk terlebih dahulu di menu List Produk.")
    else:
        produk_names = [p["Nama Produk"] for p in st.session_state.products]
        selected_produk = st.selectbox("Pilih Produk", produk_names)
        qty = st.number_input("Jumlah", min_value=1, value=1)

        if st.button("Tambah ke Keranjang"):
            produk = next(p for p in st.session_state.products if p["Nama Produk"] == selected_produk)
            st.session_state.cart.append(
                {"SKU": produk["SKU"], "Nama Produk": produk["Nama Produk"], 
                 "Harga Jual": produk["Harga Jual"], "Owner": produk["Owner"], "Qty": qty}
            )
            st.success(f"{qty} x {produk['Nama Produk']} ditambahkan ke keranjang")

        if st.session_state.cart:
            st.subheader("Keranjang Belanja")
            df_cart = pd.DataFrame(st.session_state.cart)
            df_cart["Total"] = df_cart["Harga Jual"] * df_cart["Qty"]
            st.dataframe(df_cart, use_container_width=True)
            st.write("**Total Bayar: Rp**", df_cart["Total"].sum())

            pembayaran = st.number_input("Nominal Pembayaran", min_value=0, value=0)
            if st.button("Checkout"):
                total = df_cart["Total"].sum()
                if pembayaran < total:
                    st.error("Nominal pembayaran kurang!")
                else:
                    kembalian = pembayaran - total
                    st.success(f"Transaksi berhasil! Kembalian: Rp{kembalian:,}")
                    # Simpan laporan
                    df_cart["Pembayaran"] = pembayaran
                    df_cart["Kembalian"] = kembalian
                    df_cart["Timestamp"] = pd.Timestamp.now()
                    st.session_state.report.extend(df_cart.to_dict("records"))
                    st.session_state.cart = []

# ----------------- LIST PRODUK (CRUD) -----------------
elif menu == "List Produk":
    st.subheader("Daftar Produk")

    df = pd.DataFrame(st.session_state.products)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Belum ada produk yang ditambahkan.")

    st.download_button(
        label="Download Template Excel",
        data=download_template_excel(),
        file_name="template_produk.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.divider()
    st.write("### Tambah Produk Baru")
    sku = st.text_input("SKU")
    nama_produk = st.text_input("Nama Produk")
    harga_jual = st.number_input("Harga Jual", min_value=0, value=0)
    owner = st.text_input("Owner")

    if st.button("Tambah Produk"):
        if sku and nama_produk:
            st.session_state.products.append({
                "SKU": sku, "Nama Produk": nama_produk, "Harga Jual": harga_jual, "Owner": owner
            })
            st.success(f"Produk '{nama_produk}' berhasil ditambahkan!")
            st.rerun()
        else:
            st.error("SKU dan Nama Produk wajib diisi!")

    st.divider()
    st.write("### Edit Produk")
    produk_names = [p["Nama Produk"] for p in st.session_state.products]
    if produk_names:
        selected_edit = st.selectbox("Pilih produk untuk edit", produk_names)
        produk_edit = next(p for p in st.session_state.products if p["Nama Produk"] == selected_edit)

        new_sku = st.text_input("SKU Baru", value=produk_edit["SKU"])
        new_nama = st.text_input("Nama Produk Baru", value=produk_edit["Nama Produk"])
        new_harga = st.number_input("Harga Jual Baru", min_value=0, value=produk_edit["Harga Jual"])
        new_owner = st.text_input("Owner Baru", value=produk_edit["Owner"])

        if st.button("Update Produk"):
            produk_edit.update({
                "SKU": new_sku, "Nama Produk": new_nama, "Harga Jual": new_harga, "Owner": new_owner
            })
            st.success("Produk berhasil diupdate!")
            st.rerun()

    st.divider()
    st.write("### Hapus Produk")
    if produk_names:
        selected_delete = st.selectbox("Pilih produk untuk hapus", produk_names, key="delete")
        if st.button("Hapus Produk"):
            st.session_state.products = [p for p in st.session_state.products if p["Nama Produk"] != selected_delete]
            st.success(f"Produk '{selected_delete}' berhasil dihapus!")
            st.rerun()

# ----------------- LAPORAN PENJUALAN -----------------
elif menu == "Laporan Penjualan":
    st.subheader("Laporan Penjualan")
    if st.session_state.report:
        df_report = pd.DataFrame(st.session_state.report)
        st.dataframe(df_report, use_container_width=True)
        total_penjualan = df_report["Total"].sum()
        st.write("**Total Penjualan: Rp**", total_penjualan)

        # Grafik jumlah produk terjual
        fig, ax = plt.subplots()
        df_report.groupby("Nama Produk")["Qty"].sum().plot(kind="bar", ax=ax)
        ax.set_ylabel("Jumlah Terjual")
        st.pyplot(fig)

        # Download laporan Excel
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df_report.to_excel(writer, index=False, sheet_name="Laporan")
        st.download_button("Download Laporan Excel", buffer.getvalue(), "laporan_penjualan.xlsx")
    else:
        st.info("Belum ada transaksi.")
