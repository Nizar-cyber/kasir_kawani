# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm

st.set_page_config(page_title="Kasir App", layout="wide")

# ----------------- INITIAL PRODUCTS (from your image) -----------------
# Each product: Owner, Nama Produk, Harga Reseller, Harga Retail, Potongan (auto), Stock, Stock_Awal
initial_products = [
    {"Owner": "Bu.Ilah", "Nama Produk": "Kacang Bawang", "Harga Reseller": 18000, "Harga Retail": 20000, "Stock": 5},
    {"Owner": "Bu.Ilah", "Nama Produk": "Kacang Thailand", "Harga Reseller": 18000, "Harga Retail": 20000, "Stock": 5},
    {"Owner": "Bu.Irma", "Nama Produk": "Kacang Serda", "Harga Reseller": 13000, "Harga Retail": 15000, "Stock": 4},
    {"Owner": "DMF", "Nama Produk": "Telor Gabus", "Harga Reseller": 13000, "Harga Retail": 15000, "Stock": 5},

    {"Owner": "Teh Dudeh", "Nama Produk": "Cilok", "Harga Reseller": 10000, "Harga Retail": 12000, "Stock": 6},
    {"Owner": "Teh Abel", "Nama Produk": "Potachiz Bread", "Harga Reseller": 20000, "Harga Retail": 22000, "Stock": 3},
    {"Owner": "Teh Abel", "Nama Produk": "Potachiz Moza", "Harga Reseller": 23000, "Harga Retail": 25000, "Stock": 3},

    {"Owner": "Teh Sella", "Nama Produk": "Doremi Coffeegazer", "Harga Reseller": 10000, "Harga Retail": 12000, "Stock": 10},
    {"Owner": "Teh Sella", "Nama Produk": "Doremi Jus", "Harga Reseller": 4000, "Harga Retail": 6000, "Stock": 9},
    {"Owner": "Bu.Irma", "Nama Produk": "Pudot", "Harga Reseller": 8000, "Harga Retail": 10000, "Stock": 10},
    {"Owner": "Bu.Irma", "Nama Produk": "Es Kuwut", "Harga Reseller": 8000, "Harga Retail": 10000, "Stock": 6},

    {"Owner": "Teh Abel", "Nama Produk": "Juice True", "Harga Reseller": 8000, "Harga Retail": 10000, "Stock": 9},
    {"Owner": "Bu.Diah", "Nama Produk": "Kopikir", "Harga Reseller": 8000, "Harga Retail": 10000, "Stock": 7},
    {"Owner": "Pak Tata", "Nama Produk": "Belgian Chocolate", "Harga Reseller": 8000, "Harga Retail": 10000, "Stock": 3},
    {"Owner": "Pak Tata", "Nama Produk": "Matcha Latte", "Harga Reseller": 8000, "Harga Retail": 10000, "Stock": 3},

    {"Owner": "Bu.Ilah", "Nama Produk": "Kunyit asem", "Harga Reseller": 8000, "Harga Retail": 10000, "Stock": 10},
    {"Owner": "Pak Tata", "Nama Produk": "Lemon Tea", "Harga Reseller": 8000, "Harga Retail": 10000, "Stock": 3},
    {"Owner": "DMF", "Nama Produk": "Cendol Cebong", "Harga Reseller": 10000, "Harga Retail": 12000, "Stock": 10},
    {"Owner": "DMF", "Nama Produk": "Jelly Lumut", "Harga Reseller": 8000, "Harga Retail": 10000, "Stock": 5},
    {"Owner": "Bu.Ilah", "Nama Produk": "Air Mineral", "Harga Reseller": 4000, "Harga Retail": 5000, "Stock": 17},
]

# ----------------- SESSION STATE -----------------
if "products" not in st.session_state:
    # initialize products, compute potongan and set Stock_Awal
    products = []
    for p in initial_products:
        prod = p.copy()
        prod["Potongan"] = prod["Harga Retail"] - prod["Harga Reseller"]
        prod["Stock_Awal"] = prod["Stock"]
        products.append(prod)
    st.session_state.products = products

if "cart" not in st.session_state:
    st.session_state.cart = []

if "history" not in st.session_state:
    # history stores transactions: each entry: dict with timestamp, items(list), total, pembayaran, kembalian
    st.session_state.history = []

# ----------------- HELPERS: exports -----------------
def export_excel(df: pd.DataFrame) -> bytes:
    # requires openpyxl installed
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Laporan")
    return output.getvalue()

