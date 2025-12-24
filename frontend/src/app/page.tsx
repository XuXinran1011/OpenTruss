import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-white">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-zinc-900 mb-4">OpenTruss</h1>
        <p className="text-lg text-zinc-600 mb-8">面向建筑施工行业的生成式 BIM 中间件</p>
        <Link
          href="/workbench"
          className="inline-block px-6 py-3 text-white bg-zinc-900 hover:bg-zinc-800 rounded transition-colors"
        >
          进入工作台
        </Link>
      </div>
    </main>
  );
}
