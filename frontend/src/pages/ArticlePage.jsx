import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import BiasMeter from '../components/BiasMeter';
import ReactMarkdown from 'react-markdown'; // We might need to install this, or just render as text for now

const ArticlePage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const article = location.state?.article;

    if (!article) {
        return (
            <div style={{ padding: '40px', textAlign: 'center' }}>
                <p>Article not found. <button onClick={() => navigate('/')}>Go Home</button></p>
            </div>
        );
    }

    // Helper to render markdown-like sections if we don't have a library
    const renderDetailedSummary = (text) => {
        if (!text) return <p>No detailed summary available.</p>;

        // Simple split by double newlines to create paragraphs
        return text.split('\n').map((line, index) => {
            if (line.trim().startsWith('**') && line.trim().endsWith('**')) {
                return <h3 key={index} style={{ marginTop: '20px', marginBottom: '10px' }}>{line.replace(/\*\*/g, '')}</h3>;
            }
            if (line.trim().startsWith('**')) {
                // Handle inline bolding for section headers like "**What Happened**: ..."
                const parts = line.split('**:');
                if (parts.length > 1) {
                    return <p key={index} style={{ marginBottom: '15px', lineHeight: '1.6' }}><strong>{parts[0].replace(/\*\*/g, '')}:</strong>{parts.slice(1).join('**:')}</p>;
                }
            }
            return <p key={index} style={{ marginBottom: '15px', lineHeight: '1.6' }}>{line}</p>;
        });
    };

    return (
        <div style={{ maxWidth: '800px', margin: '0 auto', padding: '40px 20px', fontFamily: 'Inter, sans-serif' }}>
            <button
                onClick={() => navigate('/')}
                style={{
                    background: 'none',
                    border: 'none',
                    color: '#666',
                    cursor: 'pointer',
                    fontSize: '1rem',
                    marginBottom: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px'
                }}
            >
                ← Back to Feed
            </button>

            <header style={{ marginBottom: '30px' }}>
                <div style={{ display: 'flex', gap: '10px', marginBottom: '15px', flexWrap: 'wrap' }}>
                    <BiasMeter label={article.bias_label} />
                    <span style={{ color: '#888' }}>{new Date(article.created_at).toLocaleDateString()}</span>
                    {article.category && (
                        <span style={{
                            backgroundColor: '#e3f2fd',
                            color: '#1976d2',
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontSize: '0.9rem'
                        }}>
                            {article.category}
                        </span>
                    )}
                </div>

                <h1 style={{ fontSize: '2.5rem', fontWeight: '800', lineHeight: '1.2', marginBottom: '20px' }}>
                    {article.headline}
                </h1>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {article.topic_tags && article.topic_tags.map(tag => (
                        <span key={tag} style={{
                            backgroundColor: '#f5f5f5',
                            padding: '6px 12px',
                            borderRadius: '20px',
                            fontSize: '0.85rem',
                            color: '#555',
                            fontWeight: '500'
                        }}>
                            #{tag}
                        </span>
                    ))}
                </div>
            </header>

            <div style={{ backgroundColor: '#fafafa', padding: '25px', borderRadius: '12px', marginBottom: '40px', borderLeft: '4px solid #007bff' }}>
                <h3 style={{ marginTop: 0, fontSize: '1.1rem', color: '#333', textTransform: 'uppercase', letterSpacing: '0.05em' }}>TL;DR</h3>
                <p style={{ fontSize: '1.1rem', lineHeight: '1.6', margin: 0 }}>
                    {article.tldr_summary || article.summary}
                </p>
            </div>

            <div style={{ fontSize: '1.1rem', color: '#333' }}>
                {renderDetailedSummary(article.detailed_summary)}
            </div>

            <div style={{ marginTop: '50px', borderTop: '1px solid #eee', paddingTop: '30px', textAlign: 'center' }}>
                <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                        display: 'inline-block',
                        backgroundColor: '#000',
                        color: 'white',
                        padding: '16px 32px',
                        borderRadius: '30px',
                        textDecoration: 'none',
                        fontWeight: '600',
                        fontSize: '1.1rem',
                        transition: 'transform 0.2s'
                    }}
                >
                    Read Original Article
                </a>
            </div>
        </div>
    );
};

export default ArticlePage;