def export_report_pdf(df: pd.DataFrame) -> bytes:
    # create a simple table-like PDF (landscape) summarizing products and owner totals
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 20, "Laporan Penjualan")

    # table header
    headers = ["Nama Produk", "Owner", "Stock Awal", "Stock Akhir", "Sold", "Harga Reseller",
               "Harga Jual", "Potongan", "Gross Income", "Net Income"]
    col_x = [10*mm, 55*mm, 95*mm, 120*mm, 145*mm, 175*mm, 205*mm, 235*mm, 260*mm, 300*mm]
    y = height - 40
    c.setFont("Helvetica-Bold", 8)
    for i, h in enumerate(headers):
        c.drawString(col_x[i], y, h)
    y -= 8

    c.setFont("Helvetica", 8)
    row_h = 10
    for _, row in df.iterrows():
        if y < 30:
            c.showPage()
            y = height - 30
            c.setFont("Helvetica-Bold", 8)
            for i, h in enumerate(headers):
                c.drawString(col_x[i], y, h)
            y -= 8
            c.setFont("Helvetica", 8)

        c.drawString(col_x[0], y, str(row["Nama Produk"])[:25])
        c.drawString(col_x[1], y, str(row["Owner"])[:15])
        c.drawRightString(col_x[2]+20*mm, y, str(int(row["Stock_Awal"])))
        c.drawRightString(col_x[3]+20*mm, y, str(int(row["Stock_Akhir"])))
        c.drawRightString(col_x[4]+10*mm, y, str(int(row["Sold"])))
        c.drawRightString(col_x[5]+20*mm, y, f"Rp{int(row['Harga Reseller']):,}")
        c.drawRightString(col_x[6]+20*mm, y, f"Rp{int(row['Harga Jual']):,}")
        c.drawRightString(col_x[7]+20*mm, y, f"Rp{int(row['Potongan']):,}")
        c.drawRightString(col_x[8]+30*mm, y, f"Rp{int(row['Gross Income']):,}")
        c.drawRightString(col_x[9]+30*mm, y, f"Rp{int(row['Net Income']):,}")
        y -= row_h

    # totals per owner (append at end)
    owners = df.groupby("Owner").agg(
        total_qty=("Sold", "sum"),
        total_gross=("Gross Income", "sum"),
        total_net=("Net Income", "sum")
    ).reset_index()

    if y < 80:
        c.showPage()
        y = height - 40

    y -= 10
    c.setFont("Helvetica-Bold", 10)
    c.drawString(10*mm, y, "Ringkasan per Owner")
    y -= 8
    c.setFont("Helvetica-Bold", 8)
    c.drawString(10*mm, y, "Owner")
    c.drawRightString(120*mm, y, "Qty Sold")
    c.drawRightString(160*mm, y, "Gross")
    c.drawRightString(200*mm, y, "Net")
    y -= 6
    c.setFont("Helvetica", 8)
    for _, r in owners.iterrows():
        if y < 30:
            c.showPage()
            y = height - 40
        c.drawString(10*mm, y, str(r["Owner"]))
        c.drawRightString(120*mm, y, str(int(r["total_qty"])))
        c.drawRightString(160*mm, y, f"Rp{int(r['total_gross']):,}")
        c.drawRightString(200*mm, y, f"Rp{int(r['total_net']):,}")
        y -= 8

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# ----------------- TEMPLATE download & upload -----------------
def download_template_bytes() -> bytes:
    df = pd.DataFrame(columns=["Owner", "Nama Produk", "Harga Reseller", "Harga Jual", "Stock"])
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Template Produk")
    return out.getvalue()

def add_product_from_row(row):
    # row: dict or Series, compute Potongan and Stock_Awal
    prod = {
        "Owner": row.get("Owner"),
        "Nama Produk": row.get("Nama Produk"),
        "Harga Reseller": float(row.get("Harga Reseller")),
        "Harga Jual": float(row.get("Harga Jual")),
        "Potongan": float(row.get("Harga Jual")) - float(row.get("Harga Reseller")),
        "Stock": int(row.get("Stock")),
        "Stock_Awal": int(row.get("Stock"))
    }
    st.session_state.products.append(prod)

# ----------------- SIDEBAR MENU -----------------
menu = st.sidebar.radio("📌 Menu", ["Kasir", "Daftar Produk", "Tambah Produk", "Edit Produk", "Laporan Penjualan"])

