    import { User, Mail, Calendar, Shield, Edit3 } from 'lucide-react';

    const ProfileHeader = ({ user }) => {
    if (!user) return null;

    const getRoleBadge = (role) => {
        const roles = {
        user: { label: 'Usuario', color: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
        artist: { label: 'Artista', color: 'bg-purple-500/20 text-purple-400 border-purple-500/30' },
        admin: { label: 'Administrador', color: 'bg-red-500/20 text-red-400 border-red-500/30' }
        };
        
        const roleConfig = roles[role] || roles.user;
        
        return (
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${roleConfig.color}`}>
            <Shield className="w-3 h-3 mr-1" />
            {roleConfig.label}
        </span>
        );
    };

    return (
        <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
        <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                <User className="w-8 h-8 text-white" />
            </div>
            <div>
                <h1 className="text-2xl font-bold text-white">{user.name || user.username}</h1>
                <p className="text-gray-400">@{user.username}</p>
            </div>
            </div>
        </div>

        <div className="space-y-3">
            <div className="flex items-center gap-3 text-gray-300">
            <Mail className="w-4 h-4 text-gray-400" />
            <span className="text-sm">{user.email}</span>
            </div>
        
        </div>
        </div>
    );
    };

    export default ProfileHeader;