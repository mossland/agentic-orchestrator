import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Transaction {
  id: number;
  date: string;
  assetType: string;
  amount: number;
}

interface Props {
  portfolioId: number;
}

const TransactionHistoryComponent: React.FC<Props> = ({ portfolioId }) => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<'date' | 'assetType'>('date');
  const [filterValue, setFilterValue] = useState<string>('');

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        const response = await axios.get(`/api/portfolio/${portfolioId}/transactions`);
        setTransactions(response.data);
      } catch (err) {
        setError('Failed to load transactions');
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
  }, [portfolioId]);

  const filteredTransactions = transactions.filter((transaction) => {
    if (filterType === 'date') return transaction.date.includes(filterValue);
    else return transaction.assetType.toLowerCase().includes(filterValue.toLowerCase());
  });

  return (
    <div className="p-4 max-w-screen-lg mx-auto">
      {loading && <p>Loading...</p>}
      {error && <p>{error}</p>}
      {!loading && !error && (
        <>
          <div className="flex justify-between items-center mb-2">
            <label htmlFor="filterType" className="mr-2">Filter by:</label>
            <select
              id="filterType"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as 'date' | 'assetType')}
              aria-label="Select filter type"
              className="border p-1 rounded mr-4"
            >
              <option value="date">Date</option>
              <option value="assetType">Asset Type</option>
            </select>
            <input
              type="text"
              placeholder={filterType === 'date' ? 'Enter date...' : 'Enter asset type...'}
              className="border p-1 rounded"
              aria-label={`Filter by ${filterType}`}
              onChange={(e) => setFilterValue(e.target.value)}
            />
          </div>
          <table className="w-full text-left">
            <thead>
              <tr>
                <th>Date</th>
                <th>Asset Type</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              {filteredTransactions.map((transaction) => (
                <tr key={transaction.id} className="border-b">
                  <td>{transaction.date}</td>
                  <td>{transaction.assetType}</td>
                  <td>{transaction.amount}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
};

export default TransactionHistoryComponent;