# ----------------- KASIR -----------------
if menu == "Kasir":
    st.title("🛒 Kasir")
    st.markdown("Pilih produk (grid 4 kolom). Harga final = Harga Jual - Potongan (potongan dihitung otomatis).")

    # product grid 4 columns
    if len(st.session_state.products) == 0:
        st.info("Belum ada produk.")
    else:
        cols = st.columns(4)
        for i, p in enumerate(st.session_state.products):
            col = cols[i % 4]
            with col:
                st.markdown(f"**{p['Nama Produk']}**")
                st.write(f"Owner: {p['Owner']}")
                st.write(f"Harga Jual: Rp{int(p['Harga Jual']):,}")
                st.write(f"Potongan: Rp{int(p['Potongan']):,}")
                st.write(f"Stock: {int(p['Stock'])}")
                qty = st.number_input(f"qty_{i}", min_value=1, max_value=max(1, int(p["Stock"])), value=1, key=f"qty_{i}")
                if st.button(f"Tambah ke Keranjang - {p['Nama Produk']}", key=f"add_{i}"):
                    if p["Stock"] < qty:
                        st.error("Stok tidak mencukupi!")
                    else:
                        harga_final = p["Harga Jual"] - p["Potongan"]
                        subtotal = harga_final * qty
                        st.session_state.cart.append({
                            "Owner": p["Owner"],
                            "Nama Produk": p["Nama Produk"],
                            "Harga Reseller": p["Harga Reseller"],
                            "Harga Jual": p["Harga Jual"],
                            "Potongan": p["Potongan"],
                            "Harga Final": harga_final,
                            "Qty": qty,
                            "Subtotal": subtotal
                        })
                        st.success(f"{qty} x {p['Nama Produk']} ditambahkan ke keranjang!")

            if (i + 1) % 4 == 0:
                cols = st.columns(4)  # new row

    # show cart
    if st.session_state.cart:
        st.subheader("🧾 Keranjang")
        df_cart = pd.DataFrame(st.session_state.cart)
        st.dataframe(df_cart[["Nama Produk", "Owner", "Harga Final", "Potongan", "Qty", "Subtotal"]])

        total = df_cart["Subtotal"].sum()
        st.markdown(f"### Total: Rp{int(total):,}")

        st.subheader("Pembayaran")
        pembayaran = st.number_input("Masukkan Nominal Pembayaran", min_value=0, step=1000, value=0, key="in_pembayaran")

        if st.button("Proses Checkout"):
            if pembayaran < total:
                st.error("Uang tidak cukup!")
            else:
                kembalian = pembayaran - total
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # save transaction
                transaction_items = []
                for it in st.session_state.cart:
                    transaction_items.append(it.copy())
                    # reduce stock in products
                    for p in st.session_state.products:
                        if p["Nama Produk"] == it["Nama Produk"] and p["Owner"] == it["Owner"]:
                            p["Stock"] = max(0, int(p["Stock"]) - int(it["Qty"]))
                st.session_state.history.append({
                    "timestamp": timestamp,
                    "items": transaction_items,
                    "total": float(total),
                    "pembayaran": float(pembayaran),
                    "kembalian": float(kembalian)
                })
                st.session_state.cart = []
                st.success(f"Checkout sukses! Total Rp{int(total):,} — Pembayaran Rp{int(pembayaran):,} — Kembalian Rp{int(kembalian):,}")

# ----------------- DAFTAR PRODUK -----------------
elif menu == "Daftar Produk":
    st.title("📦 Daftar Produk")
    if len(st.session_state.products) == 0:
        st.info("Belum ada produk.")
    else:
        dfp = pd.DataFrame(st.session_state.products)
        st.dataframe(dfp[["Nama Produk", "Owner", "Harga Reseller", "Harga Jual", "Potongan", "Stock", "Stock_Awal"]])

