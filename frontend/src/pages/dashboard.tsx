import { useEffect, useState } from 'react';

type Project = { id: string; name: string; description?: string };

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);

  useEffect(() => {
    // Placeholder: would fetch from backend with auth token
    setProjects([{ id: 'demo', name: 'Demo Project', description: 'Example' }]);
  }, []);

  return (
    <main className="min-h-screen p-8">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        {projects.map((p) => (
          <div key={p.id} className="border rounded p-4">
            <div className="font-medium">{p.name}</div>
            <div className="text-sm text-gray-500">{p.description}</div>
          </div>
        ))}
      </div>
    </main>
  );
}

