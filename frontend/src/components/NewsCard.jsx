import React from 'react';
import { useNavigate } from 'react-router-dom';
import BiasMeter from './BiasMeter';

const NewsCard = ({ article }) => {
  const navigate = useNavigate();
  const isPending = article.processing_status === 'pending';

  const handleClick = () => {
    navigate('/article', { state: { article } });
  };

  return (
    <div
      className="news-card"
      onClick={handleClick}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '10px' }}>
        <span className="news-source">{new URL(article.url).hostname.replace('www.', '').toUpperCase()}</span>
        <span className="news-time">{new Date(article.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
      </div>

      <h3 className="news-headline">{article.headline}</h3>

      {isPending ? (
        <div className="news-summary processing">
          <span className="loading-pulse">Processing AI Summary...</span>
        </div>
      ) : (
        <p className="news-summary">
          {article.tldr_summary || article.summary}
        </p>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
        {!isPending && <BiasMeter bias={article.bias_label} />}

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {article.topic_tags && article.topic_tags.map((tag, index) => (
            <span key={index} className="news-tag">
              {tag}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default NewsCard;
