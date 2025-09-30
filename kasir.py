import streamlit as st
import pandas as pd
from datetime import datetime

# ==================== INISIALISASI DATA ====================
if "products" not in st.session_state:
    st.session_state.products = [
        {"sku": "SKU001", "name": "Produk A", "owner": "Nizar", "reseller_price": 50000, "retail_price": 60000, "stock": 10},
        {"sku": "SKU002", "name": "Produk B", "owner": "Andi", "reseller_price": 70000, "retail_price": 85000, "stock": 5},
    ]

if "cart" not in st.session_state:
    st.session_state.cart = []

if "transactions" not in st.session_state:
    st.session_state.transactions = []  # histori transaksi

st.set_page_config(page_title="Aplikasi Kasir", page_icon="🛒", layout="wide")
st.title("🛒 Aplikasi Kasir")

menu = st.sidebar.radio("📌 Menu", ["Kasir", "Tambah Produk", "Histori Transaksi"])

# ==================== MENU KASIR ====================
if menu == "Kasir":
    col_produk, col_cart = st.columns([2, 1])

    with col_produk:
        st.subheader("📦 Daftar Produk")
        df = pd.DataFrame(st.session_state.products)
        st.dataframe(df, hide_index=True, use_container_width=True)

        for product in st.session_state.products:
            with st.expander(f"{product['sku']} - {product['name']} (Stok: {product['stock']})"):
                st.write(f"**Owner:** {product['owner']}")
                st.write(f"**Harga Reseller:** Rp{product['reseller_price']:,}")
                st.write(f"**Harga Ritel:** Rp{product['retail_price']:,}")
                st.write(f"**Stok Tersedia:** {product['stock']}")

                qty = st.number_input(
                    f"Jumlah {product['sku']}", 
                    min_value=1, 
                    max_value=product['stock'] if product['stock'] > 0 else 1, 
                    value=1, 
                    step=1, 
                    key=f"qty_{product['sku']}"
                )
                if st.button(f"Tambah {product['name']} ke Keranjang", key=f"add_{product['sku']}"):
                    if product["stock"] >= qty:
                        # cek apakah produk sudah ada di keranjang
                        found = False
                        for item in st.session_state.cart:
                            if item["sku"] == product["sku"]:
                                item["qty"] += qty
                                found = True
                                break
                        if not found:
                            st.session_state.cart.append({
                                "sku": product["sku"],
                                "name": product["name"],
                                "price": product["retail_price"],
                                "qty": qty
                            })
                        st.success(f"{product['name']} ditambahkan ke keranjang")
                    else:
                        st.error("Stok tidak mencukupi!")

    with col_cart:
        st.subheader("🛍️ Keranjang Belanja")

        if len(st.session_state.cart) == 0:
            st.info("Keranjang masih kosong")
        else:
            total = 0
            for item in st.session_state.cart:
                subtotal = item["price"] * item["qty"]
                total += subtotal
                st.write(f"**{item['name']}** (x{item['qty']})")
                st.write(f"Harga: Rp{item['price']:,} | Subtotal: Rp{subtotal:,}")
                if st.button(f"Hapus {item['sku']}", key=f"del_{item['sku']}"):
                    st.session_state.cart.remove(item)
                    st.rerun()

            st.markdown("---")
            st.write(f"### 💰 Total Belanja: Rp{total:,}")

            if st.button("✅ Checkout"):
                # Simpan transaksi ke histori
                transaksi = {
                    "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "items": st.session_state.cart.copy(),
                    "total": total,
                }
                st.session_state.transactions.append(transaksi)

                # Kurangi stok produk sesuai keranjang
                for item in st.session_state.cart:
                    for product in st.session_state.products:
                        if product["sku"] == item["sku"]:
                            product["stock"] -= item["qty"]
                st.session_state.cart = []
                st.success("Checkout berhasil! Stok diperbarui & transaksi tercatat.")
                st.rerun()

# ==================== MENU TAMBAH PRODUK ====================
elif menu == "Tambah Produk":
    st.subheader("➕ Tambah Produk Baru")
    with st.form("add_product_form"):
        sku = st.text_input("SKU")
        name = st.text_input("Nama Produk")
        owner = st.text_input("Owner")
        reseller_price = st.number_input("Harga Reseller", min_value=0, step=1000)
        retail_price = st.number_input("Harga Ritel", min_value=0, step=1000)
        stock = st.number_input("Stok", min_value=0, step=1)
        submitted = st.form_submit_button("Simpan Produk")

        if submitted:
            st.session_state.products.append({
                "sku": sku,
                "name": name,
                "owner": owner,
                "reseller_price": reseller_price,
                "retail_price": retail_price,
                "stock": stock,
            })
            st.success(f"Produk {name} berhasil ditambahkan!")

# ==================== MENU HISTORI TRANSAKSI ====================
elif menu == "Histori Transaksi":
    st.subheader("📜 Histori Transaksi")
    if len(st.session_state.transactions) == 0:
        st.info("Belum ada transaksi.")
    else:
        for trx in st.session_state.transactions:
            with st.expander(f"Transaksi {trx['waktu']} - Total Rp{trx['total']:,}"):
                for item in trx["items"]:
                    st.write(f"{item['name']} (x{item['qty']}) - Rp{item['price']:,}/item")
                st.write(f"**Total: Rp{trx['total']:,}**")
