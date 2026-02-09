import { NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, Package, Users, Settings } from 'lucide-react';

const menuItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/products', label: 'Products', icon: Package },
  { path: '/users', label: 'Users', icon: Users },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="w-64 bg-[#F5F5F0] text-[#5C5C52] flex flex-col h-screen border-r border-[#E5E5E0]">
      <div className="p-6">
        <h1 className="text-xl font-bold text-[#2C2C2A]">Admin Panel</h1>
      </div>
      
      <nav className="flex-1 px-3 py-4">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all text-sm font-medium ${
                isActive
                  ? 'bg-[#FFFFFF] text-[#2C2C2A] shadow-sm border border-[#E5E5E0]'
                  : 'text-[#6C6C6A] hover:bg-[#FFFFFF] hover:text-[#2C2C2A]'
              }`}
            >
              <Icon size={18} className={isActive ? 'text-[#2C2C2A]' : 'text-[#9C9C9A]'} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="p-4 text-xs text-[#9C9C9A]">
        v1.0.0
      </div>
    </aside>
  );
}
