import { TrendingUp, ShoppingCart, Users, DollarSign } from 'lucide-react';

const stats = [
  { label: 'Total Sales', value: '$45,231', change: '+20%', icon: DollarSign },
  { label: 'Orders', value: '2,345', change: '+15%', icon: ShoppingCart },
  { label: 'Users', value: '1,234', change: '+8%', icon: Users },
  { label: 'Revenue', value: '$89,432', change: '+12%', icon: TrendingUp },
];

export function Dashboard() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold text-[#2C2C2A] mb-6">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-[#9C9C9A] uppercase tracking-wide">{stat.label}</p>
                  <p className="text-2xl font-semibold text-[#2C2C2A] mt-1">{stat.value}</p>
                </div>
                <div className="p-2 bg-[#F5F5F0] rounded-lg">
                  <Icon className="text-[#9C9C9A]" size={20} />
                </div>
              </div>
              <p className="mt-3 text-xs text-[#6C6C6A]">{stat.change} from last month</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
