import { User, Shield, Key } from 'lucide-react';

const ProfileTabs = ({ activeTab, onTabChange }) => {
  const tabs = [
    { id: 'personal', label: 'Información Personal', icon: User },
    { id: 'security', label: 'Seguridad', icon: Shield },
  ];

  return (
    <div className="border-b border-gray-700">
      <nav className="flex -mb-px">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                isActive
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-600'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </nav>
    </div>
  );
};

export default ProfileTabs;