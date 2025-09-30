import streamlit as st
import pandas as pd

# Inisialisasi data produk
if "products" not in st.session_state:
    st.session_state.products = [
        {"sku": "SKU001", "name": "Produk A", "owner": "Nizar", "reseller_price": 50000, "retail_price": 60000, "stock": 10},
        {"sku": "SKU002", "name": "Produk B", "owner": "Andi", "reseller_price": 70000, "retail_price": 85000, "stock": 5},
    ]

# Inisialisasi keranjang
if "cart" not in st.session_state:
    st.session_state.cart = []

st.title("🛒 Aplikasi Kasir")

# ----------------- DAFTAR PRODUK -----------------
st.header("Daftar Produk")
for product in st.session_state.products:
    with st.container():
        st.write(f"**SKU:** {product['sku']}")
        st.write(f"**Nama:** {product['name']}")
        st.write(f"**Owner:** {product['owner']}")
        st.write(f"**Harga Reseller:** Rp{product['reseller_price']:,}")
        st.write(f"**Harga Ritel:** Rp{product['retail_price']:,}")
        st.write(f"**Stok:** {product['stock']}")

        col1, col2 = st.columns([1, 2])
        with col1:
            qty = st.number_input(
                f"Qty {product['sku']}", 
                min_value=1, 
                max_value=product['stock'], 
                value=1, 
                key=f"qty_{product['sku']}"
            )
        with col2:
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

st.divider()

# ----------------- KERANJANG -----------------
st.header("Keranjang Belanja")

if len(st.session_state.cart) == 0:
    st.info("Keranjang kosong")
else:
    total = 0
    for item in st.session_state.cart:
        subtotal = item["price"] * item["qty"]
        total += subtotal
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"{item['name']} (x{item['qty']}) - Rp{item['price']:,}/item")
            st.write(f"Subtotal: Rp{subtotal:,}")
        with col2:
            if st.button(f"Hapus {item['sku']}", key=f"del_{item['sku']}"):
                st.session_state.cart.remove(item)
                st.rerun()

    st.write(f"### 💰 Total: Rp{total:,}")

    if st.button("Checkout"):
        # Kurangi stok produk
        for item in st.session_state.cart:
            for product in st.session_state.products:
                if product["sku"] == item["sku"]:
                    product["stock"] -= item["qty"]
        st.session_state.cart = []
        st.success("Checkout berhasil! Stok sudah diperbarui.")
        st.rerun()
