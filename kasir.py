import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==================== INISIALISASI ====================
if "produk" not in st.session_state:
    st.session_state.produk = pd.DataFrame(
        columns=["SKU", "Nama", "Owner", "Harga Reseller", "Harga Ritel", "Stok", "Foto"]
    )

if "keranjang" not in st.session_state:
    st.session_state.keranjang = []

if "histori" not in st.session_state:
    st.session_state.histori = []

# Folder foto produk
if not os.path.exists("produk_foto"):
    os.makedirs("produk_foto")

# ==================== FUNGSI ====================
def tambah_ke_keranjang(produk_row):
    # jika produk sudah ada di keranjang, tambah qty
    for item in st.session_state.keranjang:
        if item["SKU"] == produk_row["SKU"]:
            item["Qty"] += 1
            return
    # jika belum ada, masukkan baru
    st.session_state.keranjang.append({
        "SKU": produk_row["SKU"],
        "Nama": produk_row["Nama"],
        "Harga": produk_row["Harga Ritel"],
        "Qty": 1
    })

def checkout():
    total = sum([item["Harga"] * item["Qty"] for item in st.session_state.keranjang])
    transaksi = {
        "Waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Item": st.session_state.keranjang.copy(),
        "Total": total
    }
    st.session_state.histori.append(transaksi)

    # Kurangi stok
    for item in st.session_state.keranjang:
        idx = st.session_state.produk.index[st.session_state.produk["SKU"] == item["SKU"]].tolist()
        if idx:
            idx = idx[0]
            st.session_state.produk.at[idx, "Stok"] -= item["Qty"]

    st.session_state.keranjang = []
    st.success("Checkout berhasil! Stok sudah diperbarui.")

# ==================== SIDEBAR ====================
menu = st.sidebar.radio("📌 Menu", ["Kasir", "Daftar Produk", "Histori Transaksi"])

# ==================== HALAMAN KASIR ====================
if menu == "Kasir":
    st.title("🛒 Kasir")

    col1, col2 = st.columns([2, 1])

    # ----- Daftar Produk -----
    with col1:
        st.subheader("Pilih Produk")
        if st.session_state.produk.empty:
            st.info("Belum ada produk. Tambahkan di menu 'Daftar Produk'.")
        else:
            for idx, row in st.session_state.produk.iterrows():
                colp = st.columns([1, 2])
                with colp[0]:
                    if row["Foto"] and os.path.exists(row["Foto"]):
                        st.image(row["Foto"], width=120)
                    else:
                        st.image("https://via.placeholder.com/120", width=120)

                    if row["Stok"] > 0:
                        if st.button(f"Tambah {row['Nama']}", key=f"add_{idx}"):
                            tambah_ke_keranjang(row)
                    else:
                        st.error("Stok Habis")

                with colp[1]:
                    st.write(f"**{row['Nama']}**")
                    st.write(f"SKU: {row['SKU']}")
                    st.write(f"Harga: Rp{row['Harga Ritel']:,}")
                    st.write(f"Stok: {row['Stok']}")

                st.markdown("---")

    # ----- Keranjang -----
    with col2:
        st.subheader("Keranjang")
        if st.session_state.keranjang:
            total = 0
            for i, item in enumerate(st.session_state.keranjang):
                colk = st.columns([3,1,1])
                with colk[0]:
                    st.write(f"{item['Nama']} (x{item['Qty']})")
                with colk[1]:
                    st.write(f"Rp{item['Harga']*item['Qty']:,}")
                with colk[2]:
                    if st.button("❌", key=f"hapus_{i}"):
                        st.session_state.keranjang.pop(i)
                        st.rerun()
                total += item["Harga"] * item["Qty"]

            st.write(f"**Total: Rp{total:,}**")
            if st.button("✅ Checkout"):
                checkout()
        else:
            st.info("Keranjang kosong")

