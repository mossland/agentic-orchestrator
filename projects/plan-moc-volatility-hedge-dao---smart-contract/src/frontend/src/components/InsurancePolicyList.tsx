import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';

interface Policy {
  id: string;
  name: string;
  isActive: boolean;
}

interface InsurancePolicyListProps {
  policies: Policy[];
  onActivateDeactivate(policyId: string): void;
}

const InsurancePolicyList: React.FC<InsurancePolicyListProps> = ({ policies, onActivateDeactivate }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate fetching data
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setError(null); // Reset error on re-render with new props
    }, 1000);
  }, [policies]);

  const handleActivateDeactivate = (policyId: string) => {
    try {
      onActivateDeactivate(policyId);
    } catch (err) {
      setError('Failed to update policy status');
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <ul role="list" className="divide-y divide-gray-200">
      {policies.map((policy) => (
        <li key={policy.id} className="py-4 flex items-center justify-between space-x-6">
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-medium text-gray-900 truncate">{policy.name}</h3>
          </div>
          <button
            type="button"
            onClick={() => handleActivateDeactivate(policy.id)}
            aria-label={`Toggle ${policy.isActive ? 'deactivate' : 'activate'} policy`}
            className={`${
              policy.isActive ? 'bg-green-600 text-white hover:bg-green-700' : 'bg-red-600 text-white hover:bg-red-700'
            } py-2 px-4 rounded-md`}
          >
            {policy.isActive ? 'Deactivate' : 'Activate'}
          </button>
        </li>
      ))}
    </ul>
  );
};

export default InsurancePolicyList;