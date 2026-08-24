import React, { useEffect, useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

export const SustainabilityPage: React.FC = () => {
  const { user } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFootprint = async () => {
      try {
        const res = await fetch(import.meta.env.VITE_API_BASE_URL + '/sustainability/footprint', {
          headers: { 'Authorization': Bearer \ }
        });
        const json = await res.json();
        setData(json);
      } catch (err) {
        console.error("Failed to fetch sustainability data", err);
      } finally {
        setLoading(false);
      }
    };
    
    if (user) {
      fetchFootprint();
    }
  }, [user]);

  if (loading) return <div>Loading sustainability profile...</div>;
  if (!data) return <div>No data available</div>;

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Carbon Footprint Tracker</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle>Total Footprint</CardTitle></CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-green-600">{data.total_co2_kg} kg</div>
            <p className="text-sm text-gray-500 mt-2">CO2 equivalent this month</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader><CardTitle>Green Alternatives</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {data.suggestions?.map((sugg: any, idx: number) => (
              <div key={idx} className="p-4 bg-green-50 rounded-lg border border-green-100">
                <h3 className="font-bold text-green-800">{sugg.title}</h3>
                <p className="text-sm text-green-700 mt-1">{sugg.description}</p>
                <div className="mt-2 text-xs font-semibold text-green-600 uppercase">
                  Save {sugg.potential_co2_savings} kg CO2e
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
