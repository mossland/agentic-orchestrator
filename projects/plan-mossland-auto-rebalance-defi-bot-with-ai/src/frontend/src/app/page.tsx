import { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';

// Tailwind CSS for styling
const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Simulate fetching data
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  }, []);

  return (
    <>
      <Head>
        <title>Mossland Auto-Rebalance DeFi Bot</title>
        <meta name="description" content="AI-Powered DeFi Portfolio Auto-Rebalancing System Integrated with Mossland Ecosystem" />
      </Head>

      {/* Header */}
      <header className="bg-gray-900 text-white p-4 flex justify-between items-center">
        <div>
          <h1>Mossland Auto-Rebalance DeFi Bot</h1>
        </div>
        <nav>
          <ul className="flex space-x-4">
            <li><Link href="/"><a>Home</a></Link></li>
            <li><Link href="/portfolio"><a>Portfolio</a></Link></li>
            <li><Link href="/settings"><a>Settings</a></Link></li>
          </ul>
        </nav>
      </header>

      {/* Sidebar */}
      <aside className="hidden md:block bg-gray-800 text-white p-4 h-screen">
        <div className="space-y-2">
          <h2 className="text-lg font-semibold">Navigation</h2>
          <Link href="/"><a className="block py-2 px-3 rounded hover:bg-gray-700">Home</a></Link>
          <Link href="/portfolio"><a className="block py-2 px-3 rounded hover:bg-gray-700">Portfolio Overview</a></Link>
          <Link href="/settings"><a className="block py-2 px-3 rounded hover:bg-gray-700">Settings</a></Link>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="p-4 md:ml-60">
        {loading ? (
          <div>Loading...</div>
        ) : (
          <>
            <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
              {/* Card 1 */}
              <div className="bg-white rounded-lg shadow-md p-6 text-gray-700 dark:bg-gray-800 dark:text-white">
                <h3 className="text-xl font-semibold">Portfolio Value</h3>
                <p>$25,000.00</p>
              </div>

              {/* Card 2 */}
              <div className="bg-white rounded-lg shadow-md p-6 text-gray-700 dark:bg-gray-800 dark:text-white">
                <h3 className="text-xl font-semibold">Total Transactions</h3>
                <p>150</p>
              </div>

              {/* Card 3 */}
              <div className="bg-white rounded-lg shadow-md p-6 text-gray-700 dark:bg-gray-800 dark:text-white">
                <h3 className="text-xl font-semibold">Risk Level</h3>
                <p>Low</p>
              </div>

            </section>

            {/* Data Visualization Placeholder */}
            <section className="bg-white rounded-lg shadow-md p-6 text-gray-700 dark:bg-gray-800 dark:text-white">
              <h2 className="text-xl font-semibold">Portfolio Performance</h2>
              <p>Placeholder for chart or graph</p>
            </section>

          </>
        )}
      </main>
    </>
  );
};

export default Dashboard;