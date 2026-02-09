import { Edit, Trash2, Plus } from 'lucide-react';

const products = [
  { id: 1, name: 'Laptop Pro', price: '$1,299', stock: 45 },
  { id: 2, name: 'Wireless Mouse', price: '$29', stock: 120 },
  { id: 3, name: 'Mechanical Keyboard', price: '$149', stock: 78 },
  { id: 4, name: 'USB-C Hub', price: '$59', stock: 200 },
];

export function Products() {
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-[#2C2C2A]">Products</h1>
        <button className="bg-[#2C2C2A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#3C3C3A] transition-colors flex items-center gap-2">
          <Plus size={16} />
          Add Product
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] overflow-hidden">
        <table className="w-full">
          <thead className="bg-[#FAFAF5]">
            <tr>
              <th className="px-6 py-3.5 text-left text-xs font-medium text-[#6C6C6A] uppercase tracking-wide">Name</th>
              <th className="px-6 py-3.5 text-left text-xs font-medium text-[#6C6C6A] uppercase tracking-wide">Price</th>
              <th className="px-6 py-3.5 text-left text-xs font-medium text-[#6C6C6A] uppercase tracking-wide">Stock</th>
              <th className="px-6 py-3.5 text-left text-xs font-medium text-[#6C6C6A] uppercase tracking-wide">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#F0F0EA]">
            {products.map((product) => (
              <tr key={product.id} className="hover:bg-[#FAFAF5] transition-colors">
                <td className="px-6 py-4 text-sm font-medium text-[#2C2C2A]">{product.name}</td>
                <td className="px-6 py-4 text-sm text-[#6C6C6A]">{product.price}</td>
                <td className="px-6 py-4 text-sm text-[#6C6C6A]">{product.stock}</td>
                <td className="px-6 py-4">
                  <div className="flex gap-1">
                    <button className="p-1.5 text-[#9C9C9A] hover:text-[#2C2C2A] hover:bg-[#F5F5F0] rounded transition-colors">
                      <Edit size={16} />
                    </button>
                    <button className="p-1.5 text-[#9C9C9A] hover:text-red-600 hover:bg-red-50 rounded transition-colors">
                      <Trash2 size={16} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
