import React, { useState, useEffect, useCallback } from 'react';
import { Database, HardDrive, Dna, FileJson, RefreshCw, AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const POLL_INTERVAL_MS = 15000; // refresh every 15 seconds

const StatusIcon = ({ status }) => {
  if (status === 'critical') return <AlertTriangle size={16} style={{ color: '#ef4444' }} />;
  if (status === 'warning')  return <AlertCircle  size={16} style={{ color: '#f59e0b' }} />;
  return <CheckCircle size={16} style={{ color: '#22c55e' }} />;
};

const statusColor = (status) => {
  if (status === 'critical') return '#ef4444';
  if (status === 'warning')  return '#f59e0b';
  return '#22c55e';
};

const barGradient = (pct) => {
  if (pct >= 90) return 'linear-gradient(90deg, #ef4444, #dc2626)';
  if (pct >= 70) return 'linear-gradient(90deg, #f59e0b, #d97706)';
  return 'linear-gradient(90deg, #C41E4A, #E56B8A)';
};

const MetricTile = ({ icon: Icon, iconColor, label, value, sub }) => (
  <div style={{
    display: 'flex', flexDirection: 'column', gap: '0.4rem',
    background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)',
    borderRadius: '14px', padding: '1.1rem 1.25rem',
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      <Icon size={15} style={{ color: iconColor }} />
      <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-mute)', textTransform: 'uppercase', letterSpacing: '0.12em' }}>
        {label}
      </span>
    </div>
    <div style={{ fontSize: '1.45rem', fontWeight: 900, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>{value}</div>
    {sub && <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>{sub}</div>}
  </div>
);

const HadoopStoragePanel = () => {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);
  const [lastFetch, setLastFetch] = useState(null);

  const fetchStorage = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/hdfs/storage`);
      if (!res.ok) throw new Error(`API returned ${res.status}`);
      const json = await res.json();
      setData(json);
      setError(null);
      setLastFetch(new Date());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStorage();
    const id = setInterval(fetchStorage, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [fetchStorage]);

  const pct = data?.used_percent ?? 0;

  return (
    <div className="metric-card glow-border" style={{ padding: '1.5rem 1.75rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: '40px', height: '40px', borderRadius: '12px',
            background: 'rgba(196,30,74,0.12)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Database size={20} style={{ color: '#C41E4A' }} />
          </div>
          <div>
            <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Hadoop HDFS Storage
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-mute)', fontWeight: 600, letterSpacing: '0.08em' }}>
              /cancer_data &nbsp;·&nbsp; 1 GB Quota
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {data && <StatusIcon status={data.status} />}
          <span style={{
            fontSize: '0.65rem', fontWeight: 700, color: data ? statusColor(data.status) : 'var(--text-mute)',
            textTransform: 'uppercase', letterSpacing: '0.12em',
          }}>
            {loading ? 'loading…' : error ? 'offline' : data?.status}
          </span>
          <button
            onClick={fetchStorage}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-mute)', padding: '0.25rem', borderRadius: '6px',
            }}
            title="Refresh"
          >
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      {/* Storage bar */}
      {data && !error && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600 }}>
              {data.used_mb.toFixed(0)} MB used
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600 }}>
              {data.quota_mb.toFixed(0)} MB quota
            </span>
          </div>
          <div style={{
            height: '10px', borderRadius: '999px',
            background: 'rgba(255,255,255,0.06)', overflow: 'hidden',
          }}>
            <div style={{
              height: '100%',
              width: `${Math.min(pct, 100)}%`,
              background: barGradient(pct),
              borderRadius: '999px',
              transition: 'width 0.8s cubic-bezier(0.4,0,0.2,1)',
              boxShadow: pct >= 70 ? '0 0 10px rgba(196,30,74,0.4)' : 'none',
            }} />
          </div>
          <div style={{
            marginTop: '0.35rem', textAlign: 'right',
            fontSize: '0.7rem', fontWeight: 800,
            color: statusColor(data.status),
          }}>
            {pct.toFixed(1)}% used &nbsp;·&nbsp; {data.available_mb.toFixed(0)} MB free
          </div>
        </div>
      )}

      {error && (
        <div style={{
          padding: '0.75rem 1rem', borderRadius: '10px',
          background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
          fontSize: '0.75rem', color: '#ef4444', fontWeight: 600,
        }}>
          ⚠ HDFS unavailable — {error}
        </div>
      )}

      {/* Metric tiles */}
      {data && !error && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem' }}>
          <MetricTile
            icon={Dna}
            iconColor="#E56B8A"
            label="Gene Data"
            value={`${data.genes_used_mb.toFixed(1)} MB`}
            sub={`${data.gene_batches} batch files uploaded`}
          />
          <MetricTile
            icon={FileJson}
            iconColor="#C41E4A"
            label="Predictions"
            value={`${data.prediction_records}`}
            sub={`${data.predictions_used_mb.toFixed(2)} MB in HDFS`}
          />
          <MetricTile
            icon={HardDrive}
            iconColor="#F099AC"
            label="Available"
            value={`${data.available_mb.toFixed(0)} MB`}
            sub="Remaining quota space"
          />
          <MetricTile
            icon={Database}
            iconColor="#A01745"
            label="Quota"
            value={`${data.quota_mb.toFixed(0)} MB`}
            sub="HDFS space quota enforced"
          />
        </div>
      )}

      {/* DataNode replication note */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0.5rem',
        padding: '0.6rem 0.85rem', borderRadius: '8px',
        background: 'rgba(196,30,74,0.05)', border: '1px solid rgba(196,30,74,0.12)',
      }}>
        <Database size={12} style={{ color: '#C41E4A', flexShrink: 0 }} />
        <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)', fontWeight: 600 }}>
          Data replicated across <strong style={{ color: 'var(--accent)' }}>3 DataNodes</strong> ·
          Replication factor 3 · 128 MB block size
        </span>
      </div>

      {lastFetch && (
        <div style={{ textAlign: 'right', fontSize: '0.62rem', color: 'var(--text-mute)' }}>
          Last refreshed: {lastFetch.toLocaleTimeString()}
        </div>
      )}
    </div>
  );
};

export default HadoopStoragePanel;