# ----------------- TAMBAH PRODUK -----------------
elif menu == "Tambah Produk":
    st.title("➕ Tambah Produk Manual / Upload Excel")
    with st.form("tambah_form"):
        owner = st.text_input("Owner")
        nama = st.text_input("Nama Produk")
        harga_reseller = st.number_input("Harga Reseller", min_value=0, value=0)
        harga_jual = st.number_input("Harga Jual", min_value=0, value=0)
        stock = st.number_input("Stock", min_value=0, value=0)
        submitted = st.form_submit_button("Tambah Produk")
        if submitted:
            prod = {
                "Owner": owner,
                "Nama Produk": nama,
                "Harga Reseller": float(harga_reseller),
                "Harga Jual": float(harga_jual),
                "Potongan": float(harga_jual) - float(harga_reseller),
                "Stock": int(stock),
                "Stock_Awal": int(stock)
            }
            st.session_state.products.append(prod)
            st.success(f"Produk {nama} ditambahkan.")

    st.markdown("---")
    st.subheader("📤 Upload Produk dari Excel (format: Owner, Nama Produk, Harga Reseller, Harga Jual, Stock)")
    uploaded = st.file_uploader("Pilih file Excel", type=["xlsx"])
    if uploaded:
        try:
            df_up = pd.read_excel(uploaded)
            required = {"Owner", "Nama Produk", "Harga Reseller", "Harga Jual", "Stock"}
            if not required.issubset(set(df_up.columns)):
                st.error(f"Format salah. Pastikan kolom: {required}")
            else:
                for _, r in df_up.iterrows():
                    add_product_from_row(r)
                st.success("Produk dari Excel berhasil ditambahkan.")
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")

    st.markdown("---")
    st.subheader("📥 Download Template Excel Produk")
    st.download_button("Download Template Produk", data=download_template_bytes(), file_name="template_produk.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ----------------- EDIT PRODUK -----------------
elif menu == "Edit Produk":
    st.title("✏️ Edit / Hapus Produk")
    if len(st.session_state.products) == 0:
        st.info("Belum ada produk.")
    else:
        pilihan = [f"{p['Nama Produk']} — {p['Owner']}" for p in st.session_state.products]
        sel = st.selectbox("Pilih Produk", pilihan)
        idx = pilihan.index(sel)
        prod = st.session_state.products[idx]

        with st.form("edit_form"):
            prod["Owner"] = st.text_input("Owner", prod["Owner"])
            prod["Nama Produk"] = st.text_input("Nama Produk", prod["Nama Produk"])
            prod["Harga Reseller"] = float(st.number_input("Harga Reseller", min_value=0, value=float(prod["Harga Reseller"])))
            prod["Harga Jual"] = float(st.number_input("Harga Jual", min_value=0, value=float(prod["Harga Jual"])))
            prod["Potongan"] = prod["Harga Jual"] - prod["Harga Reseller"]
            prod["Stock"] = int(st.number_input("Stock", min_value=0, value=int(prod["Stock"])))
            col1, col2 = st.columns([1, 1])
            with col1:
                upd = st.form_submit_button("Update")
            with col2:
                delete = st.form_submit_button("Hapus Produk")
            if upd:
                st.success("Produk berhasil diperbarui.")
            if delete:
                del st.session_state.products[idx]
                st.warning("Produk dihapus.")

# ----------------- LAPORAN PENJUALAN -----------------
elif menu == "Laporan Penjualan":
    st.title("📊 Laporan Penjualan")
    if len(st.session_state.history) == 0 and all(int(p["Stock"]) == int(p["Stock_Awal"]) for p in st.session_state.products):
        st.info("Belum ada transaksi / belum ada penjualan.")
    else:
        # Build report per product based on stock change
        rows = []
        for p in st.session_state.products:
            stock_awal = int(p.get("Stock_Awal", 0))
            stock_akhir = int(p.get("Stock", 0))
            sold = max(0, stock_awal - stock_akhir)
            gross_income = sold * p["Harga Jual"]
            net_income = sold * (p["Harga Jual"] - p["Potongan"])
            rows.append({
                "Nama Produk": p["Nama Produk"],
                "Owner": p["Owner"],
                "Stock_Awal": stock_awal,
                "Stock_Akhir": stock_akhir,
                "Sold": sold,
                "Harga Reseller": p["Harga Reseller"],
                "Harga Jual": p["Harga Jual"],
                "Potongan": p["Potongan"],
                "Gross Income": gross_income,
                "Net Income": net_income
            })

        df_report = pd.DataFrame(rows)
        st.dataframe(df_report)

        # Summaries per owner
        owner_summary = df_report.groupby("Owner").agg(
            total_sold=("Sold", "sum"),
            gross_total=("Gross Income", "sum"),
            net_total=("Net Income", "sum")
        ).reset_index()
        st.subheader("Ringkasan per Owner")
        st.dataframe(owner_summary)

        # Totals
        st.write("**Total Gross:** ", f"Rp{int(df_report['Gross Income'].sum()):,}")
        st.write("**Total Net:** ", f"Rp{int(df_report['Net Income'].sum()):,}")

        # Export buttons
        col1, col2 = st.columns(2)
        with col1:
            excel_bytes = export_excel(df_report)
            st.download_button("⬇️ Download Laporan (Excel)", data=excel_bytes, file_name="laporan_penjualan.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col2:
            pdf_bytes = export_report_pdf(df_report)
            st.download_button("⬇️ Download Laporan (PDF)", data=pdf_bytes, file_name="laporan_penjualan.pdf",
                               mime="application/pdf")

        # Also show transaction history (each checkout) with timestamp, total, payment, change
        st.subheader("History Transaksi (checkout)")
        history_rows = []
        for tx in st.session_state.history:
            history_rows.append({
                "Timestamp": tx["timestamp"],
                "Total": tx["total"],
                "Pembayaran": tx["pembayaran"],
                "Kembalian": tx["kembalian"],
                "Items Count": len(tx["items"])
            })
        st.dataframe(pd.DataFrame(history_rows))

