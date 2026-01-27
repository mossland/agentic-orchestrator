import { useState, useEffect } from 'react';
import axios from 'axios';

interface Portfolio {
  id: string;
  name: string;
  assets: Asset[];
}

interface Asset {
  symbol: string;
  value: number;
}

interface Props {
  userId: string;
}

const PortfolioOverviewPage: React.FC<Props> = ({ userId }) => {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPortfolios = async () => {
      try {
        const response = await axios.get(`/api/portfolios/${userId}`);
        setPortfolios(response.data);
      } catch (err) {
        setError('Failed to load portfolios');
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolios();
  }, [userId]);

  const handleRebalance = async (portfolioId: string) => {
    try {
      await axios.post(`/api/rebalance/${portfolioId}`);
      alert(`Portfolio ${portfolioId} rebalanced successfully`);
    } catch (err) {
      setError('Failed to initiate rebalancing');
    }
  };

  if (loading) return <div className="text-center">Loading...</div>;
  if (error) return <div className="text-center text-red-500">{error}</div>;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      {portfolios.map((portfolio) => (
        <div
          key={portfolio.id}
          className="w-full max-w-md bg-white rounded-lg shadow-md overflow-hidden mb-4"
        >
          <div className="p-6">
            <h2 className="text-xl font-bold text-gray-900">{portfolio.name}</h2>
            <ul role="list" className="mt-3 space-y-1 text-sm leading-6 text-gray-600">
              {portfolio.assets.map((asset) => (
                <li key={asset.symbol} className="flex items-center justify-between gap-x-4">
                  <span>{asset.symbol}</span>
                  <span>{asset.value.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="p-6 bg-gray-50 space-x-2 flex justify-end">
            <button
              onClick={() => handleRebalance(portfolio.id)}
              type="button"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Rebalance
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default PortfolioOverviewPage;