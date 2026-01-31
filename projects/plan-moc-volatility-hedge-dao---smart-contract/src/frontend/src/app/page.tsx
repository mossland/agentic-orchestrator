import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { InsurancePolicyList, TradeHistory } from './components';

const Dashboard = () => {
  const [insurancePolicies, setInsurancePolicies] = useState([]);
  const [tradeHistory, setTradeHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInsuranceData();
    fetchTradeData();
  }, []);

  const fetchInsuranceData = async () => {
    try {
      const response = await axios.get('https://api.etherscan.io/insurance');
      setInsurancePolicies(response.data);
    } catch (error) {
      console.error("Error fetching insurance data:", error);
    }
    setLoading(false);
  };

  const fetchTradeData = async () => {
    try {
      const response = await axios.get('https://api.etherscan.io/trades');
      setTradeHistory(response.data);
    } catch (error) {
      console.error("Error fetching trade history data:", error);
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col min-h-screen bg-gray-100 dark:bg-gray-900">
      <header className="bg-white shadow dark:bg-gray-800 p-4 text-center">
        <h1 className="text-xl font-bold">MOC V-MOP Dashboard</h1>
      </header>
      <main className="flex-grow flex p-4">
        <aside className="w-64 bg-white shadow-md mr-4 dark:bg-gray-800 hidden md:block">
          {/* Sidebar content */}
        </aside>
        <div className="flex-grow">
          {loading ? (
            <p>Loading...</p>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <InsurancePolicyList insurancePolicies={insurancePolicies} />
                <TradeHistory tradeHistory={tradeHistory} />
              </div>
              {/* Data visualization placeholders */}
              <div className="mb-4">
                <h3 className="text-lg font-semibold">Market Overview</h3>
                <div className="p-4 bg-white shadow dark:bg-gray-800 rounded-lg h-64">Chart Placeholder</div>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;