import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen p-8">
      <h1 className="text-3xl font-bold">ai-bom</h1>
      <p className="text-gray-600 mt-2">Auditable AI Bill of Materials & model lineage</p>
      <div className="mt-6 flex gap-4">
        <Link className="px-4 py-2 bg-blue-600 text-white rounded" href="/dashboard">Dashboard</Link>
        <Link className="px-4 py-2 border rounded" href="/docs">Docs</Link>
      </div>
    </main>
  );
}