# ==================== HALAMAN PRODUK ====================
elif menu == "Daftar Produk":
    st.title("📦 Daftar Produk")

    tab1, tab2 = st.tabs(["➕ Tambah Produk", "✏️ Edit Produk"])

    # ---- Tambah Produk ----
    with tab1:
        with st.form("form_produk"):
            sku = st.text_input("SKU")
            nama = st.text_input("Nama Produk")
            owner = st.text_input("Owner")
            harga_reseller = st.number_input("Harga Reseller", min_value=0)
            harga_ritel = st.number_input("Harga Ritel", min_value=0)
            stok = st.number_input("Stok", min_value=0)
            foto = st.file_uploader("Foto Produk", type=["jpg", "png", "jpeg"])

            submit = st.form_submit_button("Tambah Produk")

            if submit:
                foto_path = None
                if foto:
                    foto_path = os.path.join("produk_foto", foto.name)
                    with open(foto_path, "wb") as f:
                        f.write(foto.getbuffer())

                new_row = {
                    "SKU": sku,
                    "Nama": nama,
                    "Owner": owner,
                    "Harga Reseller": harga_reseller,
                    "Harga Ritel": harga_ritel,
                    "Stok": stok,
                    "Foto": foto_path
                }
                st.session_state.produk = pd.concat(
                    [st.session_state.produk, pd.DataFrame([new_row])],
                    ignore_index=True
                )
                st.success("Produk berhasil ditambahkan!")

    # ---- Edit Produk ----
    with tab2:
        if not st.session_state.produk.empty:
            pilih_sku = st.selectbox("Pilih SKU", st.session_state.produk["SKU"])
            idx = st.session_state.produk.index[st.session_state.produk["SKU"] == pilih_sku][0]
            data_produk = st.session_state.produk.loc[idx]

            with st.form("form_edit"):
                sku_edit = st.text_input("SKU", value=data_produk["SKU"])
                nama_edit = st.text_input("Nama Produk", value=data_produk["Nama"])
                owner_edit = st.text_input("Owner", value=data_produk["Owner"])
                harga_reseller_edit = st.number_input("Harga Reseller", min_value=0, value=int(data_produk["Harga Reseller"]))
                harga_ritel_edit = st.number_input("Harga Ritel", min_value=0, value=int(data_produk["Harga Ritel"]))
                stok_edit = st.number_input("Stok", min_value=0, value=int(data_produk["Stok"]))
                foto_edit = st.file_uploader("Ganti Foto Produk (opsional)", type=["jpg", "png", "jpeg"])

                submit_edit = st.form_submit_button("Simpan Perubahan")

                if submit_edit:
                    foto_path = data_produk["Foto"]
                    if foto_edit:
                        foto_path = os.path.join("produk_foto", foto_edit.name)
                        with open(foto_path, "wb") as f:
                            f.write(foto_edit.getbuffer())

                    st.session_state.produk.at[idx, "SKU"] = sku_edit
                    st.session_state.produk.at[idx, "Nama"] = nama_edit
                    st.session_state.produk.at[idx, "Owner"] = owner_edit
                    st.session_state.produk.at[idx, "Harga Reseller"] = harga_reseller_edit
                    st.session_state.produk.at[idx, "Harga Ritel"] = harga_ritel_edit
                    st.session_state.produk.at[idx, "Stok"] = stok_edit
                    st.session_state.produk.at[idx, "Foto"] = foto_path

                    st.success("Produk berhasil diperbarui!")

    st.subheader("📋 List Produk")
    if st.session_state.produk.empty:
        st.info("Belum ada produk")
    else:
        for i, row in st.session_state.produk.iterrows():
            colp = st.columns([4,1])
            with colp[0]:
                st.write(f"**{row['Nama']}** | SKU: {row['SKU']} | Harga: Rp{row['Harga Ritel']:,} | Stok: {row['Stok']}")
            with colp[1]:
                if st.button("❌ Hapus", key=f"hapus_produk_{i}"):
                    st.session_state.produk.drop(i, inplace=True)
                    st.session_state.produk.reset_index(drop=True, inplace=True)
                    st.rerun()

# ==================== HALAMAN HISTORI ====================
elif menu == "Histori Transaksi":
    st.title("🧾 Histori Transaksi")

    if st.session_state.histori:
        for trx in st.session_state.histori:
            st.write(f"📅 {trx['Waktu']}")
            for item in trx["Item"]:
                st.write(f"- {item['Nama']} x{item['Qty']} = Rp{item['Harga']*item['Qty']:,}")
            st.write(f"**Total: Rp{trx['Total']:,}**")
            st.markdown("---")
    else:
        st.info("Belum ada transaksi")
