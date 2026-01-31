import React, { useState } from 'react';
import { TradeHistoryProps } from './TradeHistory.types';

const TradeHistory: React.FC<TradeHistoryProps> = ({ trades }) => {
  const [filteredTrades, setFilteredTrades] = useState(trades);
  const [sortKey, setSortKey] = useState<'quantity' | 'price'>('quantity');
  const [isAscending, setIsAscending] = useState(true);

  const handleDateFilterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const dateValue = new Date(e.target.value).getTime();
    const filteredTrades = trades.filter(trade => trade.timestamp === dateValue);
    setFilteredTrades(filteredTrades);
  };

  const handleSortClick = (key: 'quantity' | 'price') => () => {
    if (sortKey !== key) {
      setIsAscending(true);
    }
    setSortKey(key);
    setIsAscending(!isAscending);
  };

  const sortedTrades = [...filteredTrades].sort((a, b) => {
    if (sortKey === 'quantity') {
      return isAscending ? a.quantity - b.quantity : b.quantity - a.quantity;
    } else {
      return isAscending ? a.price - b.price : b.price - a.price;
    }
  });

  const loading = !trades.length && <div>Loading...</div>;
  const error = trades === null && <div>Error fetching trade history.</div>;

  return (
    <div className="p-4 max-w-screen-lg mx-auto">
      {loading || error}
      <input
        type="date"
        onChange={handleDateFilterChange}
        aria-label="Trade date filter"
        className="mb-2 block w-full p-2 border rounded focus:outline-none focus:border-blue-500"
      />
      <table className="w-full text-left">
        <thead>
          <tr>
            <th
              onClick={handleSortClick('quantity')}
              className="cursor-pointer px-4 py-2"
            >
              Quantity {sortKey === 'quantity' && (isAscending ? '↑' : '↓')}
            </th>
            <th
              onClick={handleSortClick('price')}
              className="cursor-pointer px-4 py-2"
            >
              Price {sortKey === 'price' && (isAscending ? '↑' : '↓')}
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedTrades.map(trade => (
            <tr key={trade.id} className="border-b">
              <td className="px-4 py-2">{trade.quantity}</td>
              <td className="px-4 py-2">${trade.price.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TradeHistory;

// Interfaces
interface Trade {
  id: string;
  quantity: number;
  price: number;
  timestamp: number;
}

interface TradeHistoryProps {
  trades?: Trade[] | null;
}