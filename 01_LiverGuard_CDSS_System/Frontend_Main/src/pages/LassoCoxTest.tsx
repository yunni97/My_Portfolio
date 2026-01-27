import React, { useState } from 'react';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { lassoCoxMultimodal } from '../services/ai_api';

// Chart.js 등록
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface FeatureImportance {
  feature: string;
  coefficient: number;
  hazard_ratio: number;
  impact: 'increase' | 'decrease';
}

interface LassoCoxResult {
  status: string;
  hazard_ratio: number;
  survival_curve: {
    time: number[];
    survival: number[];
  };
  cumulative_hazard_curve: {
    time: number[];
    cumhaz: number[];
  };
  img_feature_dim: number;
  table_feature_dim: number;
  merged_dim: number;
  feature_importance?: FeatureImportance[];
  feature_names?: {
    tabular: string[];
    image: string[];
    all: string[];
  };
}

const LassoCoxTest: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LassoCoxResult | null>(null);
  const [inputFeatures, setInputFeatures] = useState<number[]>([]);

  // 컴포넌트가 마운트될 때 자동으로 예측 실행
  React.useEffect(() => {
    handlePredict();
  }, []);

  const handlePredict = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await lassoCoxMultimodal();
      setResult(response.prediction);
      setInputFeatures(response.input_features);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Survival Curve 차트 데이터
  const survivalChartData = result ? {
    labels: result.survival_curve.time,
    datasets: [
      {
        label: 'Survival Probability',
        data: result.survival_curve.survival,
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  } : null;

  // Cumulative Hazard Curve 차트 데이터
  const hazardChartData = result ? {
    labels: result.cumulative_hazard_curve.time,
    datasets: [
      {
        label: 'Cumulative Hazard',
        data: result.cumulative_hazard_curve.cumhaz,
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.1)',
        fill: true,
        tension: 0.4,
      },
    ],
  } : null;

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Time',
        },
      },
      y: {
        title: {
          display: true,
          text: 'Probability / Hazard',
        },
      },
    },
  };

  // Feature Importance Bar Chart (Top 20)
  const featureImportanceData = result?.feature_importance ? {
    labels: result.feature_importance.slice(0, 20).map(f => f.feature),
    datasets: [
      {
        label: 'Hazard Ratio',
        data: result.feature_importance.slice(0, 20).map(f => f.hazard_ratio),
        backgroundColor: result.feature_importance.slice(0, 20).map(f =>
          f.impact === 'increase' ? 'rgba(255, 99, 132, 0.6)' : 'rgba(75, 192, 192, 0.6)'
        ),
        borderColor: result.feature_importance.slice(0, 20).map(f =>
          f.impact === 'increase' ? 'rgb(255, 99, 132)' : 'rgb(75, 192, 192)'
        ),
        borderWidth: 1,
      },
    ],
  } : null;

  const barChartOptions = {
    indexAxis: 'y' as const,
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const idx = context.dataIndex;
            const feature = result?.feature_importance?.[idx];
            return [
              `Hazard Ratio: ${context.parsed.x.toFixed(4)}`,
              `Coefficient: ${feature?.coefficient.toFixed(4)}`,
              `Impact: ${feature?.impact === 'increase' ? 'Increases risk' : 'Decreases risk'}`
            ];
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Hazard Ratio',
        },
        grid: {
          drawOnChartArea: true,
        }
      },
      y: {
        ticks: {
          font: {
            size: 10
          }
        }
      }
    },
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      <h1>Lasso Cox Multimodal Analysis Test</h1>

      <div style={{ marginBottom: '20px' }}>
        <button
          onClick={handlePredict}
          disabled={loading}
          style={{
            padding: '12px 24px',
            fontSize: '16px',
            backgroundColor: loading ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? 'Loading...' : 'Run Prediction'}
        </button>
      </div>

      {error && (
        <div style={{
          padding: '12px',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          borderRadius: '4px',
          marginBottom: '20px',
        }}>
          Error: {error}
        </div>
      )}

      {result && (
        <div>
          {/* Summary Section */}
          <div style={{
            padding: '20px',
            backgroundColor: '#f8f9fa',
            borderRadius: '8px',
            marginBottom: '20px',
          }}>
            <h2>Analysis Summary</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
              <div>
                <strong>Status:</strong> {result.status}
              </div>
              <div>
                <strong>Hazard Ratio:</strong> {result.hazard_ratio.toFixed(4)}
              </div>
              <div>
                <strong>Image Feature Dim:</strong> {result.img_feature_dim}
              </div>
              <div>
                <strong>Table Feature Dim:</strong> {result.table_feature_dim}
              </div>
              <div>
                <strong>Merged Dim:</strong> {result.merged_dim}
              </div>
            </div>
          </div>

          {/* Input Features */}
          <div style={{
            padding: '20px',
            backgroundColor: '#fff',
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            marginBottom: '20px',
          }}>
            <h3>Input Tabular Features</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {inputFeatures.map((feature, idx) => (
                <span
                  key={idx}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: '#e7f3ff',
                    borderRadius: '4px',
                    fontSize: '14px',
                  }}
                >
                  Feature {idx + 1}: {feature}
                </span>
              ))}
            </div>
          </div>

          {/* Feature Importance Chart */}
          {result.feature_importance && result.feature_importance.length > 0 && (
            <div style={{
              padding: '20px',
              backgroundColor: '#fff',
              border: '1px solid #dee2e6',
              borderRadius: '8px',
              marginBottom: '30px',
            }}>
              <h3>Top 20 Feature Importance (by Hazard Ratio)</h3>
              <div style={{
                display: 'flex',
                gap: '10px',
                marginBottom: '10px',
                fontSize: '14px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <div style={{
                    width: '20px',
                    height: '20px',
                    backgroundColor: 'rgba(255, 99, 132, 0.6)',
                    border: '1px solid rgb(255, 99, 132)'
                  }}></div>
                  <span>Increases Risk (HR &gt; 1)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <div style={{
                    width: '20px',
                    height: '20px',
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    border: '1px solid rgb(75, 192, 192)'
                  }}></div>
                  <span>Decreases Risk (HR &lt; 1)</span>
                </div>
              </div>
              <div style={{ height: '600px' }}>
                {featureImportanceData && (
                  <Bar data={featureImportanceData} options={barChartOptions} />
                )}
              </div>
            </div>
          )}

          {/* Charts */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '30px' }}>
            {/* Survival Curve */}
            <div style={{
              padding: '20px',
              backgroundColor: '#fff',
              border: '1px solid #dee2e6',
              borderRadius: '8px',
            }}>
              <h3>Survival Curve</h3>
              <div style={{ height: '400px' }}>
                {survivalChartData && (
                  <Line data={survivalChartData} options={chartOptions} />
                )}
              </div>
            </div>

            {/* Cumulative Hazard Curve */}
            <div style={{
              padding: '20px',
              backgroundColor: '#fff',
              border: '1px solid #dee2e6',
              borderRadius: '8px',
            }}>
              <h3>Cumulative Hazard Curve</h3>
              <div style={{ height: '400px' }}>
                {hazardChartData && (
                  <Line data={hazardChartData} options={chartOptions} />
                )}
              </div>
            </div>
          </div>

          {/* Data Tables */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '30px' }}>
            {/* Survival Data Table */}
            <div style={{
              padding: '20px',
              backgroundColor: '#fff',
              border: '1px solid #dee2e6',
              borderRadius: '8px',
            }}>
              <h3>Survival Data (First 10 points)</h3>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f9fa' }}>
                    <th style={{ padding: '8px', border: '1px solid #dee2e6' }}>Time</th>
                    <th style={{ padding: '8px', border: '1px solid #dee2e6' }}>Survival</th>
                  </tr>
                </thead>
                <tbody>
                  {result.survival_curve.time.slice(0, 10).map((time, idx) => (
                    <tr key={idx}>
                      <td style={{ padding: '8px', border: '1px solid #dee2e6' }}>{time.toFixed(2)}</td>
                      <td style={{ padding: '8px', border: '1px solid #dee2e6' }}>
                        {result.survival_curve.survival[idx].toFixed(4)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Hazard Data Table */}
            <div style={{
              padding: '20px',
              backgroundColor: '#fff',
              border: '1px solid #dee2e6',
              borderRadius: '8px',
            }}>
              <h3>Cumulative Hazard Data (First 10 points)</h3>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f9fa' }}>
                    <th style={{ padding: '8px', border: '1px solid #dee2e6' }}>Time</th>
                    <th style={{ padding: '8px', border: '1px solid #dee2e6' }}>Cum. Hazard</th>
                  </tr>
                </thead>
                <tbody>
                  {result.cumulative_hazard_curve.time.slice(0, 10).map((time, idx) => (
                    <tr key={idx}>
                      <td style={{ padding: '8px', border: '1px solid #dee2e6' }}>{time.toFixed(2)}</td>
                      <td style={{ padding: '8px', border: '1px solid #dee2e6' }}>
                        {result.cumulative_hazard_curve.cumhaz[idx].toFixed(4)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LassoCoxTest;