import { Header } from '../components/layout/Header';
import { motion } from 'framer-motion';
import { User, Mail, Phone, MapPin, Save, Camera } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';
import { cn } from '../lib/utils';

export default function Profile() {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    // TODO: Fetch initial user profile data from backend API (GET /users/me)
    fullName: 'Deepak',
    email: 'deepak@anomalyze.com',
    phone: '+91 9876543210',
    location: 'Pune, Maharashtra',
    bio: 'Lead Developer working on Anomalyze. Passionate about AI and Security.'
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);

    // TODO: Replace with actual API call to update profile (PUT /users/me)
    // const response = await api.put('/users/me', formData);

    // Simulate API call
    setTimeout(() => {
      setLoading(false);
      toast.success('Profile updated successfully');
    }, 1500);
  };

  return (
    <div>
      <Header title="User Profile" />

      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel p-8 rounded-2xl relative overflow-hidden"
        >
          {/* Banner / Background decoration */}
          <div className="absolute top-0 left-0 right-0 h-32 bg-gradient-to-r from-indigo-500/20 to-purple-500/20" />

          <div className="relative mt-8 flex flex-col md:flex-row gap-8 items-start">
            {/* Avatar Section */}
            <div className="flex flex-col items-center gap-4">
              <div className="relative group">
                <div className="h-32 w-32 rounded-full bg-gradient-to-tr from-indigo-500 to-cyan-400 p-1">
                  <div className="h-full w-full rounded-full bg-[#1A1D2D] flex items-center justify-center overflow-hidden">
                    <span className="text-4xl font-bold text-white">D</span>
                  </div>
                </div>
                <button className="absolute bottom-0 right-0 p-2 rounded-full bg-cyan-500 text-white shadow-lg hover:bg-cyan-600 transition-colors">
                  <Camera className="h-4 w-4" />
                </button>
              </div>
              <div className="text-center">
                <h3 className="text-xl font-bold text-white">{formData.fullName}</h3>
                <p className="text-sm text-gray-400">Administrator</p>
              </div>
            </div>

            {/* Form Section */}
            <form onSubmit={handleSubmit} className="flex-1 w-full space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-400 flex items-center gap-2">
                    <User className="h-4 w-4" /> Full Name
                  </label>
                  <input
                    type="text"
                    name="fullName"
                    value={formData.fullName}
                    onChange={handleChange}
                    className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all outline-none"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-400 flex items-center gap-2">
                    <Mail className="h-4 w-4" /> Email
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all outline-none"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-400 flex items-center gap-2">
                    <Phone className="h-4 w-4" /> Phone
                  </label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all outline-none"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-400 flex items-center gap-2">
                    <MapPin className="h-4 w-4" /> Location
                  </label>
                  <input
                    type="text"
                    name="location"
                    value={formData.location}
                    onChange={handleChange}
                    className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all outline-none"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-400">Bio</label>
                <textarea
                  name="bio"
                  value={formData.bio}
                  onChange={handleChange}
                  rows={4}
                  className="w-full px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all outline-none resize-none"
                />
              </div>

              <div className="flex justify-end pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className={cn(
                    "flex items-center gap-2 px-6 py-2.5 rounded-xl bg-indigo-500 text-white font-medium hover:bg-indigo-600 transition-all shadow-lg shadow-indigo-500/20",
                    loading && "opacity-70 cursor-not-allowed"
                  )}
                >
                  <Save className="h-4 w-4" />
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
