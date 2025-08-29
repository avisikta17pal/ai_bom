import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';

type ComponentItem = { name: string; type: string; fingerprint?: { hash: string } };

export default function BomDetail() {
  const router = useRouter();
  const { bomId } = router.query as { bomId: string };
  const [components, setComponents] = useState<ComponentItem[]>([]);

  useEffect(() => {
    if (!bomId) return;
    // Placeholder: fetch from API
    setComponents([
      { name: 'model.pt', type: 'model', fingerprint: { hash: 'abc123' } },
      { name: 'data.csv', type: 'dataset', fingerprint: { hash: 'def456' } }
    ]);
  }, [bomId]);

  return (
    <main className="min-h-screen p-8">
      <h1 className="text-2xl font-semibold">BOM {bomId}</h1>
      <ul className="mt-4 space-y-2">
        {components.map((c, i) => (
          <li key={i} className="border rounded p-3 flex justify-between">
            <span>{c.type}: {c.name}</span>
            <span className="text-xs text-gray-500">{c.fingerprint?.hash?.slice(0, 12)}</span>
          </li>
        ))}
      </ul>
    </main>
  );
}

