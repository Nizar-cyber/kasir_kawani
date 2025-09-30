import React, { useState } from "react";

export default function App() {
  const [products, setProducts] = useState([
    {
      sku: "SKU001",
      name: "Produk A",
      owner: "Nizar",
      resellerPrice: 50000,
      retailPrice: 60000,
      stock: 10,
    },
    {
      sku: "SKU002",
      name: "Produk B",
      owner: "Andi",
      resellerPrice: 70000,
      retailPrice: 85000,
      stock: 5,
    },
  ]);

  const [cart, setCart] = useState([]);

  const addToCart = (product, qty) => {
    if (product.stock < qty) {
      alert("Stok tidak mencukupi!");
      return;
    }
    // cek kalau sudah ada di keranjang
    const existing = cart.find((item) => item.sku === product.sku);
    if (existing) {
      setCart(
        cart.map((item) =>
          item.sku === product.sku
            ? { ...item, qty: item.qty + qty }
            : item
        )
      );
    } else {
      setCart([...cart, { ...product, qty }]);
    }
  };

  const removeFromCart = (sku) => {
    setCart(cart.filter((item) => item.sku !== sku));
  };

  const checkout = () => {
    const updatedProducts = [...products];
    cart.forEach((item) => {
      const index = updatedProducts.findIndex((p) => p.sku === item.sku);
      if (index !== -1) {
        updatedProducts[index].stock -= item.qty;
      }
    });
    setProducts(updatedProducts);
    setCart([]);
    alert("Checkout berhasil!");
  };

  // Hitung total harga
  const totalHarga = cart.reduce(
    (sum, item) => sum + item.retailPrice * item.qty,
    0
  );

  return (
    <div className="p-6 grid grid-cols-2 gap-6">
      {/* Daftar Produk */}
      <div>
        <h2 className="text-xl font-bold mb-4">Daftar Produk</h2>
        <div className="space-y-4">
          {products.map((product) => {
            const [qty, setQty] = useState(1);
            return (
              <div
                key={product.sku}
                className="border p-4 rounded-lg shadow flex flex-col gap-2"
              >
                <p>
                  <strong>SKU:</strong> {product.sku}
                </p>
                <p>
                  <strong>Nama:</strong> {product.name}
                </p>
                <p>
                  <strong>Owner:</strong> {product.owner}
                </p>
                <p>
                  <strong>Harga Reseller:</strong> Rp
                  {product.resellerPrice.toLocaleString()}
                </p>
                <p>
                  <strong>Harga Ritel:</strong> Rp
                  {product.retailPrice.toLocaleString()}
                </p>
                <p>
                  <strong>Stok:</strong> {product.stock}
                </p>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min="1"
                    max={product.stock}
                    value={qty}
                    onChange={(e) => setQty(Number(e.target.value))}
                    className="border rounded px-2 py-1 w-20"
                  />
                  <button
                    onClick={() => addToCart(product, qty)}
                    className="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600"
                  >
                    Tambah ke Keranjang
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Keranjang */}
      <div>
        <h2 className="text-xl font-bold mb-4">Keranjang</h2>
        {cart.length === 0 ? (
          <p className="text-gray-500">Keranjang kosong</p>
        ) : (
          <div className="space-y-4">
            {cart.map((item) => (
              <div
                key={item.sku}
                className="border p-4 rounded-lg shadow flex justify-between items-center"
              >
                <div>
                  <p>
                    {item.name} (x{item.qty})
                  </p>
                  <p className="text-sm text-gray-600">
                    Rp{item.retailPrice.toLocaleString()} per item
                  </p>
                  <p className="font-semibold">
                    Subtotal: Rp{(item.retailPrice * item.qty).toLocaleString()}
                  </p>
                </div>
                <button
                  onClick={() => removeFromCart(item.sku)}
                  className="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600"
                >
                  Hapus
                </button>
              </div>
            ))}

            {/* Total Harga */}
            <div className="border-t pt-4 text-lg font-semibold">
              Total: Rp{totalHarga.toLocaleString()}
            </div>

            <button
              onClick={checkout}
              className="w-full bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              Checkout
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
