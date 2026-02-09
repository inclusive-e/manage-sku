import { Bell, Lock, User, Globe } from 'lucide-react';

export function Settings() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold text-[#2C2C2A] mb-6">Settings</h1>

      <div className="max-w-2xl space-y-4">
        <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="p-2 bg-[#F5F5F0] rounded-lg">
              <User className="text-[#9C9C9A]" size={18} />
            </div>
            <h2 className="text-base font-semibold text-[#2C2C2A]">Profile</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-[#6C6C6A] mb-1.5 uppercase tracking-wide">Name</label>
              <input
                type="text"
                defaultValue="Admin User"
                className="w-full px-3 py-2 bg-[#FAFAF5] border border-[#E5E5E0] rounded-lg text-sm text-[#2C2C2A] focus:outline-none focus:ring-2 focus:ring-[#D4D4D0] focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6C6C6A] mb-1.5 uppercase tracking-wide">Email</label>
              <input
                type="email"
                defaultValue="admin@example.com"
                className="w-full px-3 py-2 bg-[#FAFAF5] border border-[#E5E5E0] rounded-lg text-sm text-[#2C2C2A] focus:outline-none focus:ring-2 focus:ring-[#D4D4D0] focus:border-transparent"
              />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="p-2 bg-[#F5F5F0] rounded-lg">
              <Bell className="text-[#9C9C9A]" size={18} />
            </div>
            <h2 className="text-base font-semibold text-[#2C2C2A]">Notifications</h2>
          </div>
          <div className="space-y-3">
            {['Email notifications', 'Push notifications', 'Weekly digest'].map((item) => (
              <label key={item} className="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" defaultChecked className="w-4 h-4 rounded border-[#E5E5E0] text-[#2C2C2A] focus:ring-[#D4D4D0]" />
                <span className="text-sm text-[#2C2C2A]">{item}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="p-2 bg-[#F5F5F0] rounded-lg">
              <Globe className="text-[#9C9C9A]" size={18} />
            </div>
            <h2 className="text-base font-semibold text-[#2C2C2A]">Preferences</h2>
          </div>
          <div>
            <label className="block text-xs font-medium text-[#6C6C6A] mb-1.5 uppercase tracking-wide">Language</label>
            <select className="w-full px-3 py-2 bg-[#FAFAF5] border border-[#E5E5E0] rounded-lg text-sm text-[#2C2C2A] focus:outline-none focus:ring-2 focus:ring-[#D4D4D0] focus:border-transparent">
              <option>English</option>
              <option>Spanish</option>
              <option>French</option>
            </select>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="p-2 bg-[#F5F5F0] rounded-lg">
              <Lock className="text-[#9C9C9A]" size={18} />
            </div>
            <h2 className="text-base font-semibold text-[#2C2C2A]">Security</h2>
          </div>
          <button className="text-sm text-[#6C6C6A] hover:text-[#2C2C2A] transition-colors">
            Change password
          </button>
        </div>
      </div>
    </div>
  );
}
