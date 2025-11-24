import React from 'react';
import BiasMeter from './BiasMeter';

const NewsCard = ({ article, onClick }) => {
  const isPending = article.processing_status === "pending";

  return (
    <div
      onClick={() => onClick(article)}
      style={{
        border: '1px solid #eee',
        borderRadius: '12px',
        padding: '20px',
        marginBottom: '20px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
        cursor: 'pointer',
        transition: 'transform 0.2s, box-shadow 0.2s',
        backgroundColor: '#fff'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = '0 6px 16px rgba(0,0,0,0.1)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.05)';
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '10px' }}>
        <span className="news-source" style={{ fontSize: '0.8rem', color: '#666', fontWeight: 'bold', textTransform: 'uppercase' }}>
          {new URL(article.url).hostname.replace('www.', '')}
        </span>
        <span style={{ fontSize: '0.8rem', color: '#999' }}>
          {new Date(article.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>

      <h3 style={{ marginTop: 0, marginBottom: '10px', fontSize: '1.2rem', lineHeight: '1.4', color: '#1a1a1a' }}>
        {article.headline}
      </h3>

      {isPending ? (
        <div className="news-summary" style={{ color: '#aaa', fontStyle: 'italic', marginBottom: '15px' }}>
          <span className="loading-pulse">Processing AI Summary...</span>
        </div>
      ) : (
        <p style={{ fontSize: '0.95rem', color: '#4a4a4a', lineHeight: '1.6', marginBottom: '15px' }}>
          {article.tldr_summary || article.summary}
        </p>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
        {!isPending && <BiasMeter bias={article.bias_label} />}

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {article.topic_tags && article.topic_tags.map((tag, index) => (
            <span key={index} style={{
              backgroundColor: '#f5f5f5',
              padding: '4px 8px',
              borderRadius: '6px',
              fontSize: '0.75rem',
              color: '#666',
              fontWeight: '500'
            }}>
              {tag}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default NewsCard;
