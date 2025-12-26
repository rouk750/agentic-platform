import { Outlet } from 'react-router-dom';
import AppSidebar from './AppSidebar';

export default function MainLayout() {
  return (
    <div className="flex h-screen w-screen bg-slate-50 text-slate-900 overflow-hidden">
      <AppSidebar />
      <div className="flex-1 h-full overflow-hidden flex flex-col relative">
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
