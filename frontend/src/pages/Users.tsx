import { UserCircle, Mail, Shield, Plus } from 'lucide-react';

const users = [
  { id: 1, name: 'John Doe', email: 'john@example.com', role: 'Admin' },
  { id: 2, name: 'Jane Smith', email: 'jane@example.com', role: 'Editor' },
  { id: 3, name: 'Bob Johnson', email: 'bob@example.com', role: 'Viewer' },
  { id: 4, name: 'Alice Williams', email: 'alice@example.com', role: 'Editor' },
];

export function Users() {
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-[#2C2C2A]">Users</h1>
        <button className="bg-[#2C2C2A] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#3C3C3A] transition-colors flex items-center gap-2">
          <Plus size={16} />
          Add User
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] divide-y divide-[#F0F0EA]">
        {users.map((user) => (
          <div
            key={user.id}
            className="flex items-center gap-4 p-4 hover:bg-[#FAFAF5] transition-colors"
          >
            <div className="bg-[#F5F5F0] p-2 rounded-full">
              <UserCircle size={28} className="text-[#9C9C9A]" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-medium text-[#2C2C2A]">{user.name}</h3>
              <div className="flex items-center gap-1.5 text-xs text-[#9C9C9A] mt-0.5">
                <Mail size={12} />
                <span className="truncate">{user.email}</span>
              </div>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-[#9C9C9A] bg-[#F5F5F0] px-2.5 py-1 rounded-full">
              <Shield size={12} />
              {user.role}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